# tests/unit/test_sanitizer.py

class TestPIIScrubber:

    def test_scrubs_email(self, scrubber):
        text = "Contact me at john.doe@example.com for more info"
        result = scrubber.scrub(text)
        assert "john.doe@example.com" not in result

    def test_scrubs_phone_number(self, scrubber):
        text = "Call me at 416-555-1234"
        result = scrubber.scrub(text)
        assert "416-555-1234" not in result

    def test_metadata_never_contains_raw_text(self, scrubber):
        text = "My name is John Smith, email: john@test.com"
        meta = scrubber.safe_log_metadata(text)
        assert "John" not in str(meta)
        assert "john@test.com" not in str(meta)

    def test_metadata_contains_expected_keys(self, scrubber):
        text = "Some sample resume text here"
        meta = scrubber.safe_log_metadata(text)
        assert "char_count" in meta
        assert "word_count" in meta
        assert "pii_entities_found" in meta

    def test_empty_string_returns_empty(self, scrubber):
        assert scrubber.scrub("") == ""

    def test_none_returns_empty(self, scrubber):
        assert scrubber.scrub(None) == ""

    def test_word_count_is_accurate(self, scrubber):
        text = "one two three four five"
        meta = scrubber.safe_log_metadata(text)
        assert meta["word_count"] == 5