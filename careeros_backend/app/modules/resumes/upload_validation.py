"""Validation for résumé uploads. The client-declared content type and filename are untrusted."""

import io
import re
import zipfile
from typing import Optional

from fastapi import HTTPException, status

MAX_RESUME_BYTES = 5 * 1024 * 1024
MAX_UNCOMPRESSED_DOCX_BYTES = 50 * 1024 * 1024  # zip-bomb guard
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_TYPES = {"application/pdf": ".pdf", DOCX_MIME: ".docx"}
_UNSAFE = re.compile(r"[^A-Za-z0-9._ ()\-]")


def safe_filename(name: Optional[str], extension: str) -> str:
    """Strips directories and odd characters; always ends with the extension that matches the verified type."""
    base = (name or "").replace("\\", "/").split("/")[-1]
    base = _UNSAFE.sub("", base).strip(" .")
    stem = base.rsplit(".", 1)[0] if "." in base else base
    stem = re.sub(r"\s+", " ", stem).strip(" .")[:80]
    return f"{stem or 'resume'}{extension}"


def looks_like(content_type: str, data: bytes) -> bool:
    """True when the bytes really are the declared type (magic bytes / container structure)."""
    if content_type == "application/pdf":
        return b"%PDF-" in data[:1024]
    if content_type == DOCX_MIME:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()
                total = sum(i.file_size for i in z.infolist())
            return "word/document.xml" in names and total <= MAX_UNCOMPRESSED_DOCX_BYTES
        except (zipfile.BadZipFile, ValueError):
            return False
    return False


def validate_resume_upload(content_type: Optional[str], filename: Optional[str], data: bytes) -> str:
    """Returns the sanitised filename or raises an HTTP error. `data` must be at most MAX_RESUME_BYTES + 1 bytes."""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are supported.")
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. The maximum size is {MAX_RESUME_BYTES // (1024 * 1024)} MB.",
        )
    if not looks_like(content_type, data):
        raise HTTPException(status_code=400, detail="The file content does not match a valid PDF or DOCX document.")
    return safe_filename(filename, ALLOWED_TYPES[content_type])
