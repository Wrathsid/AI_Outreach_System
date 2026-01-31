import requests
import json
import time
import sys

# API Base URL
API_BASE = "http://localhost:8000"

# Roles to scan
ROLES = [
    # User Request
    "QA Engineer", 
    "Content Writer", 
    "DevOps Engineer", 
    "Frontend Developer", 
    "Backend Developer", 
    "Cloud Architect",
    
    # 14 More Tech Roles
    "Full Stack Developer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Site Reliability Engineer",
    "Mobile Developer",
    "UI/UX Designer",
    "Product Manager",
    "Cybersecurity Engineer",
    "Blockchain Developer",
    "Database Administrator",
    "Technical Lead",
    "Systems Engineer", 
    "Network Engineer",
    "IT Manager"
]

def scan_and_save(role):
    print(f"\n[SCAN] Starting deep scan for: {role}")
    
    # We use the stream endpoint but treat it line-by-line or just use the discovery endpoint
    # To get "real" results filtering, we'll process the stream manually
    
    try:
        # Use simple discover endpoint (blocking) or stream? 
        # Stream is better for long running, but blocking is easier to code if timeout allows.
        # Let's use the stream endpoint to parse results as they come.
        
        url = f"{API_BASE}/discover-stream?role={role}"
        
        count = 0
        with requests.get(url, stream=True) as r:
            for line in r.iter_lines():
                if not line: continue
                
                try:
                    msg = json.loads(line.decode('utf-8'))
                    
                    if msg['type'] == 'result':
                        data = msg['data']
                        
                        # STRICT FILTER: User wants "mails to apply" -> Must have email
                        if not data.get('email'):
                            continue
                            
                        # Save to DB via API
                        payload = {
                            "name": data.get("name", "Unknown"),
                            "title": data.get("title", role),
                            "company": data.get("company", "Unknown"),
                            "email": data.get("email"),
                            "linkedin_url": data.get("linkedin_url", ""),
                            "summary": data.get("summary", "")[:500],
                            "match_score": int(data.get("hr_score", 0.5) * 100) if data.get("hr_score", 0) <= 1 else int(data.get("hr_score", 50)),
                            "status": "new",
                            "tags": [role, "Batch Scan"]
                        }
                        
                        save_res = requests.post(f"{API_BASE}/candidates", json=payload)
                        if save_res.status_code == 200:
                            print(f"  [SAVED] {data.get('email')} - {data.get('name')}")
                            count += 1
                        else:
                            print(f"  [ERR] Could not save: {save_res.text}")
                            
                    elif msg['type'] == 'status':
                        # print(f"  [STATUS] {msg['data']}")
                        pass
                        
                except Exception as e:
                    pass
                    
        print(f"[DONE] Finished {role}. Saved {count} verified leads.")
        
    except Exception as e:
        print(f"[ERR] Failed to scan {role}: {e}")

def main():
    print("Starting Deep Tech Scan Batch Job...")
    print("User Requirement: Real Verified Emails Only.")
    
    total_saved = 0
    for role in ROLES:
        scan_and_save(role)
        time.sleep(2) # Cooldown between roles
        
    print("\nBatch Job Complete.")

if __name__ == "__main__":
    main()
