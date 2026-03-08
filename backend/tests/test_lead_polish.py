import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

import pytest
from backend.services.lead_processor import polish_leads_activity

@pytest.mark.asyncio
async def test_polish():
    print("Testing AI Lead Polishing...")
    
    # Test case based on user screenshot
    messy_leads = [
        {
            "title": "The Rust hiring market in the US has changed. AI has made applying ...",
            "body": "The Rust hiring market in the US has changed. AI has made applying easier and filtering real engineers harder. Founders building Rust -first teams in San Francisco and New York are telling me the ...",
            "url": "https://www.linkedin.com/posts/jude-rushford-2695a9238_the-rust-hiring-market-in-the-us-has-changed-activity-7433076487995453440-Ed3Y"
        }
    ]
    
    results = await polish_leads_activity(messy_leads)
    
    for lead in results:
        print("-" * 30)
        print(f"URL: {lead.get('url')}")
        print(f"POLISHED NAME: {lead.get('name')}")
        print(f"POLISHED TITLE: {lead.get('title')}")
        print(f"POLISHED COMPANY: {lead.get('company')}")
        print(f"POLISHED SUMMARY: {lead.get('summary')}")
        print(f"IS HIRING POST: {lead.get('is_hiring_post')}")
        print("-" * 30)
        
        # Simple validations
        if lead.get('name') == "Jude Rushford":
            print("✅ SUCCESS: Name correctly extracted!")
        else:
            print(f"❌ FAIL: Expected Jude Rushford, got {lead.get('name')}")
            
        summary = lead.get('summary') or ""
        if "..." not in summary:
            print("✅ SUCCESS: Summary reconstructed without truncation!")
        else:
            print("❌ FAIL: Summary still contains truncation markers (...)")
            
        if lead.get('is_hiring_post') == True:
            print("✅ SUCCESS: Correctly identified as hiring post!")

if __name__ == "__main__":
    asyncio.run(test_polish())
