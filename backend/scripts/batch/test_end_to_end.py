
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def test_pipeline():
    print(f"[*] Starting End-to-End Test on {BASE_URL}")

    # 1. SEARCH
    role = "frontend developer"
    print(f"\n[1] Searching for '{role}'...")
    
    candidates_to_add = []
    
    try:
        # Hit the streaming endpoint
        with requests.get(f"{BASE_URL}/discover/hr-search", params={"role": role, "limit": 5}, stream=True) as r:
            print("[*] Streaming results...")
            count = 0
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if data['type'] == 'result':
                            candidate = data['data']
                            print(f"    - Found: {candidate.get('name')} | {candidate.get('title')} @ {candidate.get('company')}")
                            candidates_to_add.append(candidate)
                            count += 1
                            if count >= 3:
                                break
                    except Exception as e:
                        pass
    except Exception as e:
        print(f"[!] Search failed: {e}")
        return

    if not candidates_to_add:
        print("[!] No candidates found.")
        return

    # 2. ADD TO PIPELINE & 3. GENERATE DRAFTS
    print(f"\n[2] Adding {len(candidates_to_add)} candidates to pipeline & generating drafts...")

    for cand_data in candidates_to_add:
        # Add Candidate
        try:
            # Prepare payload (map fields if necessary, schemas.py CandidateCreate)
            payload = {
                "name": cand_data.get("name", "Unknown"),
                "title": cand_data.get("title"),
                "company": cand_data.get("company"),
                "email": cand_data.get("email"),
                "linkedin_url": cand_data.get("linkedin_profile"), # Note: check key map
                "summary": cand_data.get("summary", ""),
                "match_score": int(cand_data.get("score", 0) * 100)
            }
            
            res = requests.post(f"{BASE_URL}/candidates", json=payload)
            if res.status_code == 200:
                created_cand = res.json()
                cid = created_cand['id']
                print(f"\n    [+] Added Candidate: {created_cand['name']} (ID: {cid})")
                
                # Generate Draft
                print(f"    [*] Generating draft for {created_cand['name']}...")
                draft_res = requests.post(f"{BASE_URL}/drafts/generate/{cid}")
                
                if draft_res.status_code == 200:
                    draft = draft_res.json()
                    print(f"    [+] Draft Generated!")
                    print(f"    --- DRAFT CONTENT ({draft.get('intent', 'unknown')}) ---")
                    print(f"    Subject: {draft.get('subject')}")
                    print(f"    Body:\n{draft.get('body')}")
                    print(f"    -----------------------------------")
                else:
                    print(f"    [!] Draft generation failed: {draft_res.text}")

            else:
                print(f"    [!] Failed to add candidate: {res.text}")
                
        except Exception as e:
            print(f"    [!] Error processing candidate: {e}")

    print("\n[*] Test Complete.")

if __name__ == "__main__":
    test_pipeline()
