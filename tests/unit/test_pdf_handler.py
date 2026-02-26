# tests/unit/test_pdf_handler.py
import pytest
from unittest.mock import AsyncMock, patch
from src.api.pdf_handler import (
    extract_text_from_pdf,
    PDFTooLargeError,
    PDFInvalidError,
    PDFEmptyError,
    MAX_PDF_SIZE_BYTES,
    PDF_MAGIC_BYTES
)

def make_mock_upload(content: bytes) -> AsyncMock:
    """Helper: create a mock UploadFile with given byte content."""
    mock_file = AsyncMock()
    mock_file.filename = "resume.pdf"
    mock_file.read = AsyncMock(return_value=content)
    return mock_file

class TestPDFHandler:

    @pytest.mark.asyncio
    async def test_valid_pdf_returns_text(self):
        mock_file = make_mock_upload(PDF_MAGIC_BYTES + b"-1.4 fake content")
        with patch("src.api.pdf_handler.extract_text", return_value="Python developer with 5 years experience"):
            result = await extract_text_from_pdf(mock_file)
        assert "Python" in result

    @pytest.mark.asyncio
    async def test_oversized_file_raises_too_large(self):
        oversized = PDF_MAGIC_BYTES + b"x" * MAX_PDF_SIZE_BYTES
        mock_file = make_mock_upload(oversized)
        with pytest.raises(PDFTooLargeError, match="5MB"):
            await extract_text_from_pdf(mock_file)

    @pytest.mark.asyncio
    async def test_empty_file_raises_pdf_empty(self):
        mock_file = make_mock_upload(b"")
        with pytest.raises(PDFEmptyError, match="empty"):
            await extract_text_from_pdf(mock_file)

    @pytest.mark.asyncio
    async def test_png_disguised_as_pdf_raises_invalid(self):
        png_content = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        mock_file = make_mock_upload(png_content)
        with pytest.raises(PDFInvalidError, match="valid PDF"):
            await extract_text_from_pdf(mock_file)

    @pytest.mark.asyncio
    async def test_scanned_image_pdf_raises_empty(self):
        mock_file = make_mock_upload(PDF_MAGIC_BYTES + b"-1.4 scanned")
        with patch("src.api.pdf_handler.extract_text", return_value="   "):
            with pytest.raises(PDFEmptyError, match="no extractable text"):
                await extract_text_from_pdf(mock_file)

    @pytest.mark.asyncio
    async def test_corrupt_pdf_raises_invalid(self):
        from pdfminer.pdfparser import PDFSyntaxError as PdfErr
        mock_file = make_mock_upload(PDF_MAGIC_BYTES + b"-1.4 corrupt")
        with patch("src.api.pdf_handler.extract_text", side_effect=PdfErr("bad")):
            with pytest.raises(PDFInvalidError, match="could not be parsed"):
                await extract_text_from_pdf(mock_file)