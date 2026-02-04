from duckduckgo_search import DDGS
import json

def test_search():
    print("Testing DDGS simple search...")
    try:
        with DDGS() as ddgs:
            # excessive max_results to ensure we get something
            results = list(ddgs.text("python", max_results=5))
            
            print(f"Got {len(results)} results.")
            if results:
                print("First result keys:", results[0].keys())
                print(json.dumps(results[0], indent=2))
            else:
                print("No results found.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
