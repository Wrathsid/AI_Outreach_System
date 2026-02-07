
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

load_dotenv()

from backend.config import generate_with_openai, OPENAI_API_KEY

async def test():
    print(f"Testing OpenAI with key: {OPENAI_API_KEY[:5]}...")
    try:
        response = await generate_with_openai("Hello, are you there?", system_prompt="Answer yes or no.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test())
