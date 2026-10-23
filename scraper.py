import asyncio
from playwright.async_api import async_playwright
import os
import re

async def main():
    async with async_playwright() as p:
        # Launch browser with stealth settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920x1080'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        page = await context.new_page()
        
        try:
            print("Navigating to site...")
            await page.goto("https://freeiptv2023-d.ottc.xyz/?action=view", 
                          wait_until="domcontentloaded", 
                          timeout=30000)
            
            # Wait for Cloudflare Turnstile
            print("Waiting for Cloudflare...")
            await page.wait_for_timeout(5000)
            
            # Try to find and click the button
            print("Looking for Create button...")
            
            # Multiple selectors to try
            selectors = [
                "button:has-text('Create Free IPTV')",
                "button:has-text('Create')",
                "input[type='submit']",
                "button[type='submit']",
                "a:has-text('Create')",
                "[class*='create']"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        await element.click()
                        print(f"Clicked using selector: {selector}")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                print("Could not find button. Taking screenshot for debugging...")
                await page.screenshot(path="debug_screenshot.png")
                # Save HTML for debugging
                content = await page.content()
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                return
            
            # Wait for credentials to appear
            print("Waiting for credentials...")
            await page.wait_for_timeout(6000)
            
            # Get page content
            content = await page.content()
            
            # Extract credentials
            match = re.search(r'username=(\d+)&password=(\d+)', content)
            
            if match:
                username = match.group(1)
                password = match.group(2)
                print(f"Success! User: {username}, Pass: {password}")
                
                # Fetch M3U
                import urllib.request
                m3u_url = f"http://freeiptv.ottc.xyz:80/get.php?username={username}&password={password}&type=m3u_plus&output=ts"
                
                req = urllib.request.Request(m3u_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    playlist_data = response.read().decode('utf-8')
                
                with open("playlist.m3u", "w", encoding="utf-8") as f:
                    f.write(playlist_data)
                print("Saved playlist.m3u!")
            else:
                print("No credentials found. Saving debug files...")
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
