import asyncio
from services.crawler import Crawler

async def test():
    c = Crawler()
    print("Starting crawler test for 'Frontend Developer'...")
    async for result in c.crawl_stream("Frontend Developer", limit=5, broad_mode=False):
        print(f"TYPE: {result['type']}")
        if result['type'] == 'raw_result':
            print(f"  [FOUND] {result['data']['title']}")
            print(f"  [URL] {result['data']['url']}")
        elif result['type'] == 'status':
            print(f"  [STATUS] {result['data']}")

if __name__ == "__main__":
    asyncio.run(test())
