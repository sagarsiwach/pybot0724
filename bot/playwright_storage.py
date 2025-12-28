#!/usr/bin/env python3
"""
Playwright-based storage increase using real browser clicks.
"""

import asyncio
from playwright.async_api import async_playwright


async def main():
    username = "abaddon"
    password = "bristleback"
    loops = 5
    
    print(f"🚀 Playwright Storage Bot")
    print(f"   User: {username}")
    print(f"   Loops: {loops}")
    print("-" * 50)
    
    async with async_playwright() as p:
        # Launch browser with fixed viewport
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        # Step 1: Login
        print("🔐 Logging in...")
        await page.goto("https://gotravspeed.com")
        await page.wait_for_load_state('networkidle')
        
        await page.fill('input[name="name"]', username)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"], input[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        # Step 2: Select server via POST
        print("🎮 Selecting server...")
        await page.goto("https://gotravspeed.com/game/servers")
        await page.wait_for_load_state('networkidle')
        
        # Send server selection request
        await page.evaluate('''() => {
            fetch('/game/servers', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'action=server&value=9'
            });
        }''')
        await page.wait_for_timeout(500)
        
        # Server login
        await page.evaluate('''() => {
            fetch('/game/servers', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'action=serverLogin&value[pid]=9&value[server]=9'
            });
        }''')
        await page.wait_for_timeout(1000)
        
        # Go to game
        await page.goto("https://fun.gotravspeed.com/village1.php")
        await page.wait_for_load_state('networkidle')
        
        # Check if logged in
        if "village1.php" in page.url or "fun.gotravspeed.com" in page.url:
            print("✅ Login successful!")
        else:
            print(f"❌ Login may have failed. Current URL: {page.url}")
            # Screenshot for debugging
            await page.screenshot(path="debug_login.png")
            print("   Screenshot saved to debug_login.png")
        
        # Step 3: Loop storage increase
        for i in range(loops):
            print(f"\n--- Request {i+1}/{loops} ---")
            
            # Go to storage shop
            await page.goto("https://fun.gotravspeed.com/buy2.php?t=2")
            await page.wait_for_load_state('networkidle')
            
            # Check if we got the shop page
            key_input = page.locator('input[name="key"]')
            if await key_input.count() == 0:
                print("❌ Shop page not loaded correctly")
                await page.screenshot(path=f"debug_shop_{i}.png")
                continue
            
            key_before = await key_input.get_attribute('value')
            print(f"🔑 Key: {key_before}")
            
            # Select the 8Q option (value=4)
            await page.click('input[value="4"]')
            
            # Select 100x multiplier
            await page.select_option('select[name="xor"]', '100')
            
            # Wait for button to appear (there's a 700ms delay in the JS)
            await page.wait_for_timeout(800)
            
            # Click the submit button - this fills in key_x and key_y automatically!
            await page.click('#sendbutton')
            
            # Wait for response
            await page.wait_for_load_state('networkidle')
            
            # Check for success
            success = page.locator('span.succes')
            if await success.count() > 0:
                success_text = await success.text_content()
                print(f"✅ SUCCESS: {success_text[:60]}...")
            else:
                # Check new key
                new_key_input = page.locator('input[name="key"]')
                if await new_key_input.count() > 0:
                    key_after = await new_key_input.get_attribute('value')
                    if key_after != key_before:
                        print(f"✅ Key changed: {key_before} → {key_after}")
                    else:
                        print(f"❌ Failed - key unchanged")
                else:
                    print("⚠️ No key input found in response")
        
        await browser.close()
        print("\n" + "-" * 50)
        print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
