import requests
import json

API_URL = "http://localhost:8000"

def test_extraction():
    print("--- Testing AI Extraction ---")
    sample_text = "We are looking for a Junior DevOps Engineer for a 6 month internship. Remote. Please send your resume to careers@techstartup.io. Urgent requirement."
    
    try:
        res = requests.post(f"{API_URL}/extract-opportunity", json={"text": sample_text})
        if res.status_code == 200:
            data = res.json()
            print("[PASS] Extraction Successful")
            print(json.dumps(data, indent=2))
        else:
            print(f"[FAIL] Extraction Failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[FAIL] Connection Error: {e}")

def test_discovery():
    print("\n--- Testing Discovery Search ---")
    # We'll use the synchronous wrapper for simplicity in the test script, 
    # but the backend logic is shared.
    try:
        # Searching for a role that likely returns results but not too many to flood
        res = requests.get(f"{API_URL}/discover?role=DevOps Intern")
        if res.status_code == 200:
            data = res.json()
            print(f"[PASS] Discovery Successful. Found {len(data)} results.")
            # Print first 2 results to check structure
            for item in data[:2]:
                print(f"- {item.get('name')} | {item.get('title')} | Confident: {item.get('is_confident')}")
        else:
            print(f"[FAIL] Discovery Failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[FAIL] Connection Error: {e}")

if __name__ == "__main__":
    test_extraction()
    test_discovery()
