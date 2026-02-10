import requests
import json
import uuid
import sys

API_URL = "http://127.0.0.1:8000"

def verify_opportunity_intent():
    # 1. Create a Test Candidate (Recruiter)
    candidate_data = {
        "name": f"Test Recruiter {uuid.uuid4().hex[:6]}",
        "title": "Senior Technical Recruiter",
        "company": "Tech Corp",
        "linkedin_url": f"https://linkedin.com/in/recruiter-{uuid.uuid4().hex[:6]}",
        "summary": "Hiring for DevOps and SRE roles."
    }
    
    print(f"Creating candidate: {candidate_data['name']} ({candidate_data['title']})...")
    res = requests.post(f"{API_URL}/candidates", json=candidate_data)
    
    if res.status_code != 200:
        print(f"❌ Failed to create candidate: {res.text}")
        return
        
    candidate = res.json()
    candidate_id = candidate["id"]
    print(f"[OK] Candidate created with ID: {candidate_id}")
            
    try:
        # 2. Generate Draft
        print(f"Generating draft for candidate {candidate_id}...")
        # Force LinkedIn type to trigger the LinkedIn prompt logic
        res = requests.post(f"{API_URL}/drafts/generate/{candidate_id}?contact_type=linkedin")
        
        if res.status_code != 200:
            print(f"[FAIL] Draft generation failed: {res.text}")
            return
            
        draft_result = res.json()
        
        # 3. Verify Output
        print("\n--- GENERATED DRAFT ---")
        message = draft_result.get("message", "")
        print(message)
        print("-----------------------")
        
        # Key checks for Opportunity metrics
        checks = {
            "Greeting": "Hi" in message,
            "Direct Ask (hiring/profile/roles)": any(x in message.lower() for x in ["hiring", "open to reviewing", "relevant roles", "engineering needs", "open searches"]),
            "NO 'Open to connecting'": "open to connecting" not in message.lower(),
            "NO 'Hope this finds you well'": "hope this finds you well" not in message.lower()
        }
        
        print("\n--- VERIFICATION CHECKS ---")
        all_passed = True
        for check, passed in checks.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} {check}")
            if not passed: all_passed = False
            
        if all_passed:
            print("\n✅ Opportunity Generation Logic Verified (Direct Ask)!")
        else:
            print("\n⚠️ Some checks failed. Review output above.")
            sys.exit(1)

    finally:
        # 4. Cleanup (Delete Candidate)
        print(f"\nCleaning up candidate {candidate_id}...")
        requests.delete(f"{API_URL}/candidates/{candidate_id}")
        print("✅ Cleanup complete.")

if __name__ == "__main__":
    verify_opportunity_intent()
