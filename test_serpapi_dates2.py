import os
from serpapi import GoogleSearch
from dotenv import load_dotenv
import json

load_dotenv()

def test_dates():
    api_key = os.getenv("SERPAPI_KEY")
    query = 'site:linkedin.com "we are hiring" "React Developer"'
    print(f"Query: {query}")
    params = {
        "q": query,
        "api_key": api_key,
        "num": 5,
        "engine": "google",
        "tbs": "qdr:w"  # Past week
    }
    
    search = GoogleSearch(params)
    data = search.get_dict()
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    test_dates()
