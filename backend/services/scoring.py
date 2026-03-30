"""
Scoring functions for draft quality assessment.

Contains deterministic scoring heuristics for reply probability,
mobile readability, linguistic softness, and structural analysis.
Extracted from drafts.py for maintainability.
"""

import re
from typing import Optional


def score_draft(text: str, contact_type: str, candidate_context: Optional[dict] = None) -> float:
    """Deterministic scoring for reply probability.

    Higher scores = better reply probability.
    Sweet spots: LinkedIn 1000-2000 chars, exactly 1 question, curiosity over CTA.
    """
    score = 100.0

    # 0. Sanity Check
    if not text or len(text.strip()) < 10:
        return 0.0

    # Length sweet spot
    length = len(text)
    if 1500 <= length <= 2500:
        score += 20
    elif length < 1000:
        score -= 10
    elif length > 2500:
        score -= 15

    # Question count (exactly 1 is ideal)
    question_count = text.count("?")
    if question_count == 1:
        score += 15
    elif question_count == 0:
        score -= 5
    else:
        score -= 10 * (question_count - 1)

    # Ends with curiosity (not hard CTA)
    last_50 = text.lower()[-50:]
    cta_words = [
        "schedule",
        "call",
        "meeting",
        "chat sometime",
        "book a",
        "let's connect",
        "happy to chat",
    ]
    if any(word in last_50 for word in cta_words):
        score -= 25  # Increased penalty for generic CTAs

    # Gemini "Over-Helpful" Artifacts Check (CRITICAL)
    banned_phrases = [
        "as an ai",
        "i understand",
        "hope this message finds you",
        "wanted to reach out",
        "writing to explore",
        "love the opportunity",
        "please let me know if",
        "additionally,",
        "moreover,",
        "it's important to note",
        "based on your request",
        "this message is intended",
    ]
    for phrase in banned_phrases:
        if phrase in text.lower():
            score -= 50  # Kill this draft

    # Structure Enforcement
    if text.count("?") > 4:
        score -= 50

    # Flexible Endings
    if text.count("?") == 0:
        soft_endings = ["curious", "wondering", "thoughts", "perspective", "interest"]
        last_sentence = text.strip().split(".")[-1].lower()
        if any(w in last_sentence for w in soft_endings):
            score += 10
        else:
            score -= 5

    # Preview Sanity Check
    first_100 = text[:100].lower()
    bad_starts = ["reaching out to", "apologize", "sorry for", "hope you are"]
    if any(b in first_100 for b in bad_starts):
        score -= 50

    # Pronoun Dominance Check
    i_count = len(re.findall(r"\bI\b", text))
    you_count = len(re.findall(r"\byou\b", text, re.IGNORECASE))

    if i_count > 2 and you_count == 0:
        score -= 15
    elif i_count > 2:
        score -= 5 * (i_count - 2)

    # Check for their name/company mention
    if candidate_context:
        name_first = (
            candidate_context.get("name", "").split()[0]
            if candidate_context.get("name")
            else ""
        )
        company = candidate_context.get("company", "")

        if name_first and name_first.lower() in text.lower():
            score += 5
        if company and company.lower() in text.lower():
            mentions = text.lower().count(company.lower())
            if mentions == 1:
                score += 5
            elif mentions > 1:
                score -= 5

    # PATH A OPTIMIZATIONS
    ending_score = score_ending(text, contact_type)
    score += ending_score

    softness_score = calculate_softness_score(text)
    score += softness_score

    calm_score = check_calm_consistency(text)
    score += calm_score

    readability_score = check_mobile_readability(text, contact_type)
    score += readability_score

    ttr = calculate_time_to_read(text)
    if ttr > 180:
        score -= 10

    asymmetry_score = calculate_asymmetry_score(text)
    score += asymmetry_score

    return max(0, score)


def calculate_time_to_read(text: str) -> int:
    """Estimate reading time in seconds (approx 200 wpm / 3.3 wps)."""
    words = len(text.split())
    return round(words / 3.3)


def score_ending(text: str, contact_type: str) -> float:
    """Score the final sentence for reply probability (Optimization 15)."""
    lines = text.strip().split("\n")
    last_line = lines[-1].lower() if lines else ""

    score = 0.0

    good_endings = [
        "curious what you think",
        "open to a quick exchange",
        "would you be up for that",
        "any thoughts on this",
        "interested in your take",
        "curious to hear",
    ]

    bad_endings = [
        "let's connect",
        "let me know",
        "happy to chat",
        "reach out",
        "schedule",
        "book a",
        "set up a call",
        "grab coffee",
        "sincerely",
        "best regards",
        "best,",
        "cheers",
        "warmly",
    ]

    for good in good_endings:
        if good in last_line:
            score += 20
            break

    for bad in bad_endings:
        if bad in last_line:
            score -= 25
            break

    if last_line.endswith("?"):
        score += 15
    elif last_line.endswith("."):
        score += 5

    return score


def calculate_softness_score(text: str) -> float:
    """Measure linguistic softness — higher is better (Optimization 14)."""
    score = 0.0
    text_lower = text.lower()

    soft_modals = [
        "might", "could", "wondering", "curious",
        "perhaps", "possibly", "would you",
    ]
    for modal in soft_modals:
        score += text_lower.count(modal) * 5

    imperatives = ["you should", "you need", "you must", "let's", "we should"]
    for imp in imperatives:
        score -= text_lower.count(imp) * 10

    future_words = ["will be", "going to", "excited to", "looking forward"]
    for fw in future_words:
        score -= text_lower.count(fw) * 8

    return score


def check_calm_consistency(text: str) -> float:
    """Ensure psychological calmness in tone (Optimization 20)."""
    score = 0.0

    exclamation_count = text.count("!")
    if exclamation_count == 0:
        score += 10
    else:
        score -= 15 * exclamation_count

    words = text.split()
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    score -= len(caps_words) * 10

    hype_verbs = [
        "revolutionize", "disrupt", "transform",
        "amazing", "incredible", "awesome",
    ]
    for hype in hype_verbs:
        if hype in text.lower():
            score -= 20

    sentences = [s.strip() for s in text.split(".") if s.strip()]
    for sent in sentences:
        word_count = len(sent.split())
        if 10 <= word_count <= 20:
            score += 3
        elif word_count > 30:
            score -= 5

    return score


def check_mobile_readability(text: str, contact_type: str) -> float:
    """Ensure message passes mobile glance test (Optimization 16)."""
    score = 0.0

    lines = text.split("\n")

    for line in lines:
        if len(line) > 120:
            score -= 5

    if contact_type == "email":
        paragraph_count = len([p for p in lines if p.strip()])
        if 2 <= paragraph_count <= 3:
            score += 15
        elif paragraph_count > 4:
            score -= 10

    sentences = [s.strip() for s in text.split(".") if s.strip()]
    for sent in sentences:
        words = len(sent.split())
        if words > 25:
            score -= 5

    return score


def calculate_asymmetry_score(text: str) -> float:
    """Penalize drafts with perfectly symmetrical paragraph lengths (Phase 2).

    Humans write with variance. Robots write in blocks.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        return 0

    score = 0.0
    lengths = [len(p) for p in paragraphs]

    for i in range(len(lengths) - 1):
        len1 = lengths[i]
        len2 = lengths[i + 1]

        if len1 == 0 or len2 == 0:
            continue

        ratio = max(len1, len2) / min(len1, len2)

        if ratio < 1.15:
            score -= 20
        elif 1.5 <= ratio <= 3.0:
            score += 10

    return score
