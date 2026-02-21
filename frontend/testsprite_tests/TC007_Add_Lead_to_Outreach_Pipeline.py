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

            # 2. Mock APIs
            # Mock Search
            mock_search_data = '{"type":"result","data":{"name":"Jane Smith","title":"Product Manager","company":"Startup Inc","linkedin_url":"https://linkedin.com/in/janesmith","resonance_score":0.85}}\n{"type":"done"}'
            await page.route("**/discover/hr-search*", lambda route: route.fulfill(
                status=200,
                body=mock_search_data,
                headers={"Content-Type": "text/plain"}
            ))

            # Mock Create Candidate
            await page.route("**/candidates", lambda route: route.fulfill(
                status=200,
                body='{"id": 123, "name":"Jane Smith", "status":"new"}',
                headers={"Content-Type": "application/json"}
            ))

            # Mock Batch Pipeline Add
            await page.route("**/pipeline/batch", lambda route: route.fulfill(
                status=200,
                body='{"success": true}',
                headers={"Content-Type": "application/json"}
            ))
            
            # Mock Generate Draft (fire & forget, but might be called)
            await page.route("**/drafts/generate", lambda route: route.fulfill(
                status=200,
                body='{"success": true}',
                headers={"Content-Type": "application/json"}
            ))

            print("Navigating to Search...")
            await page.goto("http://localhost:3000/search", wait_until="domcontentloaded")

            print("Performing Search and Selection...")
            await page.fill('input[type="text"]', 'Product Manager')
            await page.press('input[type="text"]', 'Enter')

            # Wait for result
            await expect(page.get_by_text("Jane Smith")).to_be_visible()

            # Select the lead (click the card or checkbox)
            # The card has an onClick handler, toggles selection.
            # Locator: find the card container by text "Jane Smith" and click it
            # Or find the checkbox div
            # The card is usually a div with "Jane Smith" text inside.
            card = page.locator("div").filter(has_text="Jane Smith").last
            await card.click()

            # Verify "Add to Pipeline" button appears/updates
            add_button = page.get_by_role("button", name="Add to Pipeline")
            await expect(add_button).to_be_visible()
            
            print("Adding to Pipeline...")
            await add_button.click()

            # Verify Success / Redirect
            # App redirects to '/' (Pipeline) on success
            await page.wait_for_url("http://localhost:3000/", timeout=5000)
            
            # Ideally verify toast, but redirect is strong enough signal of success flow
            print("TC007: add_lead_to_pipeline - PASSED")

        except Exception as e:
            print(f"TC007: add_lead_to_pipeline - FAILED: {e}")
            await page.screenshot(path="TC007_error.png")
            raise e
        finally:
            await browser.close()

asyncio.run(run_test())