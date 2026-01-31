import sys
import os
import json
import time

# Add backend dir to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.scanner import search_leads_stream

def test_role(role_name):
    print(f"\n--- Testing HR Search for: {role_name} ---")
    # Using stream to see progress
    count = 0
    start_time = time.time()
    
    for line in search_leads_stream(role_name, limit=3):
        try:
            msg = json.loads(line)
            if msg['type'] == 'status':
                print(f"[STATUS] {msg['data']}")
            elif msg['type'] == 'result':
                res = msg['data']
                print(f"\n[FOUND] {res['name']} ({res.get('title', 'Unknown')})")
                print(f"    Email: {res.get('email', 'N/A')} | Is HR? {res.get('is_hr', False)}")
                count += 1
            elif msg['type'] == 'done':
                print(f"[DONE] {msg['data']}")
            elif msg['type'] == 'error':
                print(f"[ERROR] {msg['data']}")
                
        except Exception as e:
            print(f"Error parsing line: {e}")

        # Timeout safety (30s per role)
        if time.time() - start_time > 30:
            print("Timeout reached, moving to next.")
            break

def main():
    roles = ["DevOps", "Content Creator", "QA"]
    for r in roles:
        test_role(r)
        print("\n" + "="*50)

if __name__ == "__main__":
    main()
