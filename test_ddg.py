from ddgs import DDGS
import json

print("Testing DuckDuckGo with time limit 'w'...")
try:
    results = list(DDGS().text('site:linkedin.com/posts "hiring React Developer"', max_results=5, timelimit="w"))
    print(json.dumps(results, indent=2))
except Exception as e:
    print("Error:", e)
