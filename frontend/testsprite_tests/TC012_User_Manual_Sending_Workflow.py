import asyncio
import re
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        # Launch options
        browser = await pw.chromium.launch(headless=True)
        # Context with clipboard permissions
        context = await browser.new_context(permissions=["clipboard-write", "clipboard-read"])
        page = await context.new_page()
        
         # LOGGING
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        # MOCK HANDLERS
        async def handle_candidate(route):
            if route.request.resource_type == "document":
                await route.continue_()
                return
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"id": 1, "name": "Bob Builder", "title": "Engineer", "company": "BuildIt", "linkedin_url": "https://linkedin.com/in/bob", "status": "new"}',
                headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
            )

        async def handle_draft(route):
            if route.request.resource_type == "document":
                await route.continue_()
                return
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"message": "Hi Bob, can we build it?"}',
                headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
            )

        async def handle_sent(route):
             await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"success": true}',
                headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
            )

        # ROUTES
        await page.route(re.compile(r".*/candidates/1/sent"), handle_sent)
        await page.route(re.compile(r".*/candidates/1"), handle_candidate)
        await page.route(re.compile(r".*/drafts/generate.*"), handle_draft)

        # AUTH INJECTION
        await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")
        
        try:
            # Navigate to Candidate Details
            print("Navigating to Candidate Details...")
            await page.goto("http://localhost:3000/candidates/1", wait_until="domcontentloaded")

            # Assert Header
            await expect(page.get_by_text("Bob Builder", exact=False)).to_be_visible(timeout=5000)

            # Strict Mode Debounce Workaround
            print("Waiting for debounce (Strict Mode workaround)...")
            await page.wait_for_timeout(2500)
            
            print("Clicking Regenerate...")
            await page.get_by_role("button", name="Regenerate").click()

            # Wait for draft
            print("Verifying Draft...")
            textarea = page.locator("textarea")
            await expect(textarea).to_have_value("Hi Bob, can we build it?", timeout=10000)

            # Click Copy
            print("Clicking Copy...")
            copy_btn = page.get_by_role("button", name="Copy for LinkedIn")
            await copy_btn.click()

            # Assert Button Change
            await expect(page.get_by_role("button", name="Copied!")).to_be_visible()
            
            print("TC012: manual_sending_workflow - PASSED")
        
        except Exception as e:
            print(f"TC012 FAILED: {e}")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())