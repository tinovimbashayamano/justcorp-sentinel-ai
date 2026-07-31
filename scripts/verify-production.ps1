$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env.production"
$ComposeFile = Join-Path $RepoRoot "docker-compose.prod.yml"
$ComposePrefix = @(
    "compose",
    "--env-file", $EnvFile,
    "-f", $ComposeFile
)

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "FAILED: $Message"
    }

    Write-Host "PASS: $Message" -ForegroundColor Green
}

function Invoke-Compose {
    param([string[]]$Command)

    & docker @ComposePrefix @Command

    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose command failed: $($Command -join ' ')"
    }
}

function Get-ServiceContainerId {
    param([string]$Service)

    $id = (
        & docker @ComposePrefix ps -q $Service |
        Out-String
    ).Trim()

    Assert-True ($id.Length -gt 0) "$Service container exists"
    return $id
}

function Wait-ServiceHealthy {
    param(
        [string]$Service,
        [int]$TimeoutSeconds = 120
    )

    $containerId = Get-ServiceContainerId $Service
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    do {
        $status = (
            docker inspect `
                --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" `
                $containerId |
            Out-String
        ).Trim()

        if ($status -eq "healthy" -or $status -eq "running") {
            Write-Host "PASS: $Service is $status" -ForegroundColor Green
            return
        }

        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)

    throw "FAILED: $Service did not become healthy. Last status: $status"
}

function Get-HttpStatus {
    param([string]$Uri)

    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -eq $curl) {
        throw "FAILED: curl.exe is required for production HTTP checks"
    }

    $statusText = (
        & $curl.Source `
            --silent `
            --show-error `
            --output NUL `
            --write-out "%{http_code}" `
            --ipv4 `
            --connect-timeout 5 `
            --max-time 30 `
            --retry 3 `
            --retry-delay 2 `
            --retry-connrefused `
            $Uri |
        Out-String
    ).Trim()

    if ($LASTEXITCODE -ne 0) {
        throw "FAILED: HTTP check could not reach $Uri"
    }

    [int]$statusCode = 0
    if (-not [int]::TryParse($statusText, [ref]$statusCode)) {
        throw "FAILED: Invalid HTTP status '$statusText' returned for $Uri"
    }

    return $statusCode
}

Set-Location $RepoRoot

Write-Host "`n1. Prerequisites" -ForegroundColor Cyan

Assert-True (Test-Path $EnvFile) ".env.production exists"
Assert-True ($null -ne (Get-Command docker -ErrorAction SilentlyContinue)) `
    "Docker is installed"

$environmentText = Get-Content $EnvFile -Raw
Assert-True (
    $environmentText -notmatch "REPLACE_WITH_|CHANGE_ME|CHANGEME"
) "Production secrets do not contain placeholders"

docker info | Out-Null
Assert-True ($LASTEXITCODE -eq 0) "Docker Desktop is running"

Write-Host "`n2. Compose validation" -ForegroundColor Cyan

Invoke-Compose -Command @("config", "--quiet")
Write-Host "PASS: Docker Compose configuration is valid" -ForegroundColor Green

Write-Host "`n3. Production image builds" -ForegroundColor Cyan

Invoke-Compose -Command @("build", "--pull", "backend", "frontend")
Write-Host "PASS: Backend production image builds" -ForegroundColor Green
Write-Host "PASS: Frontend production image builds" -ForegroundColor Green

Write-Host "`n4. Start production stack" -ForegroundColor Cyan

Invoke-Compose -Command @("up", "-d")
Invoke-Compose -Command @("ps")

foreach ($service in @("postgres", "redis", "backend", "frontend")) {
    Wait-ServiceHealthy $service
}

Write-Host "`n5. Non-root containers" -ForegroundColor Cyan

foreach ($service in @("frontend", "backend", "postgres", "redis")) {
    $containerId = Get-ServiceContainerId $service
    $uid = (
        docker exec $containerId stat -c "%u" /proc/1 |
        Out-String
    ).Trim()

    Assert-True (
        $LASTEXITCODE -eq 0 -and $uid -ne "0"
    ) "$service PID 1 runs as a non-root process (UID $uid)"
}

Write-Host "`n6. Frontend and routing" -ForegroundColor Cyan

$frontendBaseUrl = "http://127.0.0.1:8080"
$frontendStatus = Get-HttpStatus "$frontendBaseUrl/"
Assert-True ($frontendStatus -eq 200) "Frontend loads"

foreach ($route in @(
    "/audit-trail",
    "/reports/export",
    "/model-governance",
    "/operations",
    "/admin",
    "/fraud/explainability",
    "/fraud/investigations"
)) {
    $status = Get-HttpStatus "$frontendBaseUrl$route"
    Assert-True ($status -eq 200) "SPA route refresh works: $route"
}

Write-Host "`n7. API proxy and backend health" -ForegroundColor Cyan

$apiStatus = Get-HttpStatus "$frontendBaseUrl/api/v1/fraud/health"

Assert-True (
    $apiStatus -notin @(404, 502, 503)
) "/api proxy reaches FastAPI (status $apiStatus)"

Invoke-Compose -Command @(
    "exec",
    "-T",
    "backend",
    "python",
    "-c",
    "import urllib.request; response=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5); assert response.status == 200"
)

Write-Host "PASS: Backend health endpoint returns 200" -ForegroundColor Green

Write-Host "`n8. Database persistence" -ForegroundColor Cyan

$createProbe = @'
CREATE TABLE IF NOT EXISTS deployment_persistence_probe (
    marker text PRIMARY KEY
);
TRUNCATE deployment_persistence_probe;
INSERT INTO deployment_persistence_probe VALUES ('step64');
'@

$createProbe |
    & docker @ComposePrefix exec -T postgres sh -lc `
        'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

if ($LASTEXITCODE -ne 0) {
    throw "FAILED: Could not create the database persistence probe"
}

Invoke-Compose -Command @("restart", "postgres")
Wait-ServiceHealthy postgres

$databaseMarker = (
    'SELECT marker FROM deployment_persistence_probe LIMIT 1;' |
    & docker @ComposePrefix exec -T postgres sh -lc `
        'exec psql -v ON_ERROR_STOP=1 -tA -U "$POSTGRES_USER" -d "$POSTGRES_DB"' |
    Out-String
).Trim()

Assert-True ($LASTEXITCODE -eq 0) `
    "Database persistence probe remains queryable after restart"
Assert-True ($databaseMarker -eq "step64") `
    "Database data survives PostgreSQL restart"

'DROP TABLE deployment_persistence_probe;' |
    & docker @ComposePrefix exec -T postgres sh -lc `
        'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

if ($LASTEXITCODE -ne 0) {
    throw "FAILED: Could not remove the database persistence probe"
}

Write-Host "`n9. Reports and model persistence" -ForegroundColor Cyan

Invoke-Compose -Command @(
    "exec",
    "-T",
    "backend",
    "sh",
    "-lc",
    'printf "step64" > /app/storage/reports/.step64-persistence-probe'
)

$modelHashBefore = (
    & docker @ComposePrefix exec -T backend `
        sha256sum /app/ml/model_artifacts/lightgbm_fraud_model.joblib |
    Out-String
).Trim()

Invoke-Compose -Command @("restart", "backend")
Wait-ServiceHealthy backend

Invoke-Compose -Command @(
    "exec",
    "-T",
    "backend",
    "sh",
    "-lc",
    'test "$(cat /app/storage/reports/.step64-persistence-probe)" = "step64"'
)

Write-Host "PASS: Reports survive backend restart" -ForegroundColor Green

$modelHashAfter = (
    & docker @ComposePrefix exec -T backend `
        sha256sum /app/ml/model_artifacts/lightgbm_fraud_model.joblib |
    Out-String
).Trim()

Assert-True ($modelHashBefore -eq $modelHashAfter) `
    "Model artifact survives restart without changing"

Invoke-Compose -Command @(
    "exec",
    "-T",
    "backend",
    "rm",
    "/app/storage/reports/.step64-persistence-probe"
)

Write-Host "`n10. Secret image scan" -ForegroundColor Cyan

$environment = @{}

Get-Content $EnvFile |
    Where-Object {
        $_ -and
        -not $_.StartsWith("#") -and
        $_.Contains("=")
    } |
    ForEach-Object {
        $parts = $_.Split("=", 2)
        $environment[$parts[0].Trim()] = $parts[1].Trim()
    }

$secretValues = @(
    $environment["POSTGRES_PASSWORD"],
    $environment["REDIS_PASSWORD"],
    $environment["JWT_SECRET_KEY"]
) | Where-Object { $_ -and $_.Length -ge 12 }

foreach ($service in @("backend", "frontend")) {
    $imageId = (
        & docker @ComposePrefix images -q $service |
        Out-String
    ).Trim()

    Assert-True ($imageId.Length -gt 0) "$service image exists"

    $inspectMetadata = (
        docker image inspect $imageId |
        Out-String
    )
    $historyMetadata = (
        docker history --no-trunc $imageId |
        Out-String
    )
    $metadata = $inspectMetadata + $historyMetadata

    foreach ($secret in $secretValues) {
        Assert-True (
            -not $metadata.Contains($secret)
        ) "$service image metadata does not contain production secret values"
    }

    docker run --rm --entrypoint sh $imageId -lc `
        'test ! -e /app/.env.production && test ! -e /.env.production'

    Assert-True ($LASTEXITCODE -eq 0) `
        "$service image does not contain .env.production"
}

Write-Host "`n11. Restart policy" -ForegroundColor Cyan

$backendId = Get-ServiceContainerId "backend"
$restartCountBefore = [int](
    docker inspect --format "{{.RestartCount}}" $backendId
)

docker kill $backendId | Out-Null
Wait-ServiceHealthy backend

$restartCountAfter = [int](
    docker inspect --format "{{.RestartCount}}" $backendId
)

Assert-True ($restartCountAfter -gt $restartCountBefore) `
    "Backend restarts automatically after failure"

Write-Host "`n12. Automated production tests" -ForegroundColor Cyan

& .\.venv\Scripts\python.exe -m pytest

Assert-True ($LASTEXITCODE -eq 0) `
    "Backend production tests pass"

Push-Location frontend

try {
    npm run test
    Assert-True ($LASTEXITCODE -eq 0) `
        "Frontend tests pass"

    $buildOutput = (
        npm run build 2>&1 |
        Tee-Object -Variable buildLines |
        Out-String
    )

    Assert-True ($LASTEXITCODE -eq 0) `
        "Frontend production build passes"

    Assert-True (
        $buildOutput -notmatch "Some chunks are larger than 500 kB"
    ) "Frontend oversized-bundle warning is absent after code splitting"
}
finally {
    Pop-Location
}

Write-Host "`nAll production verification checks passed." `
    -ForegroundColor Green
Write-Host "The production stack remains running at http://localhost:8080."
