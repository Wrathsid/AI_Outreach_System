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

        try:
            # MOCK API
            async def handle_stats(route):
                if route.request.resource_type == "document":
                    await route.continue_()
                    return
                await route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"weekly_goal_percent": 75, "people_found": 120, "emails_sent": 45, "recent_leads": [], "top_industries": []}',
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            async def handle_funnel(route):
                if route.request.resource_type == "document":
                    await route.continue_()
                    return
                await route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"total_candidates": 120, "conversions": {"found_to_contacted": 30, "contacted_to_replied": 10}, "funnel": []}',
                     headers={"Access-Control-Allow-Origin": "*"}
                )

            await page.route(re.compile(r".*/stats$"), handle_stats)
            await page.route(re.compile(r".*/stats/funnel$"), handle_funnel)

            # AUTH INJECTION
            await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")

            print("Navigating to Analytics Page...")
            await page.goto("http://localhost:3000/analytics", wait_until="domcontentloaded")

            print("Verifying Total Candidates...")
            # Expect "120" or "Total Candidates"
            await expect(page.get_by_text("Total Candidates")).to_be_visible(timeout=10000)
            await expect(page.get_by_text("120")).to_be_visible()

            print("TC014: dashboard_stats - PASSED")

        except Exception as e:
            print(f"TC014 FAILED: {e}")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())