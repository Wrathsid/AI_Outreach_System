from backend.services.signals import (
    extract_primary_signal,
    _detect_hiring_context,
    clean_candidate_data,
    sanitize_scraped_content,
    remove_hedging,
)

def test_extract_primary_signal_hiring():
    c = {"summary": "We are hiring a Senior Engineer! Apply now."}
    signal = extract_primary_signal(c)
    assert signal["type"] == "hiring_post"
    assert not signal["is_generic"]

def test_extract_primary_signal_achieve():
    c = {"summary": "I just launched a new feature successfully."}
    signal = extract_primary_signal(c)
    assert signal["type"] == "summary"

def test_detect_hiring_context():
    c = {"summary": "We are looking for a Python Developer to join our team."}
    ctx = _detect_hiring_context(c)
    assert ctx["is_hiring_post"] is True
    assert ctx["hiring_role"] == "Python Developer"

def test_detect_hiring_context_negative():
    c = {"summary": "I hate the hiring process."}
    ctx = _detect_hiring_context(c)
    assert ctx["is_hiring_post"] is False

def test_clean_candidate_data():
    c = {
        "name": "John Doe hr hiring",
        "title": "Unknown",
        "company": "N/A"
    }
    cleaned = clean_candidate_data(c)
    assert cleaned["name"] == "John Doe hr hiring"  # Currently the cleaner just replaces unknown/n/a
    assert cleaned["title"] is None
    assert cleaned["company"] is None

def test_sanitize_scraped_content():
    text = "Here is an email: test@example.com and a link: https://google.com."
    sanitized = sanitize_scraped_content(text)
    assert "test@example.com" not in sanitized
    assert "https://google.com" not in sanitized

def test_remove_hedging():
    draft = "I think I might be a good fit."
    cleaned = remove_hedging(draft)
    assert "I think" not in cleaned
