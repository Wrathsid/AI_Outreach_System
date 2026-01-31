import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.scanner import search_leads

def test_scanner():
    print("🔎 Testing Scanner with query: 'DevOps Engineer'")
    results = search_leads("DevOps Engineer", limit=5)
    
    print(f"✅ Found {len(results)} results")
    for r in results:
        print(f"---")
        print(f"Name: {r['name']}")
        print(f"Email: {r['email']}")
        print(f"Company: {r['company']}")
        print(f"Source: {r['linkedin_url']}")

if __name__ == "__main__":
    test_scanner()
