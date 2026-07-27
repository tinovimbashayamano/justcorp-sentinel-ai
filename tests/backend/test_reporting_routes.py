"""Contract tests for the fraud-case reporting API routes."""

from __future__ import annotations

from backend.app.main import app


EXPECTED_REPORTING_OPERATIONS = {
    ("POST", "/api/v1/reports/cases/{case_id}"),
    ("GET", "/api/v1/reports/cases/{case_id}"),
    ("GET", "/api/v1/reports"),
    ("GET", "/api/v1/reports/{report_id}"),
    ("GET", "/api/v1/reports/{report_id}/download"),
    ("GET", "/api/v1/reports/{report_id}/integrity"),
    ("DELETE", "/api/v1/reports/{report_id}"),
    ("POST", "/api/v1/reports/{report_id}/restore"),
}


def _reporting_operations() -> set[tuple[str, str]]:
    """Return reporting methods and paths from the OpenAPI schema."""

    schema = app.openapi()
    operations: set[tuple[str, str]] = set()

    for path, path_operations in schema["paths"].items():
        if not path.startswith("/api/v1/reports"):
            continue

        for method in path_operations:
            normalized_method = method.upper()
            if normalized_method in {
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            }:
                operations.add((normalized_method, path))

    return operations


def test_all_reporting_routes_are_registered() -> None:
    assert _reporting_operations() == EXPECTED_REPORTING_OPERATIONS


def test_reporting_routes_have_expected_tag() -> None:
    schema = app.openapi()

    for path, operations in schema["paths"].items():
        if not path.startswith("/api/v1/reports"):
            continue

        for method, operation in operations.items():
            if method.lower() not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
            }:
                continue
            assert "Fraud Case Reports" in operation["tags"]


def test_report_generation_route_accepts_request_body() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/reports/cases/{case_id}"
    ]["post"]

    assert "requestBody" in operation
    assert operation["responses"].get("201") is not None


def test_download_route_declares_report_content_types() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/reports/{report_id}/download"
    ]["get"]
    content = operation["responses"]["200"]["content"]

    assert "application/json" in content
    assert "text/csv" in content
    assert "application/pdf" in content


def test_reporting_openapi_schemas_are_registered() -> None:
    schemas = app.openapi()["components"]["schemas"]
    expected_schemas = {
        "GeneratedReportListResponse",
        "GeneratedReportResponse",
        "ReportDeleteResponse",
        "ReportFileIntegrityResponse",
        "ReportGenerationAcceptedResponse",
        "ReportGenerationRequest",
        "ReportRestoreResponse",
    }

    assert expected_schemas.issubset(schemas)
