# src/model/matcher.py

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os

logger = logging.getLogger(__name__)

# Lightweight model that runs fully locally — no data sent externally
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

class ResumeMatcher:
    """
    Computes semantic similarity between a resume and a job description
    using sentence transformers.

    Privacy: All inference is local. No text ever leaves your machine.
    """

    _instance = None  # Singleton — avoids reloading the model on every request

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info(f"Loading embedding model: {MODEL_NAME}")
            cls._instance.model = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded successfully")
        return cls._instance

    def score(self, resume_text: str, job_description: str) -> dict:
        """
        Returns a similarity score, percentage, and human-readable band.

        Raises ValueError for empty inputs.
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty")

        # Truncate to avoid memory spikes on very large documents
        resume_text = resume_text[:8000]
        job_description = job_description[:4000]

        embeddings = self.model.encode([resume_text, job_description])
        raw_score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

        # Map cosine score to a human-readable band
        if raw_score >= 0.80:
            band = "Strong Match"
        elif raw_score >= 0.60:
            band = "Moderate Match"
        elif raw_score >= 0.40:
            band = "Weak Match"
        else:
            band = "Poor Match"

        return {
            "score": round(raw_score, 4),
            "percentage": f"{raw_score * 100:.1f}%",
            "band": band
        }