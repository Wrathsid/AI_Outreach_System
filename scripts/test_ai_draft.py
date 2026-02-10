import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Mock Logic to replicate backend/routers/drafts.py behavior
from backend.services.hr_extractor import classify_entity
from backend.config import generate_with_gemini
from backend.models.schemas import Candidate

# ---------------------------------------------------------
# COPY OF PROMPT LOGIC FROM backend/routers/drafts.py
# ---------------------------------------------------------
async def simulate_draft_generation(c: Candidate, contact_type: str):
    # 1. User Context (Hardcoded as per backend)
    user_bio = """
    Name: Siddharth Chavan
    Role: DevOps-focused engineer
    Key Skills: Cloud operations, Linux systems, automation, sustaining production environments.
    Value Prop: I enjoy working close to infrastructure and ensuring systems remain stable, secure, and scalable.
    Current Status: Applying skills through hands-on projects, upskilling in DevOps/Cloud.
    """

    # 2. Determine Role Context
    is_company_recipient = False
    if c.company and c.name and c.company.lower() in c.name.lower():
            is_company_recipient = True
    
    if c.name == "Hiring Team":
        is_company_recipient = True

    if is_company_recipient:
            # TEMPLATE 1: Company Page DM
            role_context = c.title if c.title else 'DevOps / SRE Role'
            task_instruction = "Generate Message 1: Company Page DM (120-160 words). Exploratory, context-aware, slightly descriptive."
    else:
            # TEMPLATE 2: Recruiter DM
            role_context = "DevOps / Site Reliability Engineer"
            if c.title and "recruiter" not in c.title.lower() and "talent" not in c.title.lower():
                role_context = c.title
            
            task_instruction = "Generate Message 2: Recruiter DM (100-120 words). Direct, respectful, and concise."

    # 3. MASTER PROMPT
    prompt = f"""
    🔹 MASTER PROMPT (DYNAMIC PERSONA VERSION)
    
    You are an AI outreach assistant that generates human-sounding, high-conversion LinkedIn messages for job applications.
    
    INPUT CONTEXT:
    1. CANDIDATE (SENDER) RESUME SUMMARY:
    {user_bio}
    
    2. TARGET JOB / RECIPIENT CONTEXT:
    - Recipient: {c.name} ({c.title})
    - Company: {c.company}
    - Target Role / Context: {role_context}
    
    TASK: {task_instruction}
    
    CONTENT RULES:
    - Always mention the exact job title: "{role_context}"
    - Emphasize:
        1. Hands-on experience where skills overlap
        2. Learning mindset where skills are adjacent
        3. Interest in infrastructure, reliability, operations, or scale
    - End with a soft CTA (resume / connect / brief discussion)
    
    THINKING RULES (CRITICAL):
    - Analyze the implied job requirements for "{role_context}".
    - Analyze the sender's skills (Cloud, Linux, Automation, Stability).
    - Identify 2–4 overlapping or adjacent skills.
    - Only reference skills that actually exist in the sender's bio.
    
    STYLE RULES:
    - Sound like a real human engineer, not a template.
    - Slightly conversational, confident, and respectful.
    - Avoid buzzwords and exaggerated claims.
    - Do NOT sound desperate or overly polished.
    - No emojis.
    - No corporate marketing language.
    
    HARD CONSTRAINTS:
    - Do NOT invent experience.
    - Do NOT repeat resume bullet points.
    - Do NOT copy sample phrasing verbatim—adapt it.
    - Each message must feel written specifically for THIS role.
    """
    
    print(f"\\n[Generating for {c.name} ({contact_type})]")
    print(f"Prompt Length: {len(prompt)} chars")
    
    # 4. Generate
    response = await generate_with_gemini(prompt, temperature=0.4)
    return response

# ---------------------------------------------------------
# TEST CASES
# ---------------------------------------------------------

async def run_tests():
    # Mock Candidate (Data we expect after the fix)
    mock_candidate = Candidate(
        id=999,
        name="Masha Savelieva",
        title="Web Developer",
        company="Dropbox",
        linkedin_url="https://linkedin.com/in/mashasavelieva",
        summary="Experienced Web Developer with a focus on React and Node.js. Looking for reliability engineers.",
        status="new"
    )

    # 1. Test "Company Page" Scenario
    print("\\n\\n[SCENARIO 1: Message to Company/Hiring Manager]")
    draft_1 = await simulate_draft_generation(mock_candidate, "linkedin")
    print("-" * 20)
    print(draft_1)
    print("-" * 20)

    # 2. Test "Recruiter" Scenario
    mock_recruiter = Candidate(
        id=999,
        name="Jane Smith",
        title="Technical Recruiter",
        company="Amazon",
        linkedin_url="https://linkedin.com/in/janesmith",
        summary="Technical Recruiter at Amazon. Hiring for SREs and DevOps.",
        status="new"
    )

    print("\\n\\n[SCENARIO 2: Message to Recruiter]")
    draft_2 = await simulate_draft_generation(mock_recruiter, "linkedin")
    print("-" * 20)
    print(draft_2)
    print("-" * 20)

if __name__ == "__main__":
    asyncio.run(run_tests())

