
import asyncio
import json
from services.discovery_orchestrator import DiscoveryOrchestrator

async def test_broad_mode():
    orchestrator = DiscoveryOrchestrator()
    print("--- Testing Broad Mode ---")
    count = 0
    # Use a generic role that should yield results easily in broad mode
    async for result in orchestrator.discover_leads_stream("Marketing Manager", limit=5, broad_mode=True):
        try:
            data = json.loads(result)
            if data['type'] == 'result':
                print(f"[Broad] Found: {data['data']['email']}")
                count += 1
            elif data['type'] == 'status':
                print(f"[Status] {data['data']}")
        except:
            pass
        if count >= 2:
            break
            
    if count > 0:
        print("✅ Broad Mode returned results.")
    else:
        print("❌ Broad Mode returned NO results (might be rate limited or blocked).")

    print("\n--- Testing Precision Mode ---")
    count = 0
    async for result in orchestrator.discover_leads_stream("Marketing Manager", limit=5, broad_mode=False):
        try:
            data = json.loads(result)
            if data['type'] == 'result':
                print(f"[Precision] Found: {data['data']['email']}")
                count += 1
            elif data['type'] == 'status':
                 print(f"[Status] {data['data']}")
        except:
            pass
        if count >= 1:
            break

if __name__ == "__main__":
    asyncio.run(test_broad_mode())
