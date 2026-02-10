import asyncio
import sys
import os
from dotenv import load_dotenv

# Setup path
sys.path.append(os.getcwd())
load_dotenv()

from backend.config import get_supabase
from backend.routers.drafts import generate_draft

async def verify_templates():
    supabase = get_supabase()
    if not supabase:
        print("Failed to connect to Supabase")
        return

    # 1. Create Dummy Company Candidate
    print("\n--- Creating Dummy Company Candidate ---")
    company_candidate = {
        "name": "Hiring Team",
        "company": "Expansia",
        "title": "DevOps Account Management Sustainment Engineer",
        "status": "new",
        "email": "hiring@expansia.com"
    }
    res_company = supabase.table("candidates").insert(company_candidate).execute()
    company_id = res_company.data[0]["id"]
    print(f"Created Company Candidate ID: {company_id}")

    # 2. Create Dummy Recruiter Candidate
    print("\n--- Creating Dummy Recruiter Candidate ---")
    recruiter_candidate = {
        "name": "John Doe",
        "company": "Expansia",
        "title": "Technical Recruiter",
        "status": "new",
        "email": "john@expansia.com"
    }
    res_recruiter = supabase.table("candidates").insert(recruiter_candidate).execute()
    recruiter_id = res_recruiter.data[0]["id"]
    print(f"Created Recruiter Candidate ID: {recruiter_id}")

    # 3. Generate Draft for Company
    print("\n--- Generating Draft for COMPANY ---")
    draft_company = await generate_draft(company_id, contact_type="linkedin")
    print(f"COMPANY DRAFT:\n{draft_company['message']}")

    # 4. Generate Draft for Recruiter
    print("\n--- Generating Draft for RECRUITER ---")
    draft_recruiter = await generate_draft(recruiter_id, contact_type="linkedin")
    print(f"RECRUITER DRAFT:\n{draft_recruiter['message']}")

    # Write results to file
    with open("verification_output.txt", "w", encoding="utf-8") as f:
        f.write("--- COMPANY DRAFT ---\n")
        f.write(draft_company['message'])
        f.write("\n\n--- RECRUITER DRAFT ---\n")
        f.write(draft_recruiter['message'])
    
    print("Drafts written to verification_output.txt")

    # Cleanup
    print("\n--- Cleanup ---")
    supabase.table("candidates").delete().eq("id", company_id).execute()
    supabase.table("candidates").delete().eq("id", recruiter_id).execute()
    print("Deleted dummy candidates.")

if __name__ == "__main__":
    asyncio.run(verify_templates())
