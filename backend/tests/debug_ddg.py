from ddgs import DDGS
import json


def test():
    queries = [
        'site:linkedin.com/in "Technical Recruiter" DevOps',
        'site:linkedin.com "Technical Recruiter" hiring DevOps',
        "DevOps recruiter email gmail.com",
    ]
    for q in queries:
        print(f"\nQuerying: {q}")
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(q, max_results=2)]
            print(json.dumps(results, indent=2))


if __name__ == "__main__":
    test()
