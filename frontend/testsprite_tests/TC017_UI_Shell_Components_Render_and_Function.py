import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # AUTH INJECTION
            await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")

            print("Navigating to Home...")
            await page.goto("http://localhost:3000/", wait_until="domcontentloaded")

            print("Verifying Sidebar/Shell...")
            # Check for Candidates link in sidebar using href
            await expect(page.locator("a[href='/candidates']").first).to_be_visible(timeout=10000)
            
            # Check for Search link
            await expect(page.locator("a[href='/search']").first).to_be_visible()

            print("TC017: ui_shell - PASSED")

        except Exception as e:
            print(f"TC017 FAILED: {e}")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())