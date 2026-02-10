import asyncio
from playwright.async_api import async_playwright
import os
import logging

logger = logging.getLogger(__name__)


# Browser Configurations
# Browser Configurations
BROWSERS = {
    "brave": {
        # Use a SEPARATE profile for automation so it doesn't conflict with the user's main open browser
        "user_data": os.path.join(os.path.expanduser("~"), r"AppData\Local\BraveSoftware\Brave-Browser\User Data Automation"),
        "executable": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "channel": None
    },
    "chrome": {
        "user_data": os.path.join(os.path.expanduser("~"), r"AppData\Local\Google\Chrome\User Data Automation"),
        "executable": None,
        "channel": "chrome"
    }
}

def get_browser_config():
    """
    Detects available browser (prioritizing Brave) and returns config.
    """
    # 1. Check for Brave
    if os.path.exists(BROWSERS["brave"]["executable"]):
        logger.info("Brave Browser detected. Using Brave.")
        return BROWSERS["brave"]
    
    # 2. Fallback to Chrome
    logger.info("Brave not found. Falling back to Chrome.")
    return BROWSERS["chrome"]

HEADLESS = False  # Must be False to see the window

async def launch_linkedin_message(linkedin_url: str, message_text: str):
    """
    Launches Brave with existing user profile, goes to LinkedIn profile,
    clicks Connect, and pastes the message.
    """
    logger.info(f"Launching Automation for: {linkedin_url}")
    
    async with async_playwright() as p:
        browser_type = p.chromium
        
        config = get_browser_config()
        
        # Launch Browser (Persistent Context)
        try:
            launch_args = {
                "user_data_dir": config["user_data"],
                "headless": HEADLESS,
                "no_viewport": True,
                "args": [
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars"
                ],
                "ignore_default_args": ["--enable-automation"]  # Hide "Chrome is being controlled by automated software"
            }
            
            if config["executable"]:
                launch_args["executable_path"] = config["executable"]
            
            if config["channel"]:
                launch_args["channel"] = config["channel"]

            browser = await p.chromium.launch_persistent_context(**launch_args)
            logger.info(f"Launched Persistent Context successfully using {config.get('executable', 'Chrome')}")
        except Exception as e:
            logger.error(f"Failed to launch persistent context (Browser likely open): {e}")
            logger.warning("Falling back to new temporary context (User likely needs to login)")
            # Fallback: Launch a new instance (incognito-ish)
            browser = await browser_type.launch(headless=HEADLESS, channel="chrome")
            context = await browser.new_context()
            page = await context.new_page()
        else:
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
        try:
            await page.goto(linkedin_url)
            await page.wait_for_load_state("domcontentloaded")
            
            # --- CONNECTION LOGIC ---
            
            # 0. Check for Login
            try:
                # If we see a "Sign in" button or similar, pause for user
                # Common LinkedIn login indicators
                login_indicators = [
                    'a[href*="login"]',
                    'button:has-text("Sign in")', 
                    'input[id="username"]'
                ]
                
                needs_login = False
                for indicator in login_indicators:
                    if await page.locator(indicator).first.is_visible():
                        needs_login = True
                        break
                
                if needs_login or "login" in page.url:
                    logger.warning("User appears to be logged out. Waiting for manual login...")
                    # Wait for a long time to let user log in
                    # We can loop and check for "Feed" or "Me" icon
                    # Wait up to 3 minutes for login
                    try:
                        await page.wait_for_selector('div.feed-identity-module', timeout=180000) 
                        logger.info("Login detected! Proceeding...")
                    except:
                        logger.error("Login timeout. Please log in to LinkedIn in the automation window.")
                        return {"status": "login_required"}

            except Exception as e:
                logger.info(f"Check login status check ignored: {e}")

            # 1. Check if "Pending" (Already sent)
            pending_btn = page.locator('button:has-text("Pending")').first
            if await pending_btn.is_visible():
                logger.info("Connection already pending. Stopping.")
                return {"status": "pending"}

            # 2. Try Primary Connect Button
            connect_btn = page.locator('button:has-text("Connect")').first
            clicked_connect = False
            
            if await connect_btn.is_visible():
                await connect_btn.click()
                clicked_connect = True
                logger.info("Clicked primary Connect button")
            else:
                # 3. Try "More" -> "Connect"
                more_btn = page.locator('button[aria-label="More actions"]').first 
                # LinkedIn "More" button often has aria-label or just text "More"
                if await more_btn.is_visible():
                    await more_btn.click()
                    # Wait for dropdown
                    dropdown_connect = page.locator('div[role="button"]:has-text("Connect")').first
                    # Also try strictly "Connect" text item
                    if not await dropdown_connect.is_visible():
                         dropdown_connect = page.locator('span:has-text("Connect")').first

                    if await dropdown_connect.is_visible():
                        await dropdown_connect.click()
                        clicked_connect = True
                        logger.info("Clicked Connect via More dropdown")
                    else:
                        logger.warning("Could not find Connect button in More dropdown")
                else:
                    logger.warning("Could not find Connect button or More button")

            # --- ADD NOTE LOGIC ---
            
            if clicked_connect:
                # Wait for modal "Add a note"
                add_note_btn = page.locator('button:has-text("Add a note")')
                # Wait up to 3s
                try:
                    await add_note_btn.wait_for(state="visible", timeout=3000)
                    await add_note_btn.click()
                    logger.info("Clicked 'Add a note'")
                    
                    # Type Message
                    text_area = page.locator('textarea[name="message"]')
                    if await text_area.is_visible():
                        await text_area.fill(message_text)
                        logger.info("Message pasted. WAITING for user review.")
                        
                        # IMPORTANT: We stop here.
                        # We keep the browser open for a bit so user sees it?
                        # Or we detach? Playwright kills process on close.
                        # We will wait 300 seconds (5 mins) as a "Review Window"
                        logger.info("WAITING 5 MINUTES for User Review. Close browser manually if done earlier.")
                        await asyncio.sleep(300) 
                        return {"status": "pasted"}
                        
                except Exception as e:
                     logger.error(f"Error in Add Note flow: {e}")
                     # Maybe it went straight to "Send"? (Rare for Connect)
            
            return {"status": "done_manual_check_required"}

        finally:
            # Cleanup
            # In a real tool, maybe we don't close so aggressively?
            try:
                await browser.close()
            except:
                pass
