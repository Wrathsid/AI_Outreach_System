"""
T1: Prompt contract snapshot tests.
Validates that prompt sections conform to expected structure,
and that CHANNEL_TONE / PERSONA_ANCHOR constants are present.
"""

import sys
import os

# Add project root to path (two levels up from tests/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_prompt_section_order():
    """R3: PROMPT_SECTION_ORDER has all required keys."""
    from backend.routers.drafts import PROMPT_SECTION_ORDER

    required = {
        "system_identity",
        "user_bio",
        "candidate_context",
        "structural_rules",
        "negative_constraints",
        "task_instruction",
    }
    actual = set(PROMPT_SECTION_ORDER)
    missing = required - actual
    assert not missing, f"Missing required sections: {missing}"
    print("  ✓ PROMPT_SECTION_ORDER contains all required keys")


def test_assemble_prompt_order():
    """R3: assemble_prompt produces deterministic output."""
    from backend.routers.drafts import assemble_prompt

    sections = {
        "task_instruction": "Generate a message",
        "system_identity": "You are an AI",
        "user_bio": "Engineer with 5 years experience",
        "candidate_context": "Recruiter at Google",
        "structural_rules": "Keep it short",
        "negative_constraints": "No buzzwords",
    }

    result1 = assemble_prompt(sections)
    result2 = assemble_prompt(sections)
    assert result1 == result2, "assemble_prompt is non-deterministic!"

    # Verify order: system_identity should come before task_instruction
    idx_sys = result1.index("You are an AI")
    idx_task = result1.index("Generate a message")
    assert idx_sys < idx_task, "system_identity should come before task_instruction"
    print("  ✓ assemble_prompt produces deterministic, correctly-ordered output")


def test_valid_channels():
    """R5: VALID_CHANNELS contains exactly email and linkedin."""
    from backend.routers.drafts import VALID_CHANNELS

    assert VALID_CHANNELS == {
        "email",
        "linkedin",
    }, f"Unexpected channels: {VALID_CHANNELS}"
    print("  ✓ VALID_CHANNELS = {email, linkedin}")


def test_persona_anchor_exists():
    """Q2: PERSONA_ANCHOR is non-empty and mentions first person."""
    from backend.routers.drafts import PERSONA_ANCHOR

    assert len(PERSONA_ANCHOR) > 20, "PERSONA_ANCHOR is too short"
    assert (
        "first person" in PERSONA_ANCHOR.lower() or "you are" in PERSONA_ANCHOR.lower()
    ), "PERSONA_ANCHOR should mention first-person speaking"
    print("  ✓ PERSONA_ANCHOR exists and is properly configured")


def test_channel_tone_exists():
    """Q5: CHANNEL_TONE has entries for both channels."""
    from backend.routers.drafts import CHANNEL_TONE

    assert "linkedin" in CHANNEL_TONE, "Missing linkedin tone"
    assert "email" in CHANNEL_TONE, "Missing email tone"
    assert len(CHANNEL_TONE["linkedin"]) > 10, "LinkedIn tone is too short"
    assert len(CHANNEL_TONE["email"]) > 10, "Email tone is too short"
    print("  ✓ CHANNEL_TONE configured for both channels")


def test_validate_structure():
    """Q1: validate_structure enforces minimum paragraphs."""
    from backend.routers.drafts import validate_structure

    # Email needs 3+ paragraphs
    assert validate_structure("Hi\n\nBody here\n\nBest regards", "email")
    assert not validate_structure("Too short", "email")

    # LinkedIn needs 2+ paragraphs
    assert validate_structure("Hi there\n\nLet's connect", "linkedin")
    assert not validate_structure("Single line", "linkedin")
    print("  ✓ validate_structure enforces paragraph minimums")


def test_normalize_length():
    """Q4: normalize_length trims to channel limits."""
    from backend.routers.drafts import normalize_length

    # LinkedIn: 2500 char limit
    long_linkedin = "a " * 2000  # 4000 chars
    result = normalize_length(long_linkedin, "linkedin")
    assert len(result) <= 2500, f"LinkedIn result too long: {len(result)} chars"

    # Email: 150 word limit
    long_email = "word " * 200  # 200 words
    result = normalize_length(long_email, "email")
    word_count = len(result.split())
    assert word_count <= 153, f"Email result too long: {word_count} words"
    print("  ✓ normalize_length enforces channel limits")


def test_remove_hedging():
    """Q6: remove_hedging strips common hedging phrases."""
    from backend.routers.drafts import remove_hedging

    text = "I think this is a great opportunity. Perhaps we could connect."
    result = remove_hedging(text)
    assert "I think " not in result, "Failed to remove 'I think '"
    assert "Perhaps " not in result, "Failed to remove 'Perhaps '"
    print("  ✓ remove_hedging strips hedging phrases")


def test_skills_verifier():
    """Q3: verify_skills_grounding detects hallucinated skills."""
    from backend.services.verifier import verify_skills_grounding

    draft = "I have experience with Docker, Kubernetes, and Terraform."
    user_skills = ["Docker", "Kubernetes", "Linux", "Python"]

    result = verify_skills_grounding(draft, user_skills)
    assert (
        "Terraform" in result["hallucinated"]
    ), "Should detect Terraform as hallucinated"
    assert "Docker" in result["grounded"], "Should detect Docker as grounded"
    assert "Kubernetes" in result["grounded"], "Should detect Kubernetes as grounded"
    print("  ✓ verify_skills_grounding detects hallucinated skills correctly")


def test_linkedin_fallback_uses_cortex_skills():
    """LinkedIn fallback must follow Cortex skills instead of a fixed DevOps persona."""
    from backend.routers.drafts import generate_fallback_draft

    message = generate_fallback_draft(
        candidate={
            "name": "Priya Sharma",
            "title": "Technical Recruiter",
            "company": "Acme",
            "summary": "Hiring web developers for our product team.",
        },
        sender_intro="Siddharth from Portfolio",
        signal="web developer opportunity",
        intent="opportunity",
        contact_type="linkedin",
        skills=["Web Development", "React", "JavaScript"],
        desired_role="Web Developer",
    )

    assert "Web Development" in message
    assert "React" in message
    assert "JavaScript" in message
    assert "looking for Web Developer" in message
    assert "interested" in message.lower()

    forbidden = ["Kubernetes", "Terraform", "CI/CD", "SRE", "cloud ops"]
    for term in forbidden:
        assert term.lower() not in message.lower(), f"Unexpected DevOps term: {term}"


def test_prompt_contract_types():
    """D1: PromptSection and GenerationParams models exist and validate."""
    from backend.models.schemas import PromptSection, GenerationParams

    # PromptSection should require key fields
    section = PromptSection(
        system_identity="You are an AI",
        user_bio="Engineer",
        candidate_context="Recruiter at Google",
        structural_rules="Keep short",
        negative_constraints="No buzzwords",
        task_instruction="Generate message",
    )
    assert section.system_identity == "You are an AI"

    # GenerationParams should have defaults
    params = GenerationParams(variant_id="abc", score=85.0)
    assert params.model == "gemini-2.0-flash"
    assert params.temperature == 0.4
    print("  ✓ PromptSection and GenerationParams validate correctly")


if __name__ == "__main__":
    print("\n🧪 Prompt Contract Tests (T1)\n")

    tests = [
        test_prompt_section_order,
        test_assemble_prompt_order,
        test_valid_channels,
        test_persona_anchor_exists,
        test_channel_tone_exists,
        test_validate_structure,
        test_normalize_length,
        test_remove_hedging,
        test_skills_verifier,
        test_linkedin_fallback_uses_cortex_skills,
        test_prompt_contract_types,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")

    if failed > 0:
        sys.exit(1)
    else:
        print("🎉 All prompt contract tests passed!")
