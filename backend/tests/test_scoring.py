from backend.services.scoring import (
    score_draft,
    score_ending,
    calculate_softness_score,
    check_calm_consistency,
    calculate_asymmetry_score,
    check_mobile_readability,
    calculate_time_to_read,
)

def test_score_draft_linkedin_optimal():
    draft = "Hi John,\n\nI noticed your post about the Senior Engineer role. I'd love to apply given my background in Python and distributed systems.\n\nAre you open to a quick chat?"
    score = score_draft(draft, "linkedin")
    assert score > 80

def test_score_draft_email_optimal():
    draft = "Subject: Quick question\n\nHi John,\n\nI noticed your post about the Senior Engineer role. I'd love to apply given my background in Python and distributed systems.\n\nAre you open to a quick chat?"
    score = score_draft(draft, "email")
    assert score > 80

def test_score_draft_too_long():
    draft = "Hi John,\n\n" + "I am very interested. " * 50
    score = score_draft(draft, "linkedin")
    assert score < 100

def test_score_draft_too_many_questions():
    draft = "Hi John, how are you? Are you hiring? Can we chat? What's your schedule?"
    score = score_draft(draft, "linkedin")
    assert score < 100

def test_score_ending_good():
    score = score_ending("Are you open to a quick chat?", "linkedin")
    assert score >= 10.0

def test_score_ending_bad():
    score = score_ending("Looking forward to hearing from you soon.", "linkedin")
    assert score <= 5.0

def test_calculate_softness_score():
    soft = calculate_softness_score("I was wondering if you might be open to a quick chat.")
    assert soft > 0
    hard = calculate_softness_score("Let's schedule a 15 min call. I need a job.")
    assert hard < 0

def test_check_calm_consistency():
    calm_score = check_calm_consistency("This is a normal sentence.")
    assert calm_score > 0
    hype_score = check_calm_consistency("This is AMAZING!!! Synergy! Revolutionary!")
    assert hype_score < 0

def test_calculate_asymmetry_score():
    score = calculate_asymmetry_score(
        "Short.\n\nThis is a much longer paragraph that will definitely create asymmetry compared to the short one."
    )
    assert score >= 0  # Should be >= 0 for asymmetric paragraphs
    
    score_sym = calculate_asymmetry_score(
        "This is a paragraph of text.\n\nThis is a paragraph of text."
    )
    assert score_sym < 0  # Should be < 0 for symmetric paragraphs

def test_check_mobile_readability():
    readable_score = check_mobile_readability("This is a short message. It has two sentences.", "linkedin")
    assert readable_score >= 0
    
    long_pgraph = "This is a very long paragraph that will fail the mobile readability check because it is over thirty five words and it just keeps going on and on and on and on making it very difficult for anyone to read on a small mobile device screen without losing their place or getting bored."
    unreadable_score = check_mobile_readability(long_pgraph, "linkedin")
    assert unreadable_score < 0

def test_calculate_time_to_read():
    ttr = calculate_time_to_read("This is a five word sentence.")
    assert ttr > 0
    assert ttr < 5
