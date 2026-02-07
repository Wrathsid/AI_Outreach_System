
import requests
import json
import sys
import time

# Constants
BASE_URL = "http://localhost:8000"
CANDIDATE_ID = 1

def test_generate_draft():
    print(f"Testing generate_draft for candidate {CANDIDATE_ID}...")
    
    url = f"{BASE_URL}/drafts/generate/{CANDIDATE_ID}"
    
    # 1. Test LinkedIn Generation
    print("\n--- Testing LinkedIn Generation (auto-detected) ---")
    try:
        response = requests.post(url)
        if response.status_code == 200:
            draft = response.json()
            print("Success!")
            print(f"Draft ID: {draft.get('draft_id')}")
            print(f"Type: {draft.get('type')}")
            print(f"Score: {draft.get('quality_score')}")
            # Check Time to Read (Optimization 16)
            ttr = draft.get('time_to_read')
            print(f"Time to Read: {ttr}s")
            
            msg = draft.get('message', draft.get('body'))
            print(f"Message Preview: {msg[:100]}...")
            
            if ttr is None:
                print("FAIL: Time to read missing!")
            elif ttr > 60:
                print("WARNING: Time to read > 60s")
            
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Email Generation (Explicit)
    print("\n--- Testing Email Generation (Explicit) ---")
    try:
        response = requests.post(url, params={"contact_type": "email"})
        if response.status_code == 200:
            draft = response.json()
            print("Success!")
            print(f"Draft ID: {draft.get('draft_id')}")
            print(f"Type: {draft.get('type')}")
            print(f"Score: {draft.get('quality_score')}")
            ttr = draft.get('time_to_read')
            print(f"Time to Read: {ttr}s")
             
            msg = draft.get('body', "")
            print(f"Body Preview: {msg[:100]}...")
            
            if ttr is None:
                print("FAIL: Time to read missing!")
            
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_generate_draft()
