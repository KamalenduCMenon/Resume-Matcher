# Resume Matcher

An ML-powered tool that scores how well a resume matches a job description,
identifies missing keywords, and provides actionable feedback — built with
AI coding assistants and production-grade validation practices.

## Live Demo

1. Start the API: `uvicorn src.api.app:app --reload`
2. Open `frontend/index.html` in your browser
3. Paste a resume and job description → click Analyze

## Features

- Semantic similarity scoring using `sentence-transformers`
- Keyword gap analysis using TF-IDF
- PDF resume upload with security validation
- PII scrubbing on all logs using Microsoft Presidio
- Rate limiting and trusted host middleware
- 41 tests (unit + integration) with 86% coverage
- CI pipeline with automated testing, Bandit SAST, and pip-audit

## Project Structure
```
src/
  api/        ← FastAPI backend, PII sanitizer, PDF handler
  model/      ← Sentence embedding matcher, keyword extractor
tests/
  unit/       ← Component-level tests
  integration/← Full API end-to-end tests
frontend/     ← Browser UI
.github/      ← CI/CD pipeline
```

## Setup
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
uvicorn src.api.app:app --reload
```

## AI Assistant Usage Log

This project was built with AI coding assistants following responsible use practices.

| File | AI Tool | Validation Steps |
|---|---|---|
| `matcher.py` | GitHub Copilot | Verified score range 0–1, unit tested |
| `sanitizer.py` | Claude Code | Tested with 10 synthetic PII samples |
| `pdf_handler.py` | Claude Code | Magic byte test, corrupt PDF test |
| `app.py` | Cursor | Cross-checked with OWASP API Top 10 |
| `test_*.py` | Copilot | Reviewed all cases, added edge cases manually |

### Responsible Use Decisions

- **Privacy first** — Raw resume text never appears in logs. Routed through
  Presidio PII scrubber before any metadata is recorded.
- **Local inference** — `all-MiniLM-L6-v2` runs fully on-device. No resume
  text is ever sent to an external API.
- **Rejected AI suggestions** — Copilot suggested `pickle` for model
  serialization. Rejected due to known deserialization vulnerabilities.
  Used `joblib` instead.
- **AI-generated tests reviewed** — All Copilot test suggestions were
  manually reviewed. Edge cases for whitespace-only input, oversized
  files, and corrupt PDFs were added manually.
- **Deprecated tool replaced** — CI pipeline originally used `safety check`
  (deprecated). Replaced with `pip-audit` after pipeline failure.

## Security

- Input validation on all endpoints (length, empty, whitespace)
- File type validation via magic bytes (not just extension)
- Rate limiting: 10 req/min on `/match`, 5 req/min on `/upload-resume`
- Bandit SAST scan on every CI run
- Dependency vulnerability scan via pip-audit on every CI run