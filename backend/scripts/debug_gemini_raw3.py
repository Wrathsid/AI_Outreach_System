import os
import asyncio
from google import genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path)


async def test_generation():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = "Hi, this is a test. Please reply with exactly two sentences describing what a dog is."

    print("Sending prompt to Gemini...")
    try:
        res = await asyncio.wait_for(
            client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            ),
            timeout=15.0,
        )
        print(f"RAW RES LENGTH: {len(res.text) if res.text else 0}")
        print(f"RAW RES:\n{repr(res.text)}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(test_generation())
