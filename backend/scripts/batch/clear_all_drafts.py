
import requests
import sys

def clear_drafts_api():
    url = "http://localhost:8000/drafts"
    try:
        print(f"[*] Sending DELETE request to {url}...")
        response = requests.delete(url)
        
        if response.status_code == 200:
            print(f"[+] Success: {response.json()}")
        else:
            print(f"[!] Failed: Status {response.status_code}")
            print(f"[!] Response: {response.text}")
            
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    clear_drafts_api()
