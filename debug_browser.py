import asyncio
import logging
import sys
from backend.services.browser_automation import launch_linkedin_message

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)

async def main():
    print("Testing Browser Automation Launch...")
    try:
        # Dummy URL and text
        result = await launch_linkedin_message("https://www.linkedin.com/in/williamhgates/", "Hello Bill, this is a test.")
        print("Result:", result)
    except Exception as e:
        print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
