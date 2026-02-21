import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        # Launch browser
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # LOGGING
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        try:
            print("TC018: Testing Session Maintenance...")

            # 1. Navigate to Login page first
            await page.goto("http://localhost:3000/login", wait_until="domcontentloaded")
            
            # 2. Inject Authentication Manually (NOT via init_script which persists on reload)
            await page.evaluate("localStorage.setItem('isAuthenticated', 'true')")
            
            # 3. Navigate to Dashboard (Protected Route)
            print("Navigating to Dashboard...")
            await page.goto("http://localhost:3000/", wait_until="domcontentloaded")
            
            # 4. Verify Access
            print("Verifying initial access...")
            await expect(page).to_have_url("http://localhost:3000/")


            # "Ready to Prospect?" is on the dashboard
            await expect(page.get_by_text("Ready to Prospect?")).to_be_visible()

            # 4. Reload Page
            print("Reloading page...")
            await page.reload(wait_until="domcontentloaded")

            # 5. Verify Session Persisted
            print("Verifying session persistence...")
            await expect(page).to_have_url("http://localhost:3000/")
            await expect(page.get_by_text("Ready to Prospect?")).to_be_visible()
            
            # 6. Verify Logout (Mocked by clearing storage)
            print("Testing Logout flow (simulated)...")
            val_before = await page.evaluate("localStorage.getItem('isAuthenticated')")
            print(f"Auth before clear: {val_before}")
            
            await page.evaluate("localStorage.removeItem('isAuthenticated')")
            
            val_after = await page.evaluate("localStorage.getItem('isAuthenticated')")
            print(f"Auth after clear (pre-reload): {val_after}")

            await page.reload(wait_until="domcontentloaded")
            
            val_reload = await page.evaluate("localStorage.getItem('isAuthenticated')")
            print(f"Auth after reload: {val_reload}")

            # 7. Verify Redirect to Login
            print("Verifying redirect to login...")
            # Should redirect to login
            import re
            await expect(page).to_have_url(re.compile(r".*/login"))
            
            print("TC018: User Session Maintenance - PASSED")

        except Exception as e:
            print(f"TC018: User Session Maintenance - FAILED: {e}")
            await page.screenshot(path="TC018_error.png")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
    