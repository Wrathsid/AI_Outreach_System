import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        # Launch browser
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. Navigate to Login
            print("Navigating to Login...")
            # Use domcontentloaded because networkidle is flaky with HMR/WebSockets
            await page.goto("http://localhost:3000/login", wait_until="domcontentloaded", timeout=15000)

            # 2. Fill Credentials
            print("Filling credentials...")
            await page.fill('input[type="email"]', 'test@example.com')
            await page.fill('input[type="password"]', 'password123')

            # 3. Submit
            print("Submitting...")
            await page.click('button[type="submit"]')

            # 4. Assert Redirect to Dashboard
            print("Verifying Dashboard...")
            # Wait for URL to be root
            await page.wait_for_url("http://localhost:3000/", timeout=5000)
            
            # Assert "Ready to Prospect?" text is visible
            await expect(page.get_by_text("Ready to Prospect?")).to_be_visible()
            
            print("TC001: Login Success - PASSED")

        except Exception as e:
            print(f"TC001: Login Success - FAILED: {e}")
            await page.screenshot(path="TC001_error.png")
            raise e
        finally:
            await browser.close()

asyncio.run(run_test())