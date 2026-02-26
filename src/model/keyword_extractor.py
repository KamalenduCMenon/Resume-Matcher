# src/model/keyword_extractor.py

from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

# Common resume filler words that add no signal
RESUME_STOP_WORDS = [
    "experience", "work", "years", "ability", "strong",
    "excellent", "good", "team", "responsible", "skills",
    "looking", "seeking", "motivated", "passionate", "dynamic"
]

def extract_keyword_gaps(
    resume_text: str,
    job_description: str,
    top_n: int = 10
) -> dict:
    """
    Identifies keywords in the job description that are missing or
    underrepresented in the resume.

    Returns:
        missing_keywords  — top JD terms not found in the resume
        present_keywords  — top JD terms already in the resume
        coverage_score    — % of JD keywords found in resume
    """
    if not resume_text or not job_description:
        return {
            "missing_keywords": [],
            "present_keywords": [],
            "coverage_score": "0.0%"
        }

    # Fit TF-IDF on the JD only — we want terms important to the JD
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),   # single words and two-word phrases
        max_features=200
    )

    vectorizer.fit([job_description])
    jd_terms = set(vectorizer.get_feature_names_out())

    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    missing = []
    present = []

    for term in jd_terms:
        # Skip filler words
        if any(stop in term for stop in RESUME_STOP_WORDS):
            continue
        if term in resume_lower:
            present.append(term)
        else:
            missing.append(term)

    # Rank missing terms by their TF-IDF weight in the JD
    # (most important missing terms come first)
    jd_vector = vectorizer.transform([job_description]).toarray()[0]
    feature_names = vectorizer.get_feature_names_out()
    term_scores = dict(zip(feature_names, jd_vector))

    missing_sorted = sorted(
        missing,
        key=lambda t: term_scores.get(t, 0),
        reverse=True
    )[:top_n]

    present_sorted = sorted(
        present,
        key=lambda t: term_scores.get(t, 0),
        reverse=True
    )[:top_n]

    total = len(missing) + len(present)
    coverage = len(present) / total if total > 0 else 0.0

    return {
        "missing_keywords": missing_sorted,
        "present_keywords": present_sorted,
        "coverage_score": f"{coverage * 100:.1f}%"
    }