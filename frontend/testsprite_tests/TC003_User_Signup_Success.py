import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            print("Navigating to Signup...")
            # Use domcontentloaded for stability
            await page.goto("http://localhost:3000/signup", wait_until="domcontentloaded", timeout=15000)

            print("Filling signup form...")
            await page.fill('input[type="email"]', 'newuser@test.com')
            await page.fill('input[type="password"]', 'password123')

            print("Submitting...")
            # Click the signup button (using specific text or type)
            await page.click('button[type="submit"]')

            print("Verifying Redirect to Dashboard...")
            # Expect redirect to root
            await page.wait_for_url("http://localhost:3000/", timeout=8000)
            
            # Assert "Ready to Prospect?" text is visible (Dashboard unique element)
            await expect(page.get_by_text("Ready to Prospect?")).to_be_visible()

            print("TC003: user_signup_success - PASSED")

        except Exception as e:
            print(f"TC003: user_signup_success - FAILED: {e}")
            await page.screenshot(path="TC003_error.png")
            # Don't fail the batch if one fails, but we print error. 
            # Actually, standard is to exit 1 for CI, but for batch script it catches it.
            # We raise so batch sees it as fail.
            raise e
        finally:
            await browser.close()

asyncio.run(run_test())