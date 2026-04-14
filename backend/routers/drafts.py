"""
Drafts router - Draft management and AI generation.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any, List, Dict, Optional
from pydantic import BaseModel
import hashlib
import uuid
from datetime import datetime, timedelta
import asyncio


from backend.config import (
    get_supabase,
    logger,
)
from backend.models.schemas import (
    Draft,
    DraftCreate,
    DraftEditCreate,
    IntentType,
    GenerationReason,
    DraftGenerateResponse,
    BatchStatusResponse,
)
from backend.services.verifier import verify_skills_grounding

# ============================================================
# IMPORTS FROM EXTRACTED MODULES (backward-compatible re-exports)
# ============================================================
from backend.services.scoring import (  # noqa: F401
    score_draft,
    score_ending,
    calculate_softness_score,
    check_calm_consistency,
    check_mobile_readability,
    calculate_asymmetry_score,
    calculate_time_to_read,
)
from backend.services.signals import (  # noqa: F401
    clean_candidate_data,
    sanitize_scraped_content,
    validate_structure,
    normalize_length,
    remove_hedging,
    _detect_hiring_context,
    extract_primary_signal,
)
from backend.services.generation import (  # noqa: F401
    get_cached_brain_context,
    get_recent_opener_hashes,
    get_semantically_similar_openers,
    get_recent_openers,
    get_biased_parameters,
    generate_with_scoring,
)

router = APIRouter(tags=["Drafts"])


class BatchDraftRequest(BaseModel):
    contact_type: str = "auto"
    candidate_ids: List[int]
    context: Optional[str] = None


# ============================================================
# R5: VALID CHANNELS
# ============================================================
VALID_CHANNELS = {"email", "linkedin"}


# ============================================================
# Q5: CHANNEL TONE LOCK
# ============================================================
CHANNEL_TONE = {
    "linkedin": "TONE: This is LinkedIn job-seeking outreach. Be professional, direct, and clear that the applicant is interested and looking for an opportunity. Aim for 130-220 words. Do not invent skills that are absent from Cortex.",
    "email": "TONE: This is a direct, professional cold email for a job application or inquiry. Be concise, respectful of their time, and clear about your value proposition. Aim for ~150 words.",
}

# ============================================================
# H2: PROMPT VERSIONING
# ============================================================
PROMPT_VERSION = "v1.7"




# ============================================================
# H1: DETERMINISTIC FINGERPRINT
# ============================================================
def generate_fingerprint(
    candidate_id: int,
    contact_type: str,
    skills: list,
    resume_text: str,
    tone_directive: str,
) -> str:
    """Generate a deterministic hash of all inputs affecting generation."""
    skills_str = "|".join(sorted([s.lower() for s in skills]))
    resume_hash = hashlib.sha256((resume_text or "").encode()).hexdigest()[:8]
    tone_hash = hashlib.sha256((tone_directive or "").encode()).hexdigest()[:8]

    raw = f"{candidate_id}|{contact_type}|{skills_str}|{resume_hash}|{PROMPT_VERSION}|{tone_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()





# ============================================================
# R3: DETERMINISTIC PROMPT ASSEMBLY
# ============================================================
PROMPT_SECTION_ORDER = [
    "system_identity",
    "user_bio",
    "candidate_context",
    "signal",
    "memory_constraint",
    "skills_grounding",
    "structural_rules",
    "negative_constraints",
    "task_instruction",
]


def assemble_prompt(sections: dict) -> str:
    """Assemble prompt in a fixed, deterministic order (R3)."""
    parts = []
    for key in PROMPT_SECTION_ORDER:
        if key in sections and sections[key]:
            parts.append(sections[key].strip())
    return "\n\n---\n\n".join(parts)


# ============================================================
# Q2: PERSONA ANCHOR
# ============================================================
PERSONA_ANCHOR = """
PERSONA: You are the applicant described in the context below, actively looking for job opportunities.
You speak as yourself — first person, direct, professional but approachable.
You are a JOB APPLICANT. Every message you write is a job application or inquiry about open positions.
You never write generic networking messages or "looking to connect" messages.
You never introduce yourself in third person.
You never say "the candidate" when referring to yourself.
"""




def _format_skill_phrase(skills: Optional[List[str]], max_items: int = 4) -> str:
    """Turn Cortex skills into a short human phrase for templates."""
    clean_skills = [s.strip() for s in (skills or []) if s and s.strip()]
    if not clean_skills:
        return "software development and problem solving"
    visible = clean_skills[:max_items]
    if len(visible) == 1:
        return visible[0]
    return ", ".join(visible[:-1]) + f", and {visible[-1]}"


def _group_skills_for_prompt(skills_list: List[str]) -> str:
    """Group raw skills into domain buckets so the AI references categories, not a laundry list.

    RULE: The generated message must mention skill DOMAINS (e.g. 'frontend development'),
    NOT individual tools (e.g. 'React, Next.js, Vue.js, Angular, Vite, WebGL...').
    """
    frontend_kw = {"react", "next", "nextjs", "vue", "angular", "svelte", "html", "css",
                   "tailwind", "framer", "webgl", "vite", "webpack", "typescript", "javascript",
                   "web components", "sass", "scss", "figma", "three.js", "gsap"}
    backend_kw = {"node", "express", "fastapi", "django", "flask", "spring", "rails",
                  "graphql", "rest", "api", "postgres", "mysql", "mongodb", "redis", "prisma"}
    cloud_kw = {"aws", "gcp", "azure", "cloud", "docker", "kubernetes", "k8s", "terraform",
                "ansible", "ci/cd", "devops", "sre", "linux", "nginx", "serverless", "lambda"}
    ai_kw = {"ml", "ai", "llm", "machine learning", "deep learning", "pytorch", "tensorflow",
             "langchain", "openai", "nlp", "computer vision", "data science"}
    mobile_kw = {"flutter", "react native", "swift", "kotlin", "android", "ios"}

    buckets: dict = {"Frontend": [], "Backend": [], "Cloud/DevOps": [], "AI/ML": [], "Mobile": [], "Other": []}

    for skill in skills_list:
        sl = skill.strip().lower()
        if any(k in sl for k in frontend_kw):
            buckets["Frontend"].append(skill.strip())
        elif any(k in sl for k in backend_kw):
            buckets["Backend"].append(skill.strip())
        elif any(k in sl for k in cloud_kw):
            buckets["Cloud/DevOps"].append(skill.strip())
        elif any(k in sl for k in ai_kw):
            buckets["AI/ML"].append(skill.strip())
        elif any(k in sl for k in mobile_kw):
            buckets["Mobile"].append(skill.strip())
        else:
            buckets["Other"].append(skill.strip())

    lines = []
    for domain, items in buckets.items():
        if items:
            # Show max 2 representative tools + "and more" to avoid laundry lists
            sample = items[:2]
            sample_str = " and ".join(sample)
            extra = len(items) - 2
            if extra > 0:
                lines.append(f"- {domain}: {sample_str} (and {extra} more tools)")
            else:
                lines.append(f"- {domain}: {sample_str}")
    return "\n".join(lines) if lines else "- General: Software Development"


def generate_fallback_draft(
    candidate: dict,
    sender_intro: str,
    signal: str,
    intent: str,
    contact_type: str,
    skills: Optional[List[str]] = None,
    desired_role: Optional[str] = None,
) -> str:
    """Generate a template-based draft when AI fails (Resilience).

    IMPORTANT: All templates must produce human-quality output even with
    minimal/missing data. Never output 'Unknown' or hashtags.
    Context-aware: detects hiring posts and generates appropriate templates.
    """
    import random

    # Clean inputs — never let garbage through
    raw_name = candidate.get("name") or ""
    first_name = (
        raw_name.split()[0] if raw_name and not raw_name.startswith("#") else None
    )
    company = candidate.get("company") or None
    title = candidate.get("title") or None
    candidate.get("summary") or ""
    sender_first = sender_intro.split()[0] if sender_intro else "Siddharth"
    skill_phrase = _format_skill_phrase(skills)
    target_role = desired_role or "roles that match my background"

    # Determine what info we actually have
    has_name = first_name is not None and first_name.lower() not in ("unknown", "n/a")
    has_company = company is not None and company.lower() not in ("unknown", "n/a")
    has_title = title is not None and title.lower() not in ("unknown", "n/a")

    # DETECT HIRING CONTEXT from candidate data
    hiring_ctx = _detect_hiring_context(candidate)
    is_hiring_post = hiring_ctx["is_hiring_post"]
    hiring_role = hiring_ctx.get("hiring_role") or title

    # Build greeting (skip 'Hr' or 'Hiring' as first names)
    if has_name and first_name and first_name.lower() not in ("hiring", "hr", "team"):
        greeting = f"Hi {first_name}"
    else:
        greeting = "Hi there"

    # ============ LINKEDIN TEMPLATES (with data-quality awareness) ============
    if contact_type == "linkedin":
        role_label = hiring_role or title or target_role
        company_label = company if has_company else "your team"

        if is_hiring_post:
            return (
                f"{greeting}, I saw your post about the {role_label} opportunity at {company_label}. "
                f"I am interested in this role and actively looking for an opportunity where I can contribute with {skill_phrase}.\n\n"
                f"My background is focused on {skill_phrase}, and I would like to be considered if my profile matches what your team needs. "
                f"Could I share my resume or apply for the {role_label} position?"
            )

        if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
            if has_company:
                opening = (
                    f"{greeting}, I came across your profile at {company}. "
                    f"I am actively looking for {target_role} opportunities and wanted to reach out directly."
                )
            elif has_title:
                opening = (
                    f"{greeting}, I came across your profile as {title}. "
                    f"I am actively looking for {target_role} opportunities and wanted to reach out."
                )
            else:
                opening = (
                    f"{greeting}, I came across your profile while searching for {target_role} opportunities. "
                    "I wanted to reach out directly."
                )

            return (
                f"{opening}\n\n"
                f"My current focus is {skill_phrase}. I am interested in joining a team where I can apply these skills, "
                f"keep learning, and contribute to real product work.\n\n"
                "Are there any relevant openings on your team right now, or could I share my resume for future opportunities?"
            )

        # HIRING POST TEMPLATES — these take priority over all other branches
        if is_hiring_post and has_title:
            role_label = hiring_role or title
            company_label = company if has_company else "your team"
            options = [
                f"{greeting}, I noticed your post about hiring for a {role_label} position. I am an experienced professional with a strong background in my field, and I am very interested in this opportunity.\n\nThroughout my career, I have focused on building scalable and resilient systems. I have extensive experience with Infrastructure as Code using Terraform, container orchestration with Kubernetes, and implementing comprehensive CI/CD pipelines that allow teams to ship code faster without compromising stability. I treat every deployment as a software engineering problem, ensuring everything is version-controlled, tested, and repeatable.\n\nI believe my skills in cloud architecture, Linux systems, and automation align well with what {company_label} is looking for. I would love the opportunity to discuss how my background can contribute to the goals of this role. Would you be open to reviewing my profile or scheduling a brief call?",
                f"{greeting}, came across your post about the {role_label} opening at {company_label}. I wanted to reach out directly to express my interest and share a bit about my relevant background.\n\nI am deeply passionate about automation, efficiency, and delivering high quality results. My experience spans managing complex cloud environments on AWS and GCP, designing zero-downtime deployment strategies, and building observability stacks with Prometheus and Grafana. I am a firm believer in the SRE philosophy of treating operations as a software challenge.\n\nThe {role_label} role you posted about resonates strongly with my career trajectory. I am confident that my hands-on experience with industry best practices and modern architectures can add real value to your engineering team. Would you be available for a quick conversation about this opportunity, or would it be best if I sent over my resume?",
                f"{greeting}, saw that {company_label} is looking for a {role_label}. I am actively looking for my next opportunity in my field, and this position seems like a great match for my skill set.\n\nOver the past several years, I have built deep expertise in designing and maintaining highly available systems. I excel at driving process improvements, managing workflows at scale, and implementing security best practices across the entire deployment pipeline. I am driven by the challenge of turning complex manual processes into elegant, automated workflows.\n\nI am very enthusiastic about this opportunity and would welcome the chance to discuss how my experience aligns with the requirements. Could we connect to talk further, or would you prefer I share my resume directly?",
            ]
            return random.choice(options)

        # BEST: Have name + company/title
        if has_name and has_company:
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                # OPPORTUNITY TEMPLATES (Direct Hiring Ask)
                options = [
                    f"{greeting}, noticed you're recruiting at {company}. I am reaching out because I am an experienced professional with a very strong background in solving complex technical problems.\n\nThroughout my career, I have consistently focused on building scalable, resilient systems that can handle high traffic while minimizing downtime. I am deeply passionate about automating repetitive tasks using tools like Terraform, Ansible, and Kubernetes, ensuring that deployments are seamless and environments are consistent from development to production.\n\nI noticed that {company} is pushing the boundaries in your industry, and I would love to bring my expertise in Linux systems and CI/CD pipelines to your engineering team. Are you currently open to reviewing my profile for any relevant roles? I'd love to connect and see if there is a mutual fit.",
                    f"{greeting}, saw {company} is hiring. I specialize in driving reliability and best practices, and I am reaching out to explore potential synergies between my skillset and your engineering needs.\n\nMy approach to infrastructure is heavily rooted in Infrastructure as Code (IaC) principles. I believe that every aspect of the deployment lifecycle should be version-controlled, testable, and automated. I have extensive experience managing AWS environments, orchestrating containerized applications, and setting up robust monitoring and alerting systems to catch issues before they impact users.\n\nAs {company} continues to scale, having reliable backend operations is critical. I'd love to discuss how my background in SRE can help your team achieve its goals. Would you be open to a brief chat about your engineering needs or connecting so I can share my resume?",
                    f"{greeting}, verified your role at {company}. I'm actively looking for new opportunities and wanted to share a bit about my technical philosophy and background.\n\nI have spent years honing my skills in cloud architecture, focusing on creating systems that are not just functional, but highly optimized and secure. I thrive in environments where infrastructure is treated like software, utilizing robust CI/CD pipelines to accelerate development cycles without sacrificing stability. Whether it's managing complex Linux clusters or optimizing Database performance, I am driven by the challenge of solving hard infrastructure problems.\n\nI admire the technical work happening at {company} and would be thrilled to contribute my expertise. Are you hiring for any roles that match this profile, or open to reviewing my background for future opportunities? Worth a quick look?",
                ]
            else:
                # STANDARD CONNECTION TEMPLATES
                options = [
                    f"{greeting}, saw your profile at {company}. I work in the tech space, and I'm always looking to connect with other professionals who share a passion for scalable systems.\n\nMy work typically revolves around automating server provisioning, managing Kubernetes clusters, and ensuring that our applications have five-nines of reliability. It requires a constant balance between pushing new features quickly and maintaining iron-clad stability, something I'm sure you appreciate in your role.\n\nI'm looking to expand my network with people who understand the complexities of modern software delivery. Would love to connect and exchange notes on how our respective teams handle infrastructure challenges.",
                    f"{greeting}, noticed you're at {company}. I'm exploring opportunities in {signal} and your background caught my eye. I am a professional heavily focused on building efficient lifecycles.\n\nI believe that the best engineering teams are built on a foundation of strong automation and clear observability. My day-to-day involves writing Terraform scripts, designing resilient AWS architectures, and troubleshooting complex systemic issues across distributed microservices. It's a challenging field, but incredibly rewarding when everything runs smoothly.\n\nI am always eager to learn how different organizations, particularly innovative ones like yours, tackle these problems. Open to connecting to share insights?",
                    f"{greeting}, came across your profile while researching {company}. I have a background in cloud ops and automation, and I'm reaching out to build my professional network within the industry.\n\nI specialize in bridging the gap between development and operations. By implementing comprehensive CI/CD pipelines and shifting security left, I help teams deliver code faster and safer. I'm deeply familiar with the intricacies of Linux administration and container orchestration, which form the backbone of the systems I manage.\n\nI'd be very interested in hearing your perspective on the current technical landscape. Curious to connect and follow your team's work.",
                ]
        elif has_name and has_title:
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                options = [
                    f"{greeting}, saw your work as {title}. I'm an experienced professional looking for new challenges, specifically roles where I can architect and manage large-scale solutions.\n\nMy technical journey has been defined by a commitment to automation and reliability. I have successfully migrated legacy hardware to the cloud, implemented comprehensive monitoring solutions with Prometheus and Grafana, and drastically reduced deployment times using modern CI/CD practices. I treat infrastructure as code, ensuring that every change is tracked, tested, and reversible.\n\nI am currently exploring the market for roles that will allow me to leverage these skills to solve complex operational problems. Are you currently hiring for any infrastructure roles on your team?",
                    f"{greeting}, noticed you're a {title}. I have a strong professional background, and I'm reaching out to see if my profile aligns with any of your current hiring needs.\n\nAs a Site Reliability Engineer, my primary focus is protecting the user experience by ensuring the backend services are always available and performant. I write automation scripts in Python and Bash, manage complex Kubernetes deployments, and constantly analyze system metrics to identify potential bottlenecks before they cause outages. I am a strong advocate for proactive infrastructure management.\n\nI would love the opportunity to bring this proactive, automation-first mindset to your organization. Would you be open to reviewing my resume for potential fits?",
                ]
            else:
                options = [
                    f"{greeting}, your work as {title} caught my attention. I'm building my professional experience, and I'm looking to connect with leaders and peers in the field.\n\nThe challenges of leading fast-paced, high impact work are what drive me. I spend my time diving deep into execution and defining clear processes to automate tedious operational tasks. I believe that a strong culture of ownership is the key to velocity and stability in any company.\n\nI am trying to expand my network thoughtfully with individuals whose careers I respect. Would love to connect and follow your journey.",
                    f"{greeting}, saw your role as {title}. I am an experienced professional, where I focus on building resilient backend systems that can scale dynamically with user demand.\n\nMy expertise lies in taking complex, manual processes and turning them into streamlined, automated workflows. Whether it's setting up a new CI/CD pipeline from scratch or troubleshooting a difficult networking issue in a VPC, I enjoy the puzzle of operations engineering. I am constantly exploring new tools and methodologies to improve system reliability.\n\nI find your professional background very interesting. Curious to exchange perspectives and connect here on LinkedIn.",
                ]
        elif has_name:
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                options = [
                    f"{greeting}, came across your profile. I'm actively looking for new roles in my field, and I'm reaching out to share my background.\n\nI have a strong track record of designing, implementing, and maintaining highly available cloud architectures. By treating operations as a software engineering problem, I utilize tools like Terraform, Docker, and Kubernetes to automate deployments and ensure consistency. I am passionate about eliminating manual toil and fostering a culture of continuous delivery & integration.\n\nI am eager to bring my skills to a forward-thinking team. Are you hiring for any relevant positions in your organization?",
                    f"{greeting}, I'm an experienced professional with a strong track record, writing to you to explore potential career opportunities.\n\nMy focus is always on the triad of reliability, scalability, and security. I spend my days writing automation code, managing cloud providers, and configuring robust alerting systems to make sure the platform never goes down. I believe that good infrastructure should be invisible to the end-user, functioning flawlessly in the background.\n\nI am currently looking for my next big challenge. Are you open to reviewing profiles for potential openings at your company?",
                ]
            else:
                options = [
                    f"{greeting}, came across your profile and your background resonated with the work I do professionally. I am looking to expand my professional circle.\n\nI spend my professional time building the systems that allow software to run securely and at scale. It is a constantly evolving field that requires an understanding of both high-level architecture and deep, low-level system internals. I enjoy the challenge of automating complex workflows and ensuring high availability.\n\nI respect the path you've taken in your career. Open to connecting and sharing insights?",
                    f"{greeting}, I'm building my network in the infrastructure and cloud space, and your profile stood out to me as someone I would like to be connected with.\n\nMy daily work involves a mix of systems administration, software engineering, and architectural planning. I advocate for Site Reliability Engineering principles, believing that we should use software to solve operational problems. It's a role that demands constant learning and adaptation to new technologies.\n\nI am trying to learn from others navigating this industry. Would love to stay in touch and connect.",
                ]
        else:
            # MINIMAL DATA: Don't pretend we know them
            if intent == "opportunity" or intent == IntentType.OPPORTUNITY:
                options = [
                    "Hi, I'm an experienced professional exploring new opportunities. I am reaching out to see if my background might be a fit for your needs.\n\nMy core competencies include leading high-impact initiatives, taking extreme ownership of complex problems, and delivering results. I am deeply committed to the principles of scaling effectively and ensuring sustainable growth.\n\nAre you currently hiring for any roles? I would appreciate the opportunity to share my resume.",
                    "Hi, I specialize in cloud operations and automation, and I'm looking for my next role. I wanted to proactively reach out with my professional background.\n\nI have dedicated my career to building the invisible backbone of modern software applications. I excel at designing CI/CD pipelines that allow developers to ship code rapidly without compromising on security or stability. From managing Linux servers to optimizing database performance, I thrive on solving complex backend infrastructure challenges.\n\nIf your team is recruiting, would you be open to a brief chat or reviewing my profile?",
                ]
            else:
                options = [
                    "Hi, came across your profile while exploring open roles in my field. Would love to connect and learn more about your work.",
                    "Hi, I'm an experienced professional exploring new opportunities. Would love to connect.",
                    "Hi, your profile came up while I was researching roles in my industry. I work in the tech space — curious to connect.",
                ]
        return random.choice(options)

    # ============ EMAIL TEMPLATES ============
    else:
        subject = f"{company}" if has_company else "Quick intro"
        body_greeting = f"Hi {first_name}," if has_name else "Hi,"

        if has_name and has_company:
            body = f"{body_greeting}\n\nCame across your profile at {company}. I work in the tech space — and your background resonated with the kind of work I enjoy.\n\nWould you be open to a brief exchange?\n\n{sender_first}"
        elif has_name:
            body = f"{body_greeting}\n\nI found your profile while exploring opportunities in {signal}. I work in cloud ops and systems engineering — your background caught my eye.\n\nOpen to connecting?\n\n{sender_first}"
        else:
            body = f"{body_greeting}\n\nI came across your profile while researching open roles in my field. I have solid hands-on experience.\n\nWould love to connect if there's a fit.\n\n{sender_first}"

        return f"Subject: {subject}\n\n{body}"



# Updated system prompts with stronger tone anchors + Q2 Persona Anchor
SYSTEM_PROMPTS = {
    IntentType.CURIOUS: PERSONA_ANCHOR
    + """
You are writing a LinkedIn connection request.
TONE: Casual, mid-thought, low-pressure. Like a quick note to a peer.
GOAL: Spark conversation, not a meeting.

NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain.
- Do NOT give advice.
- Do NOT include context-setting sentences.
- Do NOT use "I hope this finds you well".
- Do NOT use "I wanted to reach out".

RULES:
- Start MID-THOUGHT ("Saw you're...", "Noticed...")
- NO introductions ("Hi name, I am...")
- Write 1-2 distinct paragraphs.
- MAX 1 question.

STRUCTURE:
1. "Hi [Name]"
2. Observation ("Saw you're hiring for X", "Noticed your post on Y")
3. Soft question ("Curious how you're thinking about Z", "Open to a quick exchange?")

MAX: 600 chars. Write the message ONLY.
""",
    IntentType.PEER: PERSONA_ANCHOR
    + """
You are writing a cold email to a peer.
TONE: Professional but 'typed', not 'composed'. Slightly asymmetrical.
GOAL: Soft networking or idea exchange.

NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain why you are writing.
- Do NOT use formal transitions ("Additionally", "Moreover").
- Do NOT summarize.
- Do NOT look for "synergies".

RULES:
- Paragraphs should be short and punchy.
- No "Sincerely" or "Best regards".

STRUCTURE:
Subject: [Re: their work/role] or [Quick question]
Body:
1. Context (1 sentence)
2.The "Ask" / Curiosity (1 sentence)
Sign-off: "Curious how this lines up.", "Open to thoughts?"

MAX: 90 words. Write the message ONLY.
""",
    IntentType.SOFT: PERSONA_ANCHOR
    + """
You are writing a soft networking message.
TONE: Warm, friendly, slightly deferential but confident.
GOAL: Get on their radar without asking for anything heavy.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT explain.
- Do NOT use "picked your brain" or "15 mins".

RULES:
- Genuine compliment (must be specific).
- Soft open loop ("Wondering if...")

MAX: 600 chars (LI) or 80 words (Email). Write the message ONLY.
""",
    IntentType.DIRECT: PERSONA_ANCHOR
    + """
You are writing a high-signal value email.
TONE: Direct, calm, confident.
GOAL: Proposition value without sales hype.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT use buzzwords ("revolutionize", "synergy").
- Do NOT explain the value proposition ("This allows you to..."). Show it.

RULES:
- Problem -> Solution -> Soft CTA
- CTA must be soft: "Worth a look?", "Open to a peek?"

MAX: 100 words. Write the message ONLY.
""",
    IntentType.OPPORTUNITY: PERSONA_ANCHOR
    + """
You are writing a high-impact outreach message about an open opportunity.
TONE: Professional, competent, and direct.
GOAL: Express interest in an open role and secure next steps.
NEGATIVE CONSTRAINTS (CRITICAL):
- Do NOT use "I'm a [your role] with experience in...". That is boring. Start creatively.
- Do NOT use "I hope this email finds you well".
- Do NOT use repetitive or awkward greetings (e.g. "Hi Name, Dear Name"). Only use one simple greeting like "Hi [Name]," or "Hi,".

RULES:
- Hook them immediately with your strongest skill mapped to their role.
- Be articulate and detailed without rambling.

Write the message ONLY.
""",
    "GENERIC": PERSONA_ANCHOR
    + """
You are writing a generic but polite outreach.
TONE: Honest, extremely brief.
GOAL: Connect without pretending to know them deeply.
STRATEGY: Be vulnerable ("I don't know you well but...")
MAX: 150 chars. Write the message ONLY.
""",
}


@router.post("", response_model=Draft)
def create_draft(draft: DraftCreate):
    """Create a new draft."""
    supabase = get_supabase()
    if supabase:
        result = supabase.table("drafts").insert(draft.model_dump()).execute()
        if result.data:
            candidate = (
                supabase.table("candidates")
                .select("name")
                .eq("id", draft.candidate_id)
                .single()
                .execute()
            )
            supabase.table("activity_log").insert(
                {
                    "candidate_id": draft.candidate_id,
                    "action_type": "draft_created",
                    "title": f"Drafted email to {candidate.data['name'] if candidate.data else 'Unknown'}",
                    "description": "AI generated based on profile",
                }
            ).execute()
            return result.data[0]
    raise HTTPException(status_code=500, detail="Failed to create draft")


@router.post("/generate/{candidate_id}", response_model=DraftGenerateResponse)
async def generate_draft(
    candidate_id: int, context: str = "", contact_type: str = "auto"
):
    """Generate AI draft with MULTI-VARIANT SCORING (Priority 1-3 Optimizations)."""
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        # Auto-detect contact type
        if contact_type == "auto":
            contact_type = "linkedin"  # Email drafting disabled

        # R5: Strict channel lock — reject invalid contact types early
        if contact_type not in VALID_CHANNELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid contact_type: {contact_type}. Must be one of {VALID_CHANNELS}",
            )

        # PRE-FLIGHT: Run all independent DB queries concurrently (Massive TTFT Reduction)
        def _fetch_candidate():
            try:
                return (
                    supabase.table("candidates")
                    .select("*")
                    .eq("id", candidate_id)
                    .single()
                    .execute()
                    .data
                )
            except Exception:
                return None

        def _fetch_settings():
            try:
                res = supabase.table("user_settings").select("*").eq("id", 1).execute()
                return (
                    res.data[0]
                    if res and res.data
                    else {
                        "full_name": "Siddharth",
                        "company": "Antigravity",
                        "role": "Founder",
                    }
                )
            except Exception:
                return {
                    "full_name": "Siddharth",
                    "company": "Antigravity",
                    "role": "Founder",
                }

        def _fetch_last_draft():
            try:
                return (
                    supabase.table("drafts")
                    .select("*")
                    .eq("candidate_id", candidate_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                    .data
                )
            except Exception:
                return []

        (
            raw_candidate,
            settings,
            brain,
            existing_query_data,
            recent_openers,
            biased_params,
        ) = await asyncio.gather(
            asyncio.to_thread(_fetch_candidate),
            asyncio.to_thread(_fetch_settings),
            asyncio.to_thread(get_cached_brain_context, supabase),
            asyncio.to_thread(_fetch_last_draft),
            asyncio.to_thread(get_recent_openers, supabase),
            asyncio.to_thread(get_biased_parameters, supabase),
        )

        # 1. Validate Candidate Data
        if not raw_candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # 1.5 CRITICAL: Clean candidate data before it touches any prompt
        c = clean_candidate_data(raw_candidate)
        logger.info(
            f"Data quality for candidate {candidate_id}: {c['_data_quality']}/4 | Name: {c.get('name')} | Title: {c.get('title')} | Company: {c.get('company')}"
        )

        sender_intro = f"{settings.get('full_name', 'Siddharth')} from {settings.get('company', 'Antigravity')}"

        # H1: Compute Deterministic Fingerprint
        tone_directive = CHANNEL_TONE.get(contact_type, "")
        fingerprint = generate_fingerprint(
            candidate_id,
            contact_type,
            brain.get("extracted_skills", []),
            brain.get("resume_text", ""),
            tone_directive,
        )

        # R1 & H1: Idempotency Check
        if existing_query_data:
            d = existing_query_data[0]
            recent_cutoff = (datetime.utcnow() - timedelta(seconds=60)).isoformat()
            created_at = d.get("created_at")
            stored_params = d.get("generation_params") or {}
            stored_fingerprint = stored_params.get("fingerprint")

            is_recent = created_at >= recent_cutoff
            is_fingerprint_match = stored_fingerprint == fingerprint

            if is_recent or is_fingerprint_match:
                reason_code = GenerationReason.IDEMPOTENT_RETURN
                logger.info(
                    f"Idempotent hit: candidate {candidate_id} | Recent: {is_recent} | HashMatch: {is_fingerprint_match}"
                )

                if contact_type == "linkedin":
                    return {
                        "type": "linkedin",
                        "message": d.get("body", ""),
                        "char_count": len(d.get("body", "")),
                        "quality_score": stored_params.get("score", 0),
                        "draft_id": d["id"],
                        "time_to_read": calculate_time_to_read(d.get("body", "")),
                        "variant_id": d.get("variant_id"),
                        "is_idempotent": True,
                        "reason": reason_code,
                    }
                else:
                    return {
                        "type": "email",
                        "subject": d.get("subject", ""),
                        "body": d.get("body", ""),
                        "word_count": len(d.get("body", "").split()),
                        "quality_score": stored_params.get("score", 0),
                        "draft_id": d["id"],
                        "time_to_read": calculate_time_to_read(d.get("body", "")),
                        "variant_id": d.get("variant_id"),
                        "is_idempotent": True,
                        "reason": reason_code,
                    }

        # NOTE: Run backend/migrations/seed_brain_context.sql in Supabase SQL Editor
        # if brain context is empty on first use — otherwise Generate Draft returns 412.
        # R2: Hard fail-fast on missing brain context
        if not brain.get("extracted_skills") and not brain.get("resume_text"):
            raise HTTPException(
                status_code=412,
                detail="Brain context is empty. Please add your skills first.",
            )

        # EARLY EXIT: If data quality is too low, skip AI and use smart template directly
        if c["_data_quality"] <= 1:
            logger.warning(
                f"Low data quality ({c['_data_quality']}/4) for candidate {candidate_id}. Using smart template."
            )
            signal = extract_primary_signal(c)
            intent = IntentType.OPPORTUNITY
            fallback_text = generate_fallback_draft(
                c,
                sender_intro,
                signal["signal"],
                intent.value,
                contact_type,
                skills=brain.get("extracted_skills", []),
                desired_role=settings.get("role"),
            )
            variant_id = str(uuid.uuid4())
            gen_params = {
                "variant_id": variant_id,
                "score": 60.0,
                "model": "smart-template-low-data",
                "context_band": "LOW",
                "signal_type": signal.get("type", "generic"),
                "is_fallback": True,
                "data_quality": c["_data_quality"],
            }
            if contact_type == "linkedin":
                res = (
                    supabase.table("drafts")
                    .insert(
                        {
                            "candidate_id": candidate_id,
                            "subject": "",
                            "body": fallback_text,
                            "intent": intent,
                            "temperature": 0.0,
                            "signal_used": signal["signal"],
                            "variant_id": variant_id,
                            "generation_params": gen_params,
                        }
                    )
                    .execute()
                )
                return {
                    "type": "linkedin",
                    "message": fallback_text,
                    "char_count": len(fallback_text),
                    "quality_score": 60.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(fallback_text),
                    "variant_id": variant_id,
                    "is_fallback": True,
                }
            else:
                lines = fallback_text.strip().split("\n")
                subject = "Quick intro"
                body_lines = []
                for line in lines:
                    if "Subject:" in line:
                        subject = line.replace("Subject:", "").strip()
                    elif line.strip():
                        body_lines.append(line)
                final_body = "\n".join(body_lines).strip()
                res = (
                    supabase.table("drafts")
                    .insert(
                        {
                            "candidate_id": candidate_id,
                            "subject": subject,
                            "body": final_body,
                            "intent": intent,
                            "temperature": 0.0,
                            "signal_used": signal["signal"],
                            "variant_id": variant_id,
                            "generation_params": gen_params,
                        }
                    )
                    .execute()
                )
                return {
                    "type": "email",
                    "subject": subject,
                    "body": final_body,
                    "word_count": len(final_body.split()),
                    "quality_score": 60.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(final_body),
                    "variant_id": variant_id,
                    "is_fallback": True,
                }

        raw_skills_list = brain.get("extracted_skills", [])
        skills = (
            ", ".join(raw_skills_list)
            or "Software Development, Automation, and Problem Solving"
        )
        # Grouped skills for prompt injection — prevents laundry-list skill dumps
        skills_grouped = _group_skills_for_prompt(raw_skills_list)

        # 3. CONTEXT COMPRESSION & MEMORY (Priority 2, 13)
        signal = extract_primary_signal(c)

        # Fetch Memory (Avoid Repetition) - Used pre-fetched concurrent result
        memory_constraint = ""
        if recent_openers:
            blocklist = "\\n- ".join(recent_openers)
            memory_constraint = f"\\nAvoid these recent openers:\\n- {blocklist}"

        logger.info(f"Primary signal: {signal['signal']} | Avoid: {signal['avoid']}")

        # 4. Build Prompt (Optimization 11, 12, 17)
        # Used pre-fetched concurrent result
        logger.info(f"Biasing suggestions: {biased_params}")

        # CONTEXT-AWARE CLASSIFICATION
        hiring_ctx = _detect_hiring_context(c)
        is_hiring_post = hiring_ctx["is_hiring_post"]
        hiring_role = hiring_ctx.get("hiring_role")
        recipient_role = hiring_ctx["recipient_role"]

        # Detect POST TYPE: LinkedIn Jobs section vs hiring post vs profile
        linkedin_url = c.get("linkedin_url") or ""
        post_type = "profile"  # default
        if "/jobs/" in linkedin_url or "/job/" in linkedin_url:
            post_type = "linkedin_job"  # From LinkedIn Jobs section
            is_hiring_post = True  # Always a hiring post
        elif "/posts/" in linkedin_url or "/feed/" in linkedin_url:
            post_type = "linkedin_post"  # Regular LinkedIn post
        elif "/in/" in linkedin_url:
            post_type = "linkedin_profile"  # Profile page

        logger.info(
            f"Context: is_hiring_post={is_hiring_post}, hiring_role={hiring_role}, recipient_role={recipient_role}, post_type={post_type}"
        )

        # Determine if Recipient is Company (Hiring Team) or Person
        is_company_recipient = False
        candidate_name = c.get("name") or ""
        candidate_company = c.get("company") or ""
        if candidate_name == "Hiring Team" or (
            candidate_company
            and candidate_name
            and candidate_company.lower() in candidate_name.lower()
        ):
            is_company_recipient = True

        # Context Bands
        context_band = "LOW"
        if len(brain.get("extracted_skills", [])) > 2 and c.get("title"):
            context_band = "MEDIUM"
        if signal.get("signal") and not signal.get("is_generic"):
            context_band = "HIGH"

        # ============================================================
        # DYNAMIC USER BIO — Built from Brain/Cortex skills
        # ============================================================
        sender_name = settings.get("full_name", "Professional")
        sender_company = settings.get("company", "")
        sender_role = settings.get("role", "Professional")

        user_bio = f"""
        Name: {sender_name}
        Role: {sender_role}
        Key Skills: {skills}
        {f'Current Company: {sender_company}' if sender_company else ''}
        Status: Actively looking for opportunities where I can apply these skills.
        Writing Boundary: Only claim the skills listed above or stated in the resume. Do not add cloud, DevOps, SRE, backend, frontend, or AI skills unless they appear in Cortex.
        """.strip()

        # Get post context (first 800 chars for richer understanding)
        post_context = (c.get("summary") or "")[:800].strip()

        # ============================================================
        # INTENT ROUTING (Post-type aware)
        # ============================================================
        if is_company_recipient:
            intent = IntentType.SOFT
            role_context = c.get("title") or sender_role
            task_instruction = "Generate a job inquiry message to a company page. Be respectful but direct about seeking opportunities."
        elif is_hiring_post:
            intent = IntentType.OPPORTUNITY
            role_context = hiring_role or c.get("title") or sender_role
            if post_type == "linkedin_job":
                task_instruction = f"Generate a JOB APPLICATION message. This is from a LinkedIn JOBS listing for '{hiring_role or c.get('title')}'. Write as if APPLYING for this specific position. Be specific about relevant skills."
            else:
                task_instruction = f"Generate a JOB APPLICATION message. The recipient POSTED about hiring for '{hiring_role or c.get('title')}'. Express genuine interest in the position they mentioned. Reference specifics from their post."
        elif c.get("title") and (
            "recruiter" in (c.get("title") or "").lower() or "talent" in (c.get("title") or "").lower()
        ):
            intent = IntentType.OPPORTUNITY
            role_context = sender_role
            task_instruction = f"Generate a JOB-SEEKING message to a recruiter. Ask directly if they have {sender_role} openings. Be clear you are looking for work, not just networking."
        else:
            intent = IntentType.OPPORTUNITY
            candidate_title = (c.get("title") or "").lower()
            role_context = sender_role
            if (
                candidate_title
                and "recruiter" not in candidate_title
                and "talent" not in candidate_title
            ):
                role_context = c.get("title") or sender_role
            task_instruction = "Generate a JOB OPPORTUNITY message. You are reaching out to explore job opportunities — NOT to network. Ask about openings at their company."

        # ============================================================
        # PROMPT CONSTRUCTION (Job-Application Focused)
        # ============================================================
        if intent == IntentType.OPPORTUNITY:
            # Build context block based on post type
            if is_hiring_post:
                if post_type == "linkedin_job":
                    context_block = f"""
            SOURCE: LinkedIn JOBS listing
            CRITICAL: This is a formal JOB POSTING from the Jobs section on LinkedIn.
            - The listing is for: {hiring_role or c.get('title')}
            - The recipient posted this job at: {c.get('company') or 'their company'}
            - Write as if you are APPLYING FOR THIS JOB. This is a job application, not a connection request.
            - Reference the specific role and why your skills ({skills}) make you a strong candidate.
            - DO NOT say 'looking to connect' or 'expand my network'.
            - DO say 'I am interested in the {hiring_role or c.get('title')} position' or 'applying for the role'.
            
            JOB DESCRIPTION:
            {post_context}
            """
                else:
                    context_block = f"""
            SOURCE: LinkedIn POST about hiring
            CRITICAL: This person WROTE A POST about hiring. They are a {recipient_role}.
            - They posted about hiring for: {hiring_role or c.get('title')}
            - They are NOT a {hiring_role or c.get('title')} themselves — they are RECRUITING for that role.
            - DO NOT say 'saw your work as {hiring_role}' — they don't work in that role.
            - DO reference their post: 'saw your post about the {hiring_role} opening' or 'noticed you are hiring for {hiring_role}'.
            - Express genuine interest in the position and explain how your skills ({skills}) are relevant.
            
            THEIR POST:
            {post_context}
            """
            else:
                # Regular profile — this person may or may not be hiring
                context_block = f"""
            SOURCE: LinkedIn Profile
            This person is {c.get('name') or 'a professional'}, working as {c.get('title') or 'a professional'} at {c.get('company') or 'their company'}.
            {f'PROFILE CONTEXT: {post_context}' if post_context else ''}
            
            You are reaching out to explore if their company has {sender_role} openings.
            Mention how your skills ({skills}) could add value to their team.
            """

            prompt = f"""
            # JOB APPLICATION MESSAGE GENERATOR
            
            You are writing a LinkedIn message on behalf of someone ACTIVELY SEEKING A JOB.
            This is a JOB APPLICATION outreach — NOT a networking or connection request.
            
            == APPLICANT (the person writing this message) ==
            {user_bio}
            
            == RECIPIENT ==
            Name: {c.get('name') or 'Hiring Professional'}
            At: {c.get('company') or 'their company'}
            
            {context_block}
            
            == RULES ==
            1. TASK: {task_instruction}
            
            2. STRUCTURE — ALWAYS follow this exactly:
               - Line 1 (Hook): One sentence directly tied to something specific in their job post or company. Reference what they're building, their role, or their specific opening. Never open with "I".
               
               [LEAVE ONE BLANK LINE HERE]
               
               - Line 2 (Proof): 2 sentences max. Group skills into meaningful pairs (e.g. "Python + AWS for backend, React + Next.js for frontend"). Never list more than 4 technologies. Lead with impact, not tools.
                 APPLICANT SKILLS (Use these to construct the middle section):
{skills_grouped}

               [LEAVE ONE BLANK LINE HERE]
               
               - Line 3 (CTA): One short, direct question. No more than 15 words. Example: "Open to a quick call this week?" or "Would you be open to connecting?"
               
               Always leave exactly one blank line between each of the 3 sections.
               
            3. HARD RULES — violating any = rewrite:
               - CHARACTER LIMIT: Final message MUST be under 950 characters. Never exceed.
               - BANNED PHRASES (never use these, ever): "I'm excited to...", "I came across your...", "I would love to...", "I'd appreciate the opportunity...", "drive innovation", "great fit", "versatile candidate", "leverage my skills", "contribute to your team's success", "actively looking for new opportunities", "are you currently hiring", "I'm confident in my ability to", "expand my network", "great to meet".
               - NEVER mention current or past employer unless explicitly provided in the user profile.
               - NEVER repeat the job title or salary from the post back to the recruiter.
               - NEVER ask if they're hiring — they posted the job, they're hiring.
               - NEVER write more than 4 technologies in a single sentence.
               - NEVER use one large paragraph — always use the 3-section structure with blank lines between.
               - ALWAYS write in first person as {sender_name}. No robotic sign-offs.
               - No emojis. Just the message text.
               - GROUNDING: Only claim skills from the domains listed above. Do not invent or add new skills.
               
            4. TONE — how it should feel:
               - Read like a senior professional reaching out — not someone begging for a chance.
               - Confident, warm, specific. Think: "I solve problems at this level, want to talk?" — not "please consider me."
               - The reader should finish the message thinking: "This person knows what they're doing."
               
            5. BEFORE FINALISING — check:
               [ ] Under 950 characters?
               [ ] No banned phrases?
               [ ] Hook references their specific post/company?
               [ ] Skills grouped, not dumped?
               [ ] CTA is one direct question under 15 words?
               [ ] No employer mentioned unless provided?
               [ ] 3 sections with exactly blank lines between?
               
               If ANY checkbox fails -> rewrite yourself silently before outputting.
            """
        else:
            # SOFT INTENT (Company pages, exploratory)
            prompt = f"""
            # JOB INQUIRY MESSAGE
            
            You are writing a LinkedIn message to a company or hiring team on behalf of a job seeker.
            
            == APPLICANT ==
            {user_bio}
            
            == RECIPIENT ==
            {c.get('name') or 'Hiring Team'} at {c.get('company') or 'the company'}
            Role listed: {c.get('title') or 'not specified'}
            {f'CONTEXT: {post_context}' if post_context else ''}
            
            == TASK ==
            {task_instruction}
            - Write a professional inquiry about open positions.
            - Focus most of the message on the applicant's Cortex skills ({skills}), job-search status, and value proposition. Use the rest to reference the RECIPIENT'S POST ({post_context}).
            - Ask if they are currently hiring for roles matching this background.
            - Sound professional and genuinely interested, not generic.
            - End with a clear ask: share resume, schedule a call, etc.
            - Aim for 130-220 words.
            - Use ONLY the Cortex skills listed here unless the resume explicitly proves another skill: {skills}.
            - No emojis. Only the message text.
            """

        # Q5: Inject channel tone lock into prompt
        tone_directive = CHANNEL_TONE.get(contact_type, "")
        if tone_directive:
            prompt = f"{tone_directive}\n\n{prompt}"

        # 5. MULTI-VARIANT SCORING (Priority 1)
        # Reduced to 1 variant for Gemini Free Tier (Optimization 69)
        candidate_context = {
            "name": c.get("name"),
            "company": c.get("company"),
            "title": c.get("title"),
            "intent": intent,
        }

        # H3: STRICT FALLBACK LADDER (Gemini -> Retry -> Template)
        # Note: Retry logic is handled inside generate_with_scoring/generate_with_gemini via tenacity
        try:
            result = await generate_with_scoring(
                prompt,
                contact_type,
                candidate_context,
                num_variants=1,
                suggested_temp=biased_params.get("suggested_temperature"),
            )
            reason_code = GenerationReason.FRESH_GENERATION
        except Exception as e:
            logger.error(f"H3: AI Generation CRITICAL FAILURE: {e}")
            result = None
            reason_code = GenerationReason.FALLBACK_TEMPLATE

        if not result:
            # H3: Final Fallback - Use Template
            logger.warning(
                "Switching to Fallback Template (Reason: AI Failed or Result None)."
            )
        elif result:
            # Validate completeness: reject truncated responses
            text = result.get("text", "")
            word_count = len(text.split())
            ends_cleanly = text.rstrip().endswith(('.', '!', '?', '"'))
            if word_count < 80 or (not ends_cleanly and word_count < 120):
                logger.warning(
                    f"AI response appears truncated ({word_count} words, clean_end={ends_cleanly}). Falling back to template."
                )
                result = None
                reason_code = GenerationReason.FALLBACK_TEMPLATE

        if not result:
            # H3: Final Fallback - Use Template
            logger.warning(
                "Switching to Fallback Template (Reason: AI Failed or Result None)."
            )
            fallback_text = generate_fallback_draft(
                c,
                sender_intro,
                signal["signal"],
                intent.value,
                contact_type,
                skills=brain.get("extracted_skills", []),
                desired_role=sender_role,
            )
            variant_id = str(uuid.uuid4())

            # H1/H2/H5: Audit Metadata
            gen_params = {
                "variant_id": variant_id,
                "score": 55.0,  # Baseline for templates
                "model": "fallback-template",
                "context_band": context_band,
                "signal_type": signal.get("type", "generic"),
                "is_fallback": True,
                "data_quality": c.get("_data_quality", 0),
                "fingerprint": fingerprint,  # H1
                "prompt_version": PROMPT_VERSION,  # H2
                "reason": reason_code,  # H5
                "skill_count": len(brain.get("extracted_skills", [])),  # H6
            }
            # (Duplicate block removed)
            if contact_type == "linkedin":
                res = (
                    supabase.table("drafts")
                    .insert(
                        {
                            "candidate_id": candidate_id,
                            "subject": "",
                            "body": fallback_text,
                            "intent": intent,
                            "temperature": 0.0,
                            "signal_used": signal["signal"],
                            "variant_id": variant_id,
                            "generation_params": gen_params,
                        }
                    )
                    .execute()
                )
                return {
                    "type": "linkedin",
                    "message": fallback_text,
                    "char_count": len(fallback_text),
                    "quality_score": 55.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(fallback_text),
                    "variant_id": variant_id,
                    "is_fallback": True,
                }
            else:
                lines = fallback_text.strip().split("\n")
                subject = "Quick intro"
                body_lines = []
                for line in lines:
                    if "Subject:" in line:
                        subject = line.replace("Subject:", "").strip()
                    elif line.strip():
                        body_lines.append(line)
                final_body = "\n".join(body_lines).strip()
                res = (
                    supabase.table("drafts")
                    .insert(
                        {
                            "candidate_id": candidate_id,
                            "subject": subject,
                            "body": final_body,
                            "intent": intent,
                            "temperature": 0.0,
                            "signal_used": signal["signal"],
                            "variant_id": variant_id,
                            "generation_params": gen_params,
                        }
                    )
                    .execute()
                )
                return {
                    "type": "email",
                    "subject": subject,
                    "body": final_body,
                    "word_count": len(final_body.split()),
                    "quality_score": 55.0,
                    "draft_id": res.data[0]["id"],
                    "time_to_read": calculate_time_to_read(final_body),
                    "variant_id": variant_id,
                    "is_fallback": True,
                }

        response_text = result["text"]
        score = result["score"]

        # ---- POST-PROCESSING PIPELINE (Q4, Q6, Q1) ----
        # Q6: Remove hedging language
        response_text = remove_hedging(response_text)
        # Q4: Length normalization + hard trim
        response_text = normalize_length(response_text, contact_type)
        # Q1: Structure validation
        if not validate_structure(response_text, contact_type):
            logger.warning(
                f"Q1 Structure validation failed for candidate {candidate_id}. Using as-is (still valid content)."
            )
        # Q3: Skills grounding check
        user_skills = brain.get("extracted_skills", [])
        if user_skills:
            grounding = verify_skills_grounding(response_text, user_skills)
            if grounding["hallucinated"]:
                logger.warning(
                    f"Q3 Hallucinated skills detected: {grounding['hallucinated']}"
                )

        logger.info(
            f"FINAL DRAFT | Score: {score:.1f} | Type: {contact_type} | Length: {len(response_text)}"
        )

        # 6. Parse and Save
        # Compute variant ID for this generation attempt
        variant_id = str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": score,
            "opener_hash": result.get("opener_hash"),
            "embedding": result.get("embedding"),
            "model": "gemini-2.0-flash",
            "temperature": result.get("temp", 0.4),
            "context_band": context_band,
            "signal_type": signal["type"],
            # H1/H2/H5: Audit Metadata
            "fingerprint": fingerprint,
            "prompt_version": PROMPT_VERSION,
            "reason": reason_code,
            "skill_count": len(brain.get("extracted_skills", [])),  # H6
        }

        if contact_type == "linkedin":
            final_msg = response_text.replace("Subject:", "").strip()

            # Remove any double greetings if the model ignored instructions
            # (e.g. "Hi Nidhi, Dear Nidhi," -> "Hi Nidhi,")
            lines = final_msg.split("\n")
            if lines and "," in lines[0]:
                first_line = lines[0].strip()
                # Check for pattern like "Hi [Name], Dear [Name]," or "Hi [Name] Hi [Name]"
                if first_line.count(",") >= 2 or ("Hi" in first_line and first_line.lower().count("hi") >= 2):
                    first_name = c.get("name", "").split()[0] if c.get("name") else "there"
                    lines[0] = f"Hi {first_name},"
                    final_msg = "\n".join(lines)

            res = (
                supabase.table("drafts")
                .insert(
                    {
                        "candidate_id": candidate_id,
                        "subject": "",
                        "body": final_msg,
                        "intent": intent,
                        "temperature": result.get("temp"),
                        "signal_used": signal["signal"],
                        "variant_id": variant_id,
                        "generation_params": gen_params,
                    }
                )
                .execute()
            )

            return {
                "type": "linkedin",
                "message": final_msg,
                "char_count": len(final_msg),
                "quality_score": round(score, 1),
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(final_msg),
                "variant_id": variant_id,
            }

        else:
            # Email parsing
            lines = response_text.strip().split("\n")
            subject = "Quick question"
            body_lines = []

            for line in lines:
                if "Subject:" in line:
                    subject = line.replace("Subject:", "").strip()
                elif line.strip():  # Non-empty lines
                    body_lines.append(line)

            final_body = "\n".join(body_lines).strip()

            res = (
                supabase.table("drafts")
                .insert(
                    {
                        "candidate_id": candidate_id,
                        "subject": subject,
                        "body": final_body,
                        "intent": intent,
                        "temperature": result.get("temp"),
                        "signal_used": signal["signal"],
                        "variant_id": variant_id,
                        "generation_params": gen_params,
                    }
                )
                .execute()
            )

            return {
                "type": "email",
                "subject": subject,
                "body": final_body,
                "word_count": len(final_body.split()),
                "quality_score": round(score, 1),
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(final_body),
                "variant_id": variant_id,
            }

    except HTTPException:
        # If it's a 500 from AI failure, fallback to template
        logger.warning("AI Generation failed. Switching to Fallback Template.")
        fallback_text = generate_fallback_draft(
            c,
            sender_intro,
            signal["signal"],
            intent.value if hasattr(intent, "value") else str(intent),
            contact_type,
            skills=brain.get("extracted_skills", []) if "brain" in locals() else [],
            desired_role=(
                sender_role
                if "sender_role" in locals()
                else settings.get("role", "Professional")
                if "settings" in locals()
                else "Professional"
            ),
        )

        # We need to wrap this in the same structure as a successful result to save it
        variant_id = str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": 50.0,  # Average score for fallback
            "model": "fallback-template",
            "context_band": context_band,
            "signal_type": signal.get("type", "generic"),
            "is_fallback": True,
        }

        # Save Fallback Draft
        if contact_type == "linkedin":
            res = (
                supabase.table("drafts")
                .insert(
                    {
                        "candidate_id": candidate_id,
                        "subject": "",
                        "body": fallback_text,
                        "intent": intent,
                        "temperature": 0.0,
                        "signal_used": signal["signal"],
                        "variant_id": variant_id,
                        "generation_params": gen_params,
                    }
                )
                .execute()
            )

            return {
                "type": "linkedin",
                "message": fallback_text,
                "char_count": len(fallback_text),
                "quality_score": 50.0,
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id,
                "is_fallback": True,
            }
        else:
            # Email Fallback
            subject = "Quick question"
            res = (
                supabase.table("drafts")
                .insert(
                    {
                        "candidate_id": candidate_id,
                        "subject": subject,
                        "body": fallback_text,
                        "intent": intent,
                        "temperature": 0.0,
                        "signal_used": signal["signal"],
                        "variant_id": variant_id,
                        "generation_params": gen_params,
                    }
                )
                .execute()
            )

            return {
                "type": "email",
                "subject": subject,
                "body": fallback_text,
                "word_count": len(fallback_text.split()),
                "quality_score": 50.0,
                "draft_id": res.data[0]["id"],
                "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id,
                "is_fallback": True,
            }

    except Exception as e:
        logger.error(f"Generate Check Failed: {e}")
        import traceback

        traceback.print_exc()

        # Fallback Logic (Optimization 10)
        logger.error("Falling back to Template Logic due to unexpected error.")

        # Ensure variables exist even if exception happened early in the try block
        safe_c = c if "c" in locals() else {"summary": "Experienced professional"}
        safe_intent = (
            intent.value
            if "intent" in locals() and hasattr(intent, "value")
            else "opportunity"
        )
        safe_signal = (
            signal["signal"]
            if "signal" in locals()
            else "Looking to connect and explore opportunities."
        )
        safe_sender = sender_intro if "sender_intro" in locals() else "A professional"
        safe_contact = contact_type if "contact_type" in locals() else "linkedin"

        fallback_text = generate_fallback_draft(
            safe_c,
            safe_sender,
            safe_signal,
            safe_intent,
            safe_contact,
            skills=brain.get("extracted_skills", []) if "brain" in locals() else [],
            desired_role=sender_role if "sender_role" in locals() else None,
        )

        variant_id = str(uuid.uuid4())
        gen_params = {
            "variant_id": variant_id,
            "score": 50.0,
            "model": "fallback-template-error",
            "is_fallback": True,
        }

        draft_id = 0
        try:
            if safe_contact == "linkedin":
                res = (
                    supabase.table("drafts")
                    .insert(
                        {
                            "candidate_id": candidate_id,
                            "subject": "",
                            "body": fallback_text,
                            "intent": safe_intent,
                            "temperature": 0.0,
                            "signal_used": safe_signal,
                            "variant_id": variant_id,
                            "generation_params": gen_params,
                        }
                    )
                    .execute()
                )
                draft_id = res.data[0]["id"] if res.data else 0
            else:
                res = (
                    supabase.table("drafts")
                    .insert(
                        {
                            "candidate_id": candidate_id,
                            "subject": "Quick intro",
                            "body": fallback_text,
                            "intent": safe_intent,
                            "temperature": 0.0,
                            "signal_used": safe_signal,
                            "variant_id": variant_id,
                            "generation_params": gen_params,
                        }
                    )
                    .execute()
                )
                draft_id = res.data[0]["id"] if res.data else 0
        except Exception as db_err:
            logger.error(f"Failed to save fallback draft to DB: {db_err}")

        if safe_contact == "linkedin":
            return {
                "type": "linkedin",
                "message": fallback_text,
                "char_count": len(fallback_text),
                "quality_score": 50.0,
                "draft_id": draft_id,
                "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id,
                "is_fallback": True,
            }
        else:
            return {
                "type": "email",
                "subject": "Quick intro",
                "body": fallback_text,
                "word_count": len(fallback_text.split()),
                "quality_score": 50.0,
                "draft_id": draft_id,
                "time_to_read": calculate_time_to_read(fallback_text),
                "variant_id": variant_id,
                "is_fallback": True,
            }


# In-memory dictionary to track batch operations (works for single-instance/local)
# In a distributed multi-instance deployment, this would use Redis or Postgres.
_BATCH_TASKS: Dict[str, Any] = {}


async def _process_batch_drafts(
    task_id: str, candidate_ids: list, context: str, contact_type: str
):
    """Background task to generate drafts sequentially without blocking."""
    _BATCH_TASKS[task_id] = {
        "status": "running",
        "completed": 0,
        "total": len(candidate_ids),
        "successful": 0,
        "failed": 0,
        "results": [],
    }

    for cid in candidate_ids:
        try:
            # We call the existing generate_draft function directly
            result = await generate_draft(
                candidate_id=cid, context=context, contact_type=contact_type
            )
            if result:
                _BATCH_TASKS[task_id]["successful"] += 1
                _BATCH_TASKS[task_id]["results"].append(
                    {"candidate_id": cid, "status": "success", "data": result}
                )
            else:
                _BATCH_TASKS[task_id]["failed"] += 1
                _BATCH_TASKS[task_id]["results"].append(
                    {
                        "candidate_id": cid,
                        "status": "error",
                        "error": "No result returned",
                    }
                )
        except Exception as e:
            logger.error(f"Batch generation error for candidate {cid}: {e}")
            _BATCH_TASKS[task_id]["failed"] += 1
            _BATCH_TASKS[task_id]["results"].append(
                {"candidate_id": cid, "status": "error", "error": str(e)}
            )

        _BATCH_TASKS[task_id]["completed"] += 1

        # Yield to event loop to prevent blocking other API requests
        await asyncio.sleep(0.1)

    _BATCH_TASKS[task_id]["status"] = "completed"


@router.post("/generate-batch")
async def generate_drafts_batch(body: dict, background_tasks: BackgroundTasks):
    """Start a background task for batch draft generation."""
    candidate_ids = body.get("candidate_ids", [])
    context = body.get("context", "")
    contact_type = body.get("contact_type", "auto")

    if not candidate_ids:
        raise HTTPException(status_code=400, detail="No candidate IDs provided")

    task_id = f"batch-draft-{uuid.uuid4()}"

    # Add the processing function to FastAPI's built-in BackgroundTasks
    background_tasks.add_task(
        _process_batch_drafts, task_id, candidate_ids, context, contact_type
    )

    return {
        "status": "running",
        "message": "Batch draft generation started",
        "task_id": task_id,
    }


@router.get("/batch/{task_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(task_id: str):
    """Check the status of a background batch draft workflow."""
    task_info = _BATCH_TASKS.get(task_id)

    if not task_info:
        return {
            "task_id": task_id,
            "status": "error",
            "completed": 0,
            "total": 0,
            "successful": 0,
            "failed": 0,
        }

    return {"task_id": task_id, **task_info}


@router.post("/edits")
async def save_draft_edit(edit: DraftEditCreate):
    """Save user manual edits for RAG feedback loop."""
    try:
        sb_client = get_supabase()

        data = {
            "candidate_id": edit.candidate_id,
            "original_text": edit.original_text,
            "edited_text": edit.edited_text,
            "contact_type": edit.contact_type,
        }

        sb_client.table("draft_edits").insert(data).execute()
        return {"status": "success", "message": "Draft edit saved for RAG feedback"}
    except Exception as e:
        logger.error(f"Error saving draft edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
