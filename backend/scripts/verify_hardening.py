import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def get_first_candidate():
    try:
        res = requests.get(f"{BASE_URL}/candidates")
        if res.status_code == 200:
            candidates = res.json()
            if getattr(candidates, 'get', None): # Handle dict response wrapper if any
                candidates = candidates.get('items', []) or candidates
            if isinstance(candidates, list) and len(candidates) > 0:
                print(f"Found candidate: {candidates[0]['name']} (ID: {candidates[0]['id']})")
                return candidates[0]
        print("No candidates found.")
        return None
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        return None

def verify_draft_hardening(draft):
    print("\n--- Verifying Hardening Fields (H1-H6) ---")
    gen_params = draft.get('generation_params', {})
    if not gen_params:
        print("❌ generation_params MISSING in draft response")
        return False

    all_passed = True
    
    # H1: Fingerprint
    fp = gen_params.get('fingerprint')
    if fp:
        print(f"✅ H1: Fingerprint present: {fp[:10]}...")
    else:
        print("❌ H1: Fingerprint MISSING")
        all_passed = False

    # H2: Prompt Version
    ver = gen_params.get('prompt_version')
    if ver:
        print(f"✅ H2: Prompt Version present: {ver}")
    else:
        print("❌ H2: Prompt Version MISSING")
        all_passed = False

    # H5: Reason Code
    reason = gen_params.get('reason')
    if reason:
        print(f"✅ H5: Reason Code present: {reason}")
    else:
        print("❌ H5: Reason Code MISSING")
        all_passed = False

    # H6: Skill Count
    sc = gen_params.get('skill_count')
    if sc is not None:
        print(f"✅ H6: Skill Count present: {sc}")
    else:
        print("❌ H6: Skill Count MISSING")
        all_passed = False

    return all_passed

def generate_draft(candidate_id):
    print(f"\nGeneratng draft for candidate {candidate_id}...")
    try:
        # First call - should be FRESH or IDEMPOTENT
        res = requests.post(f"{BASE_URL}/drafts/generate/{candidate_id}?contact_type=linkedin")
        if res.status_code != 200:
            print(f"❌ API Error: {res.status_code} - {res.text}")
            return
        
        draft = res.json()
        if verify_draft_hardening(draft):
            print("\n✅ All Hardening Checks Passed for Request 1")
        else:
            print("\n❌ Some Hardening Checks Failed for Request 1")

        # Second call - should be IDEMPOTENT (H1/R1 check)
        print("\nSending Duplicate Request (Testing Idempotency)...")
        res2 = requests.post(f"{BASE_URL}/drafts/generate/{candidate_id}?contact_type=linkedin")
        if res2.status_code == 200:
            draft2 = res2.json()
            reason2 = draft2.get('generation_params', {}).get('reason')
            print(f"Response 2 Reason: {reason2}")
            if reason2 == "IDEMPOTENT_RETURN":
                 print("✅ Idempotency Working (Received IDEMPOTENT_RETURN)")
            else:
                 print(f"⚠️ Warning: Expected IDEMPOTENT_RETURN, got {reason2}")
        
    except Exception as e:
        print(f"❌ Execution Error: {e}")

if __name__ == "__main__":
    c = get_first_candidate()
    if c:
        generate_draft(c['id'])
    else:
        print("Skipping test - no candidate available.")
