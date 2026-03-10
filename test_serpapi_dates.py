import os
from serpapi import GoogleSearch
from dotenv import load_dotenv
import json

load_dotenv()

def test_dates():
    api_key = os.getenv("SERPAPI_KEY")
    query = 'site:linkedin.com/posts "hiring React Developer"'
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
    organic = data.get("organic_results", [])
    
    print("\n--- RESULTS ---")
    for r in organic:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        link = r.get("link", "")
        date = r.get("date", "No date provided by Google")
        print(f"\nTitle: {title}")
        print(f"Date indexed by Google: {date}")
        print(f"Snippet: {snippet}")
        print(f"Link: {link}")

if __name__ == "__main__":
    test_dates()
