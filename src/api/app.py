# src/api/app.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv

from src.model.matcher import ResumeMatcher
from src.model.keyword_extractor import extract_keyword_gaps
from src.api.sanitizer import PIIScrubber

from fastapi import File, UploadFile
from src.api.pdf_handler import (
    extract_text_from_pdf,
    PDFTooLargeError,
    PDFInvalidError,
    PDFEmptyError
)


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Rate limiter setup ---
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Resume Matcher API", version="1.0.0")
app.state.limiter = limiter

# --- Rate limit error handler ---
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait and try again."}
    )

# --- Security middleware ---
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# --- Load ML components once at startup ---
matcher = ResumeMatcher()
scrubber = PIIScrubber()

MAX_TEXT_LENGTH = 10_000

# --- Request/Response models ---
class MatchRequest(BaseModel):
    resume: str
    job_description: str

    @field_validator("resume", "job_description")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        if len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Field exceeds maximum length of {MAX_TEXT_LENGTH} characters")
        return v.strip()

class MatchResponse(BaseModel):
    match: dict
    keywords: dict
    privacy_note: str

# --- Routes ---
@app.get("/health")
async def health():
    return {"status": "ok", "model": "all-MiniLM-L6-v2"}

@app.post("/match", response_model=MatchResponse)
@limiter.limit("10/minute")
async def match_resume(request: Request, body: MatchRequest):
    """
    Match a resume to a job description.

    Privacy contract:
    - Raw resume text is NEVER logged
    - Only metadata (word count, PII entity count) is logged
    - No data is persisted after the request completes
    """
    try:
        # Log only safe metadata — never raw text
        meta = scrubber.safe_log_metadata(body.resume)
        logger.info(f"Match request received | resume_meta={meta}")

        score_result = matcher.score(body.resume, body.job_description)
        keyword_result = extract_keyword_gaps(body.resume, body.job_description)

        return MatchResponse(
            match=score_result,
            keywords=keyword_result,
            privacy_note="Your resume was processed in memory only and not stored."
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Never log exception message — may contain user text
        logger.error(f"Match error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Matching failed. Please try again.")
@app.post("/upload-resume")
@limiter.limit("5/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = ""
):
    """
    Accept a PDF resume upload, extract text, then run match.

    Privacy contract:
    - Extracted text is NOT logged raw
    - Only metadata (word count, PII entity count) is logged
    - File bytes discarded after extraction, never persisted
    """
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=422, detail="job_description is required")

    if len(job_description) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=422, detail="job_description too long")

    # Extract text — validates size, magic bytes, and content internally
    try:
        resume_text = await extract_text_from_pdf(file)
    except PDFTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except PDFInvalidError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PDFEmptyError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Minimum content check after extraction
    word_count = len(resume_text.split())
    if word_count < 50:
        raise HTTPException(
            status_code=422,
            detail=f"Resume too short ({word_count} words). Minimum is 50 words."
        )

    # Log only safe metadata — never raw text
    meta = scrubber.safe_log_metadata(resume_text)
    logger.info(f"PDF upload processed | metadata={meta}")

    score_result = matcher.score(resume_text, job_description)
    keyword_result = extract_keyword_gaps(resume_text, job_description)

    return {
        "match": score_result,
        "keywords": keyword_result,
        "source": "pdf_upload",
        "privacy_note": "Your resume was processed in memory only and not stored."
    }