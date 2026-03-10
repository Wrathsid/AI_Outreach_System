import asyncio
from backend.services.crawler import Crawler

async def test_crawler_filter():
    crawler = Crawler()
    print("Starting e2e crawler test for 'DevOps Engineer'...")
    
    count = 0
    passed = 0
    
    async for result in crawler.crawl_stream("DevOps Engineer", limit=15, broad_mode=True):
        if result["type"] == "raw_result":
            count += 1
            data = result["data"]
            url = data.get("url", "")
            title = data.get("title", "")
            body = data.get("body", "")
            
            print(f"\nResult {count}: {title}")
            print(f"URL: {url}")
            print(f"Snippet: {body[:150]}...")
            passed += 1
            
        elif result["type"] == "status":
            print(f"Status: {result['data']}")
            
if __name__ == "__main__":
    asyncio.run(test_crawler_filter())
