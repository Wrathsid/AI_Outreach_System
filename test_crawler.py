import asyncio
from backend.services.crawler import Crawler

async def test():
    crawler = Crawler()
    print(f"SerpAPI Key present: {bool(crawler.serpapi_key)}")
    print("Testing Broad Mode Search for 'React Developer'...")
    
    async for result in crawler.crawl_stream("React Developer", limit=5, broad_mode=True):
        print(result)

if __name__ == "__main__":
    asyncio.run(test())
