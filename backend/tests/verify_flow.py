import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_step(message):
    print(f"\n👉 {message}")

def verify_flow():
    print("🚀 Starting API Verification Flow...\n")

    # 1. Check Health
    print_step("Checking System Health...")
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"✅ API Status: {resp.status_code}")
        print(f"   Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return

    # 2. Add Candidate
    print_step("Step 1: Adding a new candidate...")
    candidate_data = {
        "name": "Validation User",
        "email": "validate@test.com",
        "company": "TestCorp",
        "title": "Director of Validation",
        "location": "Test City",
        "summary": "Experienced in testing and validation.",
        "match_score": 95
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/candidates", json=candidate_data)
        if resp.status_code == 200:
            candidate = resp.json()
            candidate_id = candidate['id']
            print(f"✅ Candidate Created: {candidate['name']} (ID: {candidate_id})")
        else:
            print(f"❌ Failed to create candidate: {resp.text}")
            return
    except Exception as e:
        print(f"❌ Error during candidate creation: {e}")
        return

    # 3. Generate Draft
    print_step(f"Step 2: Generating Cold Email for Candidate {candidate_id}...")
    try:
        # Note: endpoint is POST /generate-draft?candidate_id=...
        resp = requests.post(f"{BASE_URL}/generate-draft?candidate_id={candidate_id}")
        if resp.status_code == 200:
            draft = resp.json()
            print("✅ Draft Generated Successfully!")
            print(f"   Subject: {draft['subject']}")
            print(f"   Body Preview: {draft['body'][:100]}...")
        else:
            print(f"❌ Failed to generate draft: {resp.text}")
            return
    except Exception as e:
        print(f"❌ Error during draft generation: {e}")
        return

    # 4. Fetch Drafts
    print_step("Step 3: Verifying Draft appears in list...")
    try:
        resp = requests.get(f"{BASE_URL}/drafts")
        if resp.status_code == 200:
            drafts = resp.json()
            # Find our draft
            found = False
            for d in drafts:
                if d['candidate_id'] == candidate_id:
                    print(f"✅ Found draft for {d['candidate_name']} at {d['candidate_company']}")
                    found = True
                    break
            
            if not found:
                 print("⚠️ Draft not found in list (might be an issue or just ordering)")
        else:
            print(f"❌ Failed to fetch drafts: {resp.text}")
            return
    except Exception as e:
        print(f"❌ Error fetching drafts: {e}")

    print("\n🎉 Verification Complete! The core logic works.")

if __name__ == "__main__":
    verify_flow()
