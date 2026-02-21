import asyncio
from playwright.async_api import async_playwright, expect

async def run_test():
    async with async_playwright() as pw:
        # Need userAgent to ensure Ctrl+K works? Usually fine.
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # LOGGING
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        try:
            # AUTH INJECTION (Bypass login page)
            await context.add_init_script("localStorage.setItem('isAuthenticated', 'true')")

            print("Navigating to Dashboard...")
            await page.goto("http://localhost:3000/", wait_until="domcontentloaded")
            
            # Use stricter wait for hydration/interactivity
            await page.wait_for_timeout(1000)

            print("Opening Command Palette (Ctrl+K)...")
            # Ensure focus on page
            await page.click("body")
            await page.wait_for_timeout(500)
            # Press Ctrl+K
            await page.keyboard.press("Control+k")

            print("Verifying Palette Visible...")
            # Check for "Global Command Menu" or input placeholder
            # Increase timeout as sometimes animation/rendering takes a moment
            await expect(page.get_by_placeholder("Type a command or search...")).to_be_visible(timeout=5000)

            print("Navigating to 'Search Leads'...")
            # Type "Search" to filter (just "Search" to be safe)
            await page.keyboard.type("Search")
            # Wait for item to appear
            item = page.get_by_text("Search Leads")
            await expect(item).to_be_visible()
            await item.click()

            print("Verifying Navigation...")
            await page.wait_for_url("**/search", timeout=5000)
            
            print("TC015: command_palette_functionality - PASSED")

        except Exception as e:
            print(f"TC015: command_palette_functionality - FAILED: {e}")
            await page.screenshot(path="TC015_error.png")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())