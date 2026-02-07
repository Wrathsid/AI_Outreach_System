import requests
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, path, data=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {name}: {method} {url} ...", end=" ")
    try:
        if method == "GET":
            resp = requests.get(url, stream=True, timeout=5)
            # Read a bit to ensure it works
            content = next(resp.iter_content(100), b"").decode('utf-8')
        else:
            resp = requests.post(url, json=data, timeout=10)
            content = resp.text
            
        if resp.status_code in [200, 201]:
            print(f"OK ({resp.status_code})")
            return True
        else:
            print(f"FAIL ({resp.status_code})")
            print(f"  Response: {resp.text[:100]}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Verifying Refactored Endpoints...\n")
    
    results = []
    
    # Discovery
    results.append(test_endpoint("HR Search", "GET", "/discover/hr-search?role=Tester&limit=1"))
    results.append(test_endpoint("Crawl", "POST", "/discover/crawl", {"domain": "http://example.com"}))
    results.append(test_endpoint("Pattern", "POST", "/discover/pattern", {"first_name": "Test", "last_name": "User", "domain": "example.com"})) # Should return pattern or default
    
    # Drafts
    results.append(test_endpoint("Get Drafts", "GET", "/drafts"))
    # Note: Generate might need valid candidate ID, might fail with 404 or 500 if DB empty, but we check if endpoint is reachable
    # We'll skip complex POSTs that depend on DB state for this quick check, or handle 404 as 'reachability success'
    
    # Emails
    results.append(test_endpoint("Get Sent Emails", "GET", "/emails/sent"))
    
    # Stats
    results.append(test_endpoint("Get Activity", "GET", "/stats/activity"))
    results.append(test_endpoint("Get Stats", "GET", "/stats"))
    
    print("\n" + "="*30)
    if all(results):
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")

if __name__ == "__main__":
    main()
