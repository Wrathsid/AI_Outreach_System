import sys
import os
import asyncio

from google import genai
from google.genai import types

async def test_generation():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = '''
    Hey! Can you write me a short 2-sentence paragraph about DevOps?
    '''
    
    print("Sending basic prompt to Gemini...")
    res = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.5, max_output_tokens=300)
    )
    print(f"RAW RES LENGTH: {len(res.text) if res.text else 0}")
    print(f"RAW RES:\n{repr(res.text)}")

if __name__ == "__main__":
    test_generation()
