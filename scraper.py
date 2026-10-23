import asyncio
from playwright.async_api import async_playwright
import os
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920x1080'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US'
        )
        
        page = await context.new_page()
        
        try:
            print("Step 1: Navigating to site...")
            await page.goto("https://freeiptv2023-d.ottc.xyz/?action=view", 
                          wait_until="domcontentloaded", 
                          timeout=30000)
            
            # Take screenshot BEFORE clicking
            await page.screenshot(path="debug_screenshot.png")
            print("✓ Screenshot saved (before click)")
            
            print("Step 2: Waiting 7 seconds for button to unlock...")
            await page.wait_for_timeout(7000)
            
            print("Step 3: Looking for button...")
            
            # Try multiple button selectors
            button_clicked = False
            selectors_to_try = [
                "button:has-text('Create free IPTV account !')",
                "button:has-text('Create free IPTV account')",
                "button:has-text('Create')",
                "input[type='submit']",
                "button[type='submit']"
            ]
            
            for selector in selectors_to_try:
                try:
                    button = page.locator(selector).first
                    is_visible = await button.is_visible()
                    print(f"  Trying '{selector}' - visible: {is_visible}")
                    
                    if is_visible:
                        await button.click()
                        print(f"✓ Clicked button using: {selector}")
                        button_clicked = True
                        break
                except Exception as e:
                    print(f"  Failed with '{selector}': {e}")
                    continue
            
            if not button_clicked:
                print("✗ Could not find any button to click")
                content = await page.content()
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                return
            
            print("Step 4: Waiting 8 seconds for credentials to appear...")
            await page.wait_for_timeout(8000)
            
            # Take screenshot AFTER clicking
            await page.screenshot(path="debug_screenshot_after.png")
            print("✓ Screenshot saved (after click)")
            
            # Get page content after clicking
            content = await page.content()
            with open("debug_after_click.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("✓ HTML saved (after click)")
            
            print("Step 5: Searching for credentials...")
            match = re.search(r'username=(\d+)&password=(\d+)', content)
            
            if match:
                username = match.group(1)
                password = match.group(2)
                print(f"✓ Found credentials: User={username}, Pass={password}")
                
                # Fetch M3U
                import urllib.request
                m3u_url = f"http://freeiptv.ottc.xyz:80/get.php?username={username}&password={password}&type=m3u_plus&output=ts"
                print(f"  Fetching: {m3u_url}")
                
                req = urllib.request.Request(m3u_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    playlist_data = response.read().decode('utf-8')
                
                if len(playlist_data) > 100:
                    with open("playlist.m3u", "w", encoding="utf-8") as f:
                        f.write(playlist_data)
                    print(f"✓ Saved playlist.m3u ({len(playlist_data)} bytes)")
                else:
                    print(f"✗ M3U too short ({len(playlist_data)} bytes)")
            else:
                print("✗ No credentials found in HTML")
                # Try to find them in input fields
                inputs = await page.locator("input").all()
                for i, inp in enumerate(inputs):
                    val = await inp.get_attribute("value")
                    if val:
                        print(f"  Input {i}: {val[:50]}")
                    
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
