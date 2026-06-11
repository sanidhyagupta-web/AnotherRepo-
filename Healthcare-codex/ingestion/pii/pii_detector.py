"""
PII detection using Microsoft Presidio with regex fallback.

Detects: PATIENT_NAME, MRN, DATE, PHONE_NUMBER, EMAIL_ADDRESS, SSN.
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_presidio_available: bool | None = None  # None = unchecked

# Whole-match patterns — the entire match is the PII span
_PATTERNS: dict[str, re.Pattern] = {
    "PHONE_NUMBER": re.compile(
        r"(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}"
    ),
    "EMAIL_ADDRESS": re.compile(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
    ),
    "DATE": re.compile(
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}"
    ),
    "SSN": re.compile(
        r"\d{3}\-\d{2}\-\d{4}"
    ),
}

# Group-based patterns — group(1) is the PII span, allowing a non-PII label prefix
_GROUP_PATTERNS: dict[str, re.Pattern] = {
    "PATIENT_NAME": re.compile(
        r"(?:Patient\s+Name|Name)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
    ),
    "MRN": re.compile(
        r"MRN\s*:\s*([A-Z0-9]{4,12})"
    ),
}


@dataclass
class PiiEntity:
    entity_type: str
    start: int
    end: int
    text: str
    score: float


def detect_pii(text: str) -> list[PiiEntity]:
    global _presidio_available
    entities: list[PiiEntity] = []

    if _presidio_available is None:
        try:
            from presidio_analyzer import AnalyzerEngine  # noqa: F401
            _presidio_available = True
        except ImportError:
            _presidio_available = False
            logger.warning("presidio_analyzer not installed; using regex fallback")

    if _presidio_available:
        try:
            from presidio_analyzer import AnalyzerEngine
            analyzer = AnalyzerEngine()
            results = analyzer.analyze(text=text, language="en")
            for r in results:
                entities.append(PiiEntity(
                    entity_type=r.entity_type,
                    start=r.start,
                    end=r.end,
                    text=text[r.start:r.end],
                    score=r.score,
                ))
            logger.debug("Presidio detected %d PII entities", len(entities))
        except Exception as exc:
            logger.error("Presidio error: %s; falling back to regex", exc)
            _presidio_available = False

    # Always run medical-specific regex patterns (Presidio doesn't cover MRN,
    # patient name labels, or domain-specific date formats)
    if not _presidio_available:
        for entity_type, pattern in _PATTERNS.items():
            for match in pattern.finditer(text):
                entities.append(PiiEntity(
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    text=match.group(),
                    score=0.85,
                ))

    for entity_type, pattern in _GROUP_PATTERNS.items():
        for match in pattern.finditer(text):
            entities.append(PiiEntity(
                entity_type=entity_type,
                start=match.start(1),
                end=match.end(1),
                text=match.group(1),
                score=0.85,
            ))

    # Deduplicate overlapping spans (keep highest score)
    entities.sort(key=lambda e: (e.start, -e.score))
    deduped: list[PiiEntity] = []
    last_end = -1
    for e in entities:
        if e.start >= last_end:
            deduped.append(e)
            last_end = e.end

    return deduped
