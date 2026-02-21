import asyncio
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

        try:
            # Mock Candidates API (GET)
            # Use regex to match /candidates but NOT /candidates/1
            # Matches end of string or query params
            async def handle_candidates(route):
                if route.request.resource_type == "document":
                    await route.continue_()
                    return
                
                print(f"MOCK HIT CANDIDATES: {route.request.url}")
                mock_candidates = '[{"id":1,"name":"Alice Wonderland","title":"CEO","company":"Wonderland Inc","status":"new","match_score":0.9},{"id":2,"name":"Bob Builder","title":"Construction Manager","company":"Builders Co","status":"contacted","match_score":0.7}]'
                
                await route.fulfill(
                    status=200,
                    body=mock_candidates,
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                )

            await page.route(re.compile(r".*/candidates($|\?.*)"), handle_candidates)

            # AUTH INJECTION
            await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")

            print("Navigating to Candidates Pipeline...")
            await page.goto("http://localhost:3000/candidates", wait_until="domcontentloaded")
            
            print(f"Current URL: {page.url}")
            
            if "/login" in page.url:
               print("Redirected to Login - Auth Failure?")

            print("Verifying Candidate List...")
            # Check for header - Use h1 locator to strictly match the visible header
            await expect(page.locator("h1", has_text="Pipeline")).to_be_visible(timeout=10000)
            
            # Check for candidates
            await expect(page.get_by_text("Alice Wonderland")).to_be_visible()
            await expect(page.get_by_text("Bob Builder")).to_be_visible()
            
            # Check status badges
            await expect(page.get_by_text("New", exact=True)).to_be_visible() # Alice has New
            await expect(page.get_by_text("Contacted", exact=True)).to_be_visible() # Bob has Contacted

            print("TC008: view_manage_candidates - PASSED")

        except Exception as e:
            print(f"TC008: view_manage_candidates - FAILED: {e}")
            print("PAGE CONTENT DUMP:")
            content = await page.content()
            print(content[:2000] + "... (truncated)" if len(content) > 2000 else content)
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())