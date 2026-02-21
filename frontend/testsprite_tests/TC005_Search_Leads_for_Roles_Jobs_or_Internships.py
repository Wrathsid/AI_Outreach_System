import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. Login (Simulated)
            await page.goto("http://localhost:3000/login", wait_until="domcontentloaded")
            await page.evaluate("localStorage.setItem('isAuthenticated', 'true')")
            await page.goto("http://localhost:3000/", wait_until="domcontentloaded")

            # 2. Mock Search API
            # Response format: simulating ndjson stream mechanism used in SearchPage
            # The app splits by newline and parses JSON.
            mock_data = '{"type":"result","data":{"name":"John Doe","title":"Software Engineer","company":"Tech Corp","linkedin_url":"https://linkedin.com/in/johndoe","resonance_score":0.95}}\n{"type":"done"}'
            
            await page.route("**/discover/hr-search*", lambda route: route.fulfill(
                status=200,
                body=mock_data,
                headers={"Content-Type": "text/plain"}
            ))

            print("Navigating to Search...")
            await page.goto("http://localhost:3000/search", wait_until="domcontentloaded")

            print("Performing Search...")
            # Type into search box
            await page.fill('input[type="text"]', 'Software Engineer')
            # Press Enter
            await page.press('input[type="text"]', 'Enter')

            print("Verifying Results...")
            # Wait for results to appear
            # Look for lead name
            await expect(page.get_by_text("John Doe")).to_be_visible(timeout=10000)
            await expect(page.get_by_text("Tech Corp")).to_be_visible()

            print("TC005: search_leads - PASSED")

        except Exception as e:
            print(f"TC005: search_leads - FAILED: {e}")
            await page.screenshot(path="TC005_error.png")
            raise e
        finally:
            await browser.close()

asyncio.run(run_test())