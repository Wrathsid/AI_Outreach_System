from duckduckgo_search import DDGS
from googlesearch import search
import json

def test_ddg_html():
    print("\n--- Testing DDGS (backend='html') ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("python", backend="html", max_results=5))
            print(f"Got {len(results)} results.")
            if results:
                print(results[0])
    except Exception as e:
        print(f"DDGS Error: {e}")

def test_google():
    print("\n--- Testing Google Search ---")
    try:
        results = list(search("python", num_results=5, advanced=True))
        print(f"Got {len(results)} results.")
        if results:
            print(f"Title: {results[0].title}")
            print(f"Desc: {results[0].description}")
            print(f"URL: {results[0].url}")
    except Exception as e:
        print(f"Google Error: {e}")

if __name__ == "__main__":
    test_ddg_html()
    test_google()
