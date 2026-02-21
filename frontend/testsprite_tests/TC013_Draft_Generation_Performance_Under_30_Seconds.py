import asyncio
import time
import re
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # LOGGING
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        # Mock API - delay 1s
        async def delayed_draft(route):
            if route.request.resource_type == "document":
                 await route.continue_()
                 return
            await asyncio.sleep(1) # 1s delay
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"message": "Hi fast user..."}',
                headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
            )

        async def handle_candidate(route):
            if route.request.resource_type == "document":
                 await route.continue_()
                 return
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"id": 1, "name": "Flash Gordon", "title": "Runner", "company": "SpeedForce", "linkedin_url": "https://linkedin.com/in/flash", "status": "new"}',
                headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
            )

        await page.route(re.compile(r".*/candidates/1"), handle_candidate)
        await page.route(re.compile(r".*/drafts/generate.*"), delayed_draft)

        # AUTH INJECTION
        await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")
        
        try:
            # Navigate and measure
            print("Navigating to Candidate Details...")
            start_time = time.time()
            await page.goto("http://localhost:3000/candidates/1", wait_until="domcontentloaded")

            # Strict Mode Debounce Workaround
            print("Waiting for debounce (Strict Mode workaround)...")
            await page.wait_for_timeout(2500)
            
            print("Clicking Regenerate...")
            await page.get_by_role("button", name="Regenerate").click()

            # Wait for draft
            print("Verifying Draft...")
            textarea = page.locator("textarea")
            await expect(textarea).to_have_value("Hi fast user...", timeout=30000) # 30s timeout
            
            end_time = time.time()
            duration = end_time - start_time
            print(f"Draft generation took {duration:.2f} seconds")

            if duration > 30:
                raise AssertionError(f"Draft generation took too long: {duration}s")
            
            print("TC013: performance_under_30s - PASSED")
        
        except Exception as e:
            print(f"TC013 FAILED: {e}")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())