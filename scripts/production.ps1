param(
    [ValidateSet("validate", "build", "up", "down", "logs", "ps", "restart")]
    [string]$Action = "validate"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "docker-compose.prod.yml"
$EnvironmentFile = Join-Path $RepoRoot ".env.production"
$SecretRequiredActions = @("validate", "build", "up", "restart")

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    & docker compose `
        --env-file $EnvironmentFile `
        -f $ComposeFile `
        @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed with exit code $LASTEXITCODE."
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not available in PATH."
}

if (-not (Test-Path -LiteralPath $EnvironmentFile)) {
    throw "Missing .env.production. Copy .env.production.example first."
}

if ($Action -in $SecretRequiredActions) {
    $environmentText = Get-Content -LiteralPath $EnvironmentFile -Raw
    if ($environmentText -match "REPLACE_WITH_|CHANGE_ME|CHANGEME") {
        throw (
            ".env.production still contains placeholder secrets. " +
            "Replace every placeholder before running $Action."
        )
    }
}

switch ($Action) {
    "validate" {
        Invoke-Compose config
    }
    "build" {
        Invoke-Compose build --pull
    }
    "up" {
        Invoke-Compose up -d
        Invoke-Compose ps
    }
    "down" {
        Invoke-Compose down
    }
    "logs" {
        Invoke-Compose logs -f
    }
    "ps" {
        Invoke-Compose ps
    }
    "restart" {
        Invoke-Compose restart
        Invoke-Compose ps
    }
}
