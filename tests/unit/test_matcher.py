# tests/unit/test_matcher.py

class TestResumeMatcher:

    def test_identical_text_scores_near_one(self, matcher):
        text = "Python developer with FastAPI and machine learning experience"
        result = matcher.score(text, text)
        assert result["score"] >= 0.99

    def test_unrelated_text_scores_low(self, matcher):
        resume = "Experienced baker specializing in sourdough and pastries"
        jd = "Senior ML engineer with PyTorch and Kubernetes experience"
        result = matcher.score(resume, jd)
        assert result["score"] < 0.6

    def test_score_is_between_0_and_1(self, matcher):
        result = matcher.score("software engineer Python", "Python developer role")
        assert 0.0 <= result["score"] <= 1.0

    def test_returns_percentage_string(self, matcher):
        result = matcher.score("Python developer", "Python engineer needed")
        assert "%" in result["percentage"]

    def test_returns_valid_band(self, matcher):
        result = matcher.score("Python ML engineer FastAPI", "Python ML engineer FastAPI")
        assert result["band"] in ["Strong Match", "Moderate Match", "Weak Match", "Poor Match"]

    def test_rejects_empty_resume(self, matcher):
        import pytest
        with pytest.raises(ValueError, match="empty"):
            matcher.score("", "some job description")

    def test_rejects_empty_jd(self, matcher):
        import pytest
        with pytest.raises(ValueError, match="empty"):
            matcher.score("some resume text", "")

    def test_rejects_whitespace_only_resume(self, matcher):
        import pytest
        with pytest.raises(ValueError, match="empty"):
            matcher.score("     ", "some job description")