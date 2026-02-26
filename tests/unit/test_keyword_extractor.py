# tests/unit/test_keyword_extractor.py
from src.model.keyword_extractor import extract_keyword_gaps

class TestKeywordExtractor:

    def test_detects_missing_keywords(self):
        resume = "Python developer with REST API experience"
        jd = "Python developer with Docker and Kubernetes experience"
        result = extract_keyword_gaps(resume, jd)
        assert len(result["missing_keywords"]) > 0

    def test_detects_present_keywords(self):
        resume = "Python developer with FastAPI and PostgreSQL"
        jd = "Looking for Python developer with FastAPI and PostgreSQL skills"
        result = extract_keyword_gaps(resume, jd)
        assert len(result["present_keywords"]) > 0

    def test_coverage_score_is_percentage_string(self):
        resume = "Python FastAPI developer"
        jd = "Python FastAPI developer needed"
        result = extract_keyword_gaps(resume, jd)
        assert "%" in result["coverage_score"]

    def test_empty_inputs_return_empty_lists(self):
        result = extract_keyword_gaps("", "")
        assert result["missing_keywords"] == []
        assert result["present_keywords"] == []

    def test_returns_at_most_top_n_keywords(self):
        resume = "developer"
        jd = "Python FastAPI Docker Kubernetes AWS machine learning PyTorch Redis PostgreSQL CI CD"
        result = extract_keyword_gaps(resume, jd, top_n=5)
        assert len(result["missing_keywords"]) <= 5