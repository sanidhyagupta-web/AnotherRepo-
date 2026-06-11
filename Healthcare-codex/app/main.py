"""
Entry point for the ingestion pipeline.
Provides a Python API to ingest a single document.
"""
from __future__ import annotations
import uuid
import shutil
import logging
from pathlib import Path

from db.database import init_db
from ingestion.registry import register_document, update_status
from ingestion.validator import validate_file
from ingestion.state_machine import DocStatus
from security.audit_logger import log_event
from app.config import settings
import queues

logger = logging.getLogger(__name__)


def ingest_document(
    file_path: str | Path,
    uploader_id: str = "anonymous",
    patient_id: str = "UNKNOWN",
    department: str = "general",
) -> str:
    """
    Validate and enqueue a document for ingestion.
    Returns the assigned doc_id.
    Raises ValueError on validation failure.
    """
    path = Path(file_path)
    is_valid, reason = validate_file(path)

    if not is_valid:
        log_event("VALIDATION_FAILED", user_id=uploader_id, details={"reason": reason, "file": str(path)})
        dest = settings.failed_dir / "validation" / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        raise ValueError(f"Validation failed: {reason}")

    doc_id = str(uuid.uuid4())
    suffix = path.suffix.lower()

    # Upload raw file to S3 with KMS encryption — never touches local disk after this
    from storage.s3_client import upload_file
    raw_s3_key = f"raw/{doc_id}/{path.name}"
    upload_file(raw_s3_key, path)

    register_document(doc_id, path.name, f"s3://{settings.s3_bucket}/{raw_s3_key}", uploader_id=uploader_id)
    update_status(doc_id, DocStatus.VALIDATED)

    queues.parsing_queue.put({
        "doc_id": doc_id,
        "raw_s3_key": raw_s3_key,
        "file_suffix": suffix,
        "original_filename": path.name,
        "uploader_id": uploader_id,
        "patient_id": patient_id,
        "department": department,
        "retry_count": 0,
    })

    log_event("DOCUMENT_INGESTED", user_id=uploader_id, doc_id=doc_id,
              details={"filename": path.name, "department": department, "s3_key": raw_s3_key})
    logger.info("Document %s uploaded to S3 and enqueued", doc_id)
    return doc_id
