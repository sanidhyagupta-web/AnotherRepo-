from __future__ import annotations
import logging
from pathlib import Path
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)

# Executable magic bytes to reject
_DANGEROUS_HEADERS: list[bytes] = [
    b"MZ",           # PE/EXE
    b"\x7fELF",      # ELF
    b"#!/",          # shebang
]

_PDF_MAGIC = b"%PDF"


def _detect_mime(data: bytes) -> str:
    if data[:4] == _PDF_MAGIC:
        return "application/pdf"
    try:
        data[:512].decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        return "application/octet-stream"


def validate_file(file_path: str | Path) -> Tuple[bool, str]:
    """
    Returns (is_valid, reason).
    reason is empty string on success.
    """
    path = Path(file_path)

    if not path.exists():
        return False, "File does not exist"

    size = path.stat().st_size
    if size == 0:
        return False, "File is empty"
    if size > settings.max_file_size_bytes:
        mb = settings.max_file_size_bytes // (1024 * 1024)
        return False, f"File exceeds {mb} MB limit"

    with open(path, "rb") as f:
        header = f.read(512)

    for dangerous in _DANGEROUS_HEADERS:
        if header.startswith(dangerous):
            return False, "Executable/malicious file type rejected"

    detected_mime = _detect_mime(header)
    if detected_mime not in settings.allowed_mime_types:
        return False, f"MIME type {detected_mime!r} not allowed"

    return True, ""
