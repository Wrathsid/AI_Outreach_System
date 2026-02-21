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
        # page.on("request", lambda req: print(f"REQUEST: {req.url}")) 
        
        async def log_route(route):
             print(f"ROUTE: {route.request.url}")
             try:
                 await route.continue_()
             except:
                 pass
        await page.route("**/*", log_route)

        # MOCK HANDLERS
        async def handle_candidate(route):
            if route.request.resource_type == "document":
                await route.continue_()
                return

            print(f"MOCK HIT CANDIDATE: {route.request.url}")
            # Ensure we return valid JSON
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"id": 1, "name": "Alice Wonderland", "title": "CEO", "company": "Wonderland Inc", "linkedin_url": "https://linkedin.com/in/alice", "status": "new"}',
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                }
            )

        async def handle_draft(route):
            if route.request.resource_type == "document":
                await route.continue_()
                return

            print(f"MOCK HIT DRAFT: {route.request.url}")
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"message": "Hi Alice, I saw your work at Wonderland Inc..."}',
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                }
            )

        # ROUTE REGISTRATION (Last added takes precedence)
        # Match .../candidates/1
        await page.route(re.compile(r".*/candidates/1"), handle_candidate)
        # Match .../drafts/generate/1?context=...
        await page.route(re.compile(r".*/drafts/generate.*"), handle_draft)

        # AUTH INJECTION
        await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")
        
        try:
            print("Navigating to Candidate Details...")
            await page.goto("http://localhost:3000/candidates/1", wait_until="domcontentloaded")

            # Assert Header
            # Use text selector as role might fail if content is loading or partial
            await expect(page.get_by_text("Alice Wonderland", exact=False)).to_be_visible(timeout=5000)

            # Strict Mode Debounce Workaround: 
            # If Strict Mode runs, the first effect call might fire (and unmount), setting the debounce timer.
            # The second call (remount) is then blocked by the 2s debounce.
            # We wait 2.5s and click Regenerate to force it.
            print("Waiting for debounce (Strict Mode workaround)...")
            await page.wait_for_timeout(2500)
            
            print("Clicking Regenerate...")
            await page.get_by_role("button", name="Regenerate").click()

            # Assert Draft Generated
            print("Verifying Draft Generation...")
            textarea = page.locator("textarea")
            await expect(textarea).to_have_value("Hi Alice, I saw your work at Wonderland Inc...", timeout=10000)
            
            print("TC010: draft_generation_channel - PASSED")

        except Exception as e:
            print(f"TC010: FAILED - {e}")
            print("PAGE CONTENT DUMP:")
            content = await page.content()
            print(content[:2000] + "... (truncated)" if len(content) > 2000 else content)
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())