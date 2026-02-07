import requests
import sys
import json

BASE_URL = "http://localhost:8000"

def verify_dual_formats():
    print("STARTING Double Verification of Dual-Format System...")
    
    # 1. Fetch Candidates
    print("1. Fetching candidates...")
    try:
        res = requests.get(f"{BASE_URL}/candidates")
        candidates = res.json()
    except Exception as e:
        print(f"FAILED to fetch candidates: {e}")
        return

    # 2. Identify Test Cases
    email_cand = next((c for c in candidates if c.get('email')), None)
    gen_email_cand = next((c for c in candidates if not c.get('email') and c.get('generated_email')), None)
    linkedin_cand = next((c for c in candidates if not c.get('email') and not c.get('generated_email') and c.get('linkedin_url')), None)

    print(f"\nTEST CANDIDATES IDENTIFIED:")
    print(f"   - Verified Email: {email_cand['name']} (ID: {email_cand['id']}) - {email_cand.get('email')}" if email_cand else "   - Verified Email: NONE found")
    print(f"   - AI Generated Email: {gen_email_cand['name']} (ID: {gen_email_cand['id']}) - {gen_email_cand.get('generated_email')}" if gen_email_cand else "   - AI Generated Email: NONE found")
    print(f"   - LinkedIn Only: {linkedin_cand['name']} (ID: {linkedin_cand['id']})" if linkedin_cand else "   - LinkedIn Only: NONE found")

    # 3. Test Generation
    test_cases = [
        ("Verified Email", email_cand),
        ("AI Generated Email", gen_email_cand),
        ("LinkedIn Only", linkedin_cand)
    ]
    
    results = []

    print("\nRUNNING GENERATION TESTS...")
    print("-" * 60)
    print(f"{'Type':<20} | {'Result Type':<15} | {'Format Check':<20} | {'Status'}")
    print("-" * 60)

    for case_name, cand in test_cases:
        if not cand:
            print(f"{case_name:<20} | {'SKIPPED':<15} | {'Candidate not found':<20} | SKIP")
            continue

        try:
            # Call generation endpoint
            res = requests.post(f"{BASE_URL}/drafts/generate/{cand['id']}")
            if res.status_code != 200:
                print(f"{case_name:<20} | {'ERROR':<15} | {f'HTTP {res.status_code}':<20} | FAIL")
                continue
            
            data = res.json()
            draft_type = data.get('type')
            
            # Validation Logic
            is_valid = False
            details = ""
            
            if case_name in ["Verified Email", "AI Generated Email"]:
                if draft_type == 'email' and 'subject' in data and 'body' in data:
                    is_valid = True
                    details = "Has Subject + Body"
                else:
                    details = f"Wrong fmt: {draft_type}"
            else: # LinkedIn Only
                if draft_type == 'linkedin' and 'message' in data and 'char_count' in data:
                    is_valid = True
                    details = f"Msg len: {data['char_count']}"
                else:
                    details = f"Wrong fmt: {draft_type}"

            status_icon = "PASS" if is_valid else "FAIL"
            print(f"{case_name:<20} | {draft_type:<15} | {details:<20} | {status_icon}")
            
            results.append({
                "case": case_name,
                "type": draft_type,
                "details": details,
                "status": status_icon
            })

        except Exception as e:
            print(f"{case_name:<20} | {'ERROR':<15} | {str(e)[:20]:<20} | FAIL")
            results.append({
                "case": case_name,
                "status": "ERROR",
                "error": str(e)
            })

    print("-" * 60)
    print("\nVERIFICATION COMPLETE.")
    
    with open("verification_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    verify_dual_formats()
