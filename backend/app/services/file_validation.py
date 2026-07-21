import hashlib
import re
import unicodedata
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4


ALLOWED_EXTENSIONS = frozenset(
    {"pdf", "png", "jpg", "jpeg", "csv", "txt", "json"}
)
ALLOWED_MIME_TYPES = {
    "pdf": frozenset({"application/pdf"}),
    "png": frozenset({"image/png"}),
    "jpg": frozenset({"image/jpeg"}),
    "jpeg": frozenset({"image/jpeg"}),
    "csv": frozenset({"text/csv", "application/csv", "text/plain"}),
    "txt": frozenset({"text/plain"}),
    "json": frozenset({"application/json", "text/json", "text/plain"}),
}
MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
MAX_FILE_SIZE_BYTES = MAX_UPLOAD_SIZE_BYTES
HASH_CHUNK_SIZE = 1024 * 1024


class FileValidationError(ValueError):
    pass


def sanitize_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise FileValidationError("A filename is required.")

    basename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    normalized = unicodedata.normalize("NFKC", basename).strip()
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", normalized)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")

    if not cleaned:
        raise FileValidationError("The filename is invalid.")

    if len(cleaned) > 255:
        suffix = Path(cleaned).suffix
        cleaned = f"{Path(cleaned).stem[: 255 - len(suffix)]}{suffix}"

    return cleaned


def validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower().lstrip(".")

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileValidationError(
            f"File extension '.{extension}' is not allowed. Allowed: {allowed}."
        )

    return extension


def validate_mime_type(mime_type: str | None, extension: str) -> str:
    normalized = (mime_type or "").split(";", 1)[0].strip().lower()

    if normalized not in ALLOWED_MIME_TYPES.get(extension.lower(), frozenset()):
        raise FileValidationError(
            f"MIME type '{mime_type or 'unknown'}' is not valid for .{extension}."
        )

    return normalized


def validate_file_size(file_size_bytes: int) -> int:
    if file_size_bytes <= 0:
        raise FileValidationError("The uploaded file is empty.")

    if file_size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise FileValidationError("The uploaded file exceeds the 20 MB limit.")

    return file_size_bytes


def compute_sha256(source: bytes | bytearray | Path | str | BinaryIO) -> str:
    digest = hashlib.sha256()

    if isinstance(source, (bytes, bytearray)):
        digest.update(source)
        return digest.hexdigest()

    if isinstance(source, (str, Path)):
        with Path(source).open("rb") as stream:
            for chunk in iter(lambda: stream.read(HASH_CHUNK_SIZE), b""):
                digest.update(chunk)
        return digest.hexdigest()

    position = source.tell() if source.seekable() else None
    for chunk in iter(lambda: source.read(HASH_CHUNK_SIZE), b""):
        digest.update(chunk)
    if position is not None:
        source.seek(position)
    return digest.hexdigest()


def generate_uuid_filename(original_filename: str) -> str:
    extension = validate_extension(sanitize_filename(original_filename))
    return f"{uuid4().hex}.{extension}"


generate_stored_filename = generate_uuid_filename
