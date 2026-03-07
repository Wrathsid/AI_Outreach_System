import sys
import os
from pathlib import Path

# Add project root to path so we can import backend.*
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.routers.drafts import generate_fingerprint
from backend.services.verifier import normalize_skill

def test_h4_normalize_skill():
    print("\n--- Testing H4: Synonym Normalization ---")
    cases = {
        "js": "javascript",
        "JS": "javascript",
        "ts": "typescript",
        "TypeScript": "typescript",
        "React.js": "react",
        "ReactJS": "react",
        "Node.js": "node.js",
        "NodeJS": "node.js",
        "Golang": "go"
    }
    for inp, expected in cases.items():
        got = normalize_skill(inp)
        assert got == expected, f"Failed: {inp} -> {got} (expected {expected})"
    
    print("✅ normalize_skill passed all cases.")

def test_h1_fingerprint():
    print("\n--- Testing H1: Deterministic Fingerprint ---")
    # Setup test data
    cid = 123
    ctype = "linkedin"
    skills = ["Python", "FastAPI", "React"]
    resume = "Candidate is a developer with Python and React skills."
    tone = "TONE: Casual"
    
    fp1 = generate_fingerprint(cid, ctype, skills, resume, tone)
    fp2 = generate_fingerprint(cid, ctype, skills, resume, tone)
    
    assert fp1 == fp2, "Fingerprint not deterministic!"
    print(f"✅ Fingerprint match: {fp1[:8]}...")
    
    # Change one input (skills order should effectively be same if logic sorts them, but let's change content)
    skills_diff = ["Python", "FastAPI"] # Removed React
    fp3 = generate_fingerprint(cid, ctype, skills_diff, resume, tone)
    assert fp1 != fp3, "Fingerprint collision on skill change!"
    print("✅ Fingerprint changed correctly on input diff.")

if __name__ == "__main__":
    try:
        test_h4_normalize_skill()
        test_h1_fingerprint()
        print("\n✅ All Unit Tests Passed!")
    except AssertionError as e:
        print(f"\n❌ Unit Test Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
