"""
Detect whether a PDF contains selectable text (typed) or is image-only (scanned).
Falls back gracefully if PyMuPDF is unavailable.
"""
from __future__ import annotations
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DOC_TYPED_PDF = "typed_pdf"
DOC_SCANNED_PDF = "scanned_pdf"
DOC_TEXT = "text"


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _page_image_coverage(page) -> float:
    """
    Approximate the fraction of page area occupied by embedded images.
    0.0 = no image area, 1.0 = full-page image.
    """
    try:
        page_area = max(page.rect.width * page.rect.height, 1.0)
        total_image_area = 0.0

        for img in page.get_images(full=True):
            xref = img[0]
            rects = page.get_image_rects(xref)
            for rect in rects:
                total_image_area += max(rect.width * rect.height, 0.0)

        return min(total_image_area / page_area, 1.0)
    except Exception:
        return 0.0


def detect_doc_type(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return DOC_TEXT

    if suffix != ".pdf":
        return DOC_TEXT  # treat unknown as plain text

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(path))
        page_count = len(doc)
        typed_pages = 0
        scanned_pages = 0

        for page in doc:
            text = page.get_text("text").strip()
            chars = len(text)
            words = _word_count(text)
            image_coverage = _page_image_coverage(page)

            # Page-level typed signal: meaningful selectable text
            if chars >= 120 or words >= 20:
                typed_pages += 1
                continue

            # Page-level scanned signal: little/no text + image-dominant layout
            if chars <= 25 and image_coverage >= 0.60:
                scanned_pages += 1
                continue

            # Ambiguous pages contribute weakly to typed bucket if some text exists.
            if chars >= 40 or words >= 8:
                typed_pages += 1

        doc.close()

        if page_count == 0:
            return DOC_SCANNED_PDF

        typed_ratio = typed_pages / page_count
        scanned_ratio = scanned_pages / page_count

        # Document-level decision.
        # We choose scanned for mixed docs when there is substantial scanned content
        # to avoid dropping OCR-only pages.
        if scanned_ratio >= 0.30 and scanned_pages >= 1:
            return DOC_SCANNED_PDF
        if typed_ratio >= 0.60:
            return DOC_TYPED_PDF

        # Fallback tie-breaker: low typed evidence implies scanned.
        return DOC_SCANNED_PDF

    except ImportError:
        logger.warning("PyMuPDF not installed; defaulting to typed_pdf")
        return DOC_TYPED_PDF
    except Exception as exc:
        logger.warning("Doc type detection failed for %s: %s", path, exc)
        return DOC_SCANNED_PDF
