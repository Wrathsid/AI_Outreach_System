from googlesearch import search
import json

def test_google():
    query = 'site:linkedin.com/posts "hiring React Developer"'
    print(f"Query: {query}")
    try:
        results = search(query, num_results=5, lang="en", advanced=True, tbs="qdr:w")
        for r in results:
            print(f"Title: {r.title}")
            print(f"URL: {r.url}")
            print(f"Snippet: {r.description}\n")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_google()
