# src/api/pdf_handler.py

import io
import logging
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
PDF_MAGIC_BYTES = b"%PDF"


# --- Domain exceptions (keeps HTTP concerns out of this file) ---

class PDFTooLargeError(ValueError):
    pass

class PDFInvalidError(ValueError):
    pass

class PDFEmptyError(ValueError):
    pass


async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Safely extract text from a PDF upload.

    Security controls:
    - File size capped at 5MB before reading full content
    - Magic byte check prevents file type spoofing (.png renamed to .pdf)
    - pdfminer.six used — text extraction only, no JS rendering risk
    - In-memory processing only — nothing written to disk
    - Raw content never logged (may contain PII)
    """

    # 1. Read with size cap
    #    Read 1 byte past the limit so we can detect oversized files
    content = await file.read(MAX_PDF_SIZE_BYTES + 1)

    if len(content) > MAX_PDF_SIZE_BYTES:
        raise PDFTooLargeError("PDF exceeds maximum size of 5MB")

    if len(content) == 0:
        raise PDFEmptyError("Uploaded file is empty")

    # 2. Validate magic bytes — not just the file extension
    #    A malicious user could rename a .exe or .png to .pdf
    if not content.startswith(PDF_MAGIC_BYTES):
        raise PDFInvalidError("File does not appear to be a valid PDF")

    # 3. Extract text using pdfminer (text-only, safe against embedded JS)
    try:
        text = extract_text(io.BytesIO(content))
    except PDFSyntaxError:
        raise PDFInvalidError("PDF content could not be parsed")
    except Exception as e:
        logger.error(f"PDF extraction error: {type(e).__name__}")
        raise PDFInvalidError("PDF processing failed unexpectedly")

    # 4. Reject scanned/image-only PDFs with no extractable text
    if not text or not text.strip():
        raise PDFEmptyError(
            "PDF contains no extractable text. "
            "It may be a scanned image — try copy-pasting your resume text instead."
        )

    return text.strip()