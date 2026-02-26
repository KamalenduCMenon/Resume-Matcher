# tests/conftest.py
import pytest
from src.model.matcher import ResumeMatcher
from src.api.sanitizer import PIIScrubber

@pytest.fixture(scope="module")
def matcher():
    return ResumeMatcher()

@pytest.fixture(scope="module")
def scrubber():
    return PIIScrubber()