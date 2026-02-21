import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        # Ensure clean context (no storage/cookies)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            print("Accessing Protected Route (candidates)...")
            # Navigate to a protected route
            await page.goto("http://localhost:3000/candidates", wait_until="domcontentloaded", timeout=15000)

            print("Verifying Redirect to Login...")
            # 1. Check URL contains /login
            # Wait for it to settle
            await page.wait_for_url("**/login", timeout=5000)
            
            # 2. Check for Login Page specific text
            # "Welcome Back" is the title in login/page.tsx
            await expect(page.get_by_text("Welcome Back")).to_be_visible()

            print("TC004: protected_route_access - PASSED")

        except Exception as e:
            print(f"TC004: protected_route_access - FAILED: {e}")
            await page.screenshot(path="TC004_error.png")
            raise e
        finally:
            await browser.close()

asyncio.run(run_test())