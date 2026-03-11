import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path)


async def test_generation():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    system_prompt = """
    You are writing a LinkedIn connection request to a Recruiter or TA.
    TONE: Comprehensive, highly detailed, professional, and persuasive.
    GOAL: Pitch yourself in a very thorough, multi-paragraph LinkedIn invite.
    NEGATIVE CONSTRAINTS (CRITICAL):
    - Do NOT use "I'm a DevOps engineer with experience in...". That is boring.
    - Do NOT use "I hope this email finds you well".

    RULES:
    - Hook them immediately with your 2 strongest skills mapped to their role.
    - Expand significantly on your background, providing detailed context on how you build scalable infrastructure.
    - Write at least 3 or 4 substantial paragraphs.
    - Soft Ask: "Open to connecting?" or "Worth a chat if roles open up?"

    STRUCTURE:
    Start with a strong hook about their recruitment focus.
    Follow up with a massive, detailed paragraph explaining your technical philosophy and specific tools (Linux, Cloud, etc.).
    Conclude with a soft ask.

    Write the message ONLY. Make it extremely detailed, aiming for around 2000 characters.
    """

    prompt = """
    You are generating a LinkedIn Connection Request (focus on extreme detail and length, aiming for 2000 chars).
    
    INPUT:
    - Target Role: DevOps / Site Reliability Engineer
    - Recipient: EXPANSIA at a great company
    
    TASK: Generate ONE comprehensive, multi-paragraph message.
    - Tie DevOps / Site Reliability Engineer to the user's infrastructure/cloud skills in great detail.
    - Do NOT start with "I'm an experienced engineer". Be more conversational.
    - No emojis. Only the message.
    """

    full_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{prompt}"

    print("Sending prompt to Gemini...")
    try:
        res = await asyncio.wait_for(
            client.aio.models.generate_content(
                model="gemini-1.5-flash-8b",
                contents=full_prompt,
                config=types.GenerateContentConfig(temperature=0.35),
            ),
            timeout=20.0,
        )
        print("--- FULL RESPONSE OBJECT ---")
        if hasattr(res, "candidates") and res.candidates:
            print(f"FINISH REASON: {res.candidates[0].finish_reason}")
            print(f"SAFETY RATINGS: {res.candidates[0].safety_ratings}")
        print(f"RAW RES LENGTH: {len(res.text) if res.text else 0}")
        print(f"RAW RES:\n{repr(res.text)}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(test_generation())
