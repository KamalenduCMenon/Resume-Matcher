# tests/integration/test_api.py

import pytest
from fastapi.testclient import TestClient
from src.api.app import app

# Override allowed hosts for testing — TrustedHostMiddleware blocks 'testclient' by default
app.router.on_startup.clear()
client = TestClient(app, headers={"host": "localhost"})


class TestHealthEndpoint:

    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_returns_model_name(self):
        response = client.get("/health")
        assert "model" in response.json()


class TestMatchEndpoint:

    def test_valid_request_returns_200(self):
        response = client.post("/match", json={
            "resume": "Python developer with 5 years experience in FastAPI and machine learning",
            "job_description": "Looking for a Python developer with ML and API experience"
        })
        assert response.status_code == 200

    def test_response_contains_match_block(self):
        response = client.post("/match", json={
            "resume": "Python developer with FastAPI and PostgreSQL experience",
            "job_description": "Python developer needed with API and database skills"
        })
        data = response.json()
        assert "match" in data
        assert "score" in data["match"]
        assert "percentage" in data["match"]
        assert "band" in data["match"]

    def test_response_contains_keywords_block(self):
        response = client.post("/match", json={
            "resume": "Python developer with FastAPI experience",
            "job_description": "Python developer with Docker and Kubernetes experience"
        })
        data = response.json()
        assert "keywords" in data
        assert "missing_keywords" in data["keywords"]
        assert "present_keywords" in data["keywords"]
        assert "coverage_score" in data["keywords"]

    def test_response_contains_privacy_note(self):
        response = client.post("/match", json={
            "resume": "Python developer with 5 years experience",
            "job_description": "Python developer needed"
        })
        assert "privacy_note" in response.json()

    def test_empty_resume_returns_422(self):
        response = client.post("/match", json={
            "resume": "",
            "job_description": "Some job description"
        })
        assert response.status_code == 422

    def test_empty_jd_returns_422(self):
        response = client.post("/match", json={
            "resume": "Some resume text with enough content",
            "job_description": ""
        })
        assert response.status_code == 422

    def test_whitespace_only_resume_returns_422(self):
        response = client.post("/match", json={
            "resume": "     ",
            "job_description": "Some job description"
        })
        assert response.status_code == 422

    def test_oversized_resume_returns_422(self):
        response = client.post("/match", json={
            "resume": "x" * 11000,
            "job_description": "Some job description"
        })
        assert response.status_code == 422

    def test_score_is_numeric(self):
        response = client.post("/match", json={
            "resume": "Python developer machine learning FastAPI",
            "job_description": "Python ML developer needed with FastAPI skills"
        })
        score = response.json()["match"]["score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_missing_resume_field_returns_422(self):
        response = client.post("/match", json={
            "job_description": "Some job description"
        })
        assert response.status_code == 422


class TestUploadResumeEndpoint:

    def test_missing_job_description_returns_422(self):
        response = client.post(
            "/upload-resume",
            files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"job_description": ""}
        )
        assert response.status_code == 422

    def test_non_pdf_file_returns_422(self):
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"fake image content"
        response = client.post(
            "/upload-resume",
            files={"file": ("resume.pdf", png_bytes, "application/pdf")},
            data={"job_description": "Python developer needed"}
        )
        # API returns 422 for invalid file content (caught as PDFInvalidError)
        assert response.status_code == 422
        
    def test_empty_file_returns_422(self):
        response = client.post(
            "/upload-resume",
            files={"file": ("resume.pdf", b"", "application/pdf")},
            data={"job_description": "Python developer needed"}
        )
        assert response.status_code == 422