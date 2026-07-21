from enum import StrEnum


class EvidenceCategory(StrEnum):
    TRANSACTION = "transaction"
    SCREENSHOT = "screenshot"
    BANK_STATEMENT = "bank_statement"
    CUSTOMER_DOCUMENT = "customer_document"
    EMAIL = "email"
    DEVICE_LOG = "device_log"
    EXPORT = "export"
    OTHER = "other"


class EvidenceEvent(StrEnum):
    UPLOADED = "case.evidence.uploaded"
    DOWNLOADED = "case.evidence.downloaded"
    DELETED = "case.evidence.deleted"
