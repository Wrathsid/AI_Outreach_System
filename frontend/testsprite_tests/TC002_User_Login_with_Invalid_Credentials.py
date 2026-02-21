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

            # 2. Fill INVALID Credentials
            print("Filling invalid credentials...")
            await page.fill('input[type="email"]', 'fail@test.com') # Trigger the specific error logic
            await page.fill('input[type="password"]', 'wrongpass')

            # 3. Submit
            print("Submitting...")
            await page.click('button[type="submit"]')

            # 4. Assert Error Message
            print("Verifying Error Message...")
            # Expect "Invalid credentials" (matched from my page.tsx edit)
            await expect(page.get_by_text("Invalid credentials")).to_be_visible()
            
            print("TC002: Invalid Login - PASSED")

        except Exception as e:
            print(f"TC002: Invalid Login - FAILED: {e}")
            await page.screenshot(path="TC002_error.png")
            raise e
        finally:
            await browser.close()

asyncio.run(run_test())