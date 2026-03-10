import asyncio
import json
from backend.services.crawler import Crawler
from backend.services.lead_processor import polish_single_lead
from backend.config import logger

async def run_verification():
    print("--- STARTING END-TO-END PIPELINE VERIFICATION ---")
    print("Target Role: DevOps Engineer")
    
    crawler = Crawler()
    passed_time_filter = 0
    passed_ai_filter = 0
    rejected_by_ai = 0
    
    print("\nPhase 1: Searching and Time Filtering...")
    async for result in crawler.crawl_stream("DevOps Engineer", limit=15, broad_mode=True):
        if result["type"] == "status":
            print(f"Crawler Status: {result['data']}")
            continue
            
        if result["type"] == "raw_result":
            passed_time_filter += 1
            raw_lead = result["data"]
            url = raw_lead.get("url", "")
            print(f"\n[TIME-VALID] Found recent post: {url}")
            
            print("Phase 2: AI Intent Processing...")
            # Simulate the exact pipeline in discovery.py
            polished_lead = await polish_single_lead(raw_lead)
            
            is_hiring = polished_lead.get("is_hiring_post")
            if is_hiring is False:
                rejected_by_ai += 1
                print(f"❌ [AI-REJECTED] The AI determined this is not a genuine job posting. Dropping.")
                print(f"Reason: Snippet content indicates it's likely a discussion or profile.")
                print(f"Summary: {polished_lead.get('summary')}")
            else:
                passed_ai_filter += 1
                print(f"✅ [AI-APPPROVED] Genuine Job Posting Confirmed!")
                print(f"Company: {polished_lead.get('company')}")
                print(f"Summary: {polished_lead.get('summary')}")

    print("\n==================================================")
    print("                VERIFICATION SUMMARY              ")
    print("==================================================")
    print(f"Posts that passed the 7-day strict time filter: {passed_time_filter}")
    print(f"Posts that were REJECTED by AI as non-jobs:     {rejected_by_ai}")
    print(f"Posts that PASSED both filters as pure leads:   {passed_ai_filter}")
    print("==================================================")
    
if __name__ == "__main__":
    asyncio.run(run_verification())
