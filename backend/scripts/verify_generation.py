import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def get_candidates():
    try:
        res = requests.get(f"{BASE_URL}/candidates")
        data = res.json()
        print(f"DEBUG: Candidates response type: {type(data)}")
        print(f"DEBUG: Candidates response: {data}")
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        return []

def generate_draft(candidate_id, type="auto"):
    print(f"\n--- Generating for ID {candidate_id} ({type}) ---")
    try:
        res = requests.post(f"{BASE_URL}/drafts/generate/{candidate_id}?contact_type={type}")
        if res.status_code == 200:
            data = res.json()
            print(f"Success! Type: {data.get('type')}")
            print(f"Score: {data.get('quality_score')}")
            print(f"Message: {data.get('message') or data.get('body')}")
            return True
        else:
            print(f"Failed: {res.text}")
            return False
    except Exception as e:
        print(f"Error generating: {e}")
        return False

if __name__ == "__main__":
    candidates = get_candidates()
    if candidates:
        print(f"Found {len(candidates)} candidates.")
        # Test with the first one
        c = candidates[0]
        generate_draft(c['id'], "linkedin")
        generate_draft(c['id'], "email")
    else:
        print("No candidates found or backend not running.")
