# src/api/sanitizer.py

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import logging

logger = logging.getLogger(__name__)

MAX_CODE_LENGTH = 10000

class PIIScrubber:
    """
    Scrubs PII from text before logging or storing.

    Resumes contain highly sensitive personal data — names, emails,
    phone numbers, addresses. This class ensures none of that is ever
    written to logs or persisted outside the request lifecycle.
    """

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.pii_types = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "LOCATION", "US_SSN", "CREDIT_CARD", "DATE_TIME"
        ]

    def scrub(self, text: str) -> str:
        """Replace PII with placeholder tokens for safe logging."""
        if not text or not isinstance(text, str):
            return ""

        results = self.analyzer.analyze(
            text=text,
            entities=self.pii_types,
            language="en"
        )

        if not results:
            return "[RESUME_TEXT_REDACTED]"

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results
        )
        return anonymized.text

    def safe_log_metadata(self, text: str) -> dict:
        """
        Return only safe metadata about a document — never the content.
        This is all that ever appears in logs.
        """
        return {
            "char_count": len(text),
            "word_count": len(text.split()),
            "pii_entities_found": len(
                self.analyzer.analyze(
                    text=text,
                    entities=self.pii_types,
                    language="en"
                )
            )
        }