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
            
            # Wait for Cloudflare Turnstile (if any)
            print("Waiting for page to load...")
            await page.wait_for_timeout(3000)
            
            # Wait for the button to be unlocked (page says 5 seconds)
            print("Waiting for button to unlock (5 seconds)...")
            await page.wait_for_timeout(7000)  # Wait 7 seconds to be safe
            
            # Try to find and click the button with EXACT text
            print("Looking for 'Create free IPTV account !' button...")
            
            try:
                # Wait for button to be clickable
                button = page.locator("button:has-text('Create free IPTV account !')").first
                await button.wait_for(state='visible', timeout=10000)
                await button.wait_for(state='enabled', timeout=10000)
                await button.click()
                print("Button clicked successfully!")
            except Exception as e:
                print(f"Button click failed: {e}")
                # Try alternative selectors
                try:
                    button = page.locator("button[type='submit']").first
                    await button.click()
                    print("Clicked using type='submit' selector")
                except:
                    print("Could not find any button. Taking screenshot...")
                    await page.screenshot(path="debug_screenshot.png")
                    content = await page.content()
                    with open("debug.html", "w", encoding="utf-8") as f:
                        f.write(content)
                    return
            
            # Wait for credentials to appear after clicking
            print("Waiting for credentials to generate...")
            await page.wait_for_timeout(8000)  # Wait for page to update
            
            # Get page content
            content = await page.content()
            
            # Save HTML for debugging
            with open("debug_after_click.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Extract credentials - look for the M3U link pattern
            print("Searching for credentials in page...")
            match = re.search(r'username=(\d+)&password=(\d+)', content)
            
            if match:
                username = match.group(1)
                password = match.group(2)
                print(f"✓ Success! Found credentials:")
                print(f"  Username: {username}")
                print(f"  Password: {password}")
                
                # Fetch M3U playlist
                import urllib.request
                m3u_url = f"http://freeiptv.ottc.xyz:80/get.php?username={username}&password={password}&type=m3u_plus&output=ts"
                
                print(f"Fetching M3U from: {m3u_url}")
                req = urllib.request.Request(m3u_url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    with urllib.request.urlopen(req, timeout=15) as response:
                        playlist_data = response.read().decode('utf-8')
                    
                    if playlist_data and len(playlist_data) > 100:
                        with open("playlist.m3u", "w", encoding="utf-8") as f:
                            f.write(playlist_data)
                        print(f"✓ Saved playlist.m3u ({len(playlist_data)} bytes)")
                    else:
                        print("✗ M3U response was empty or too short")
                        return
                except Exception as e:
                    print(f"✗ Failed to fetch M3U: {e}")
                    return
            else:
                print("✗ No credentials found in page source")
                print("Looking for username/password fields...")
                
                # Try to find credentials in input fields
                user_field = page.locator("input[value]").all()
                for field in user_field:
                    value = await field.get_attribute("value")
                    if value and len(value) > 10:
                        print(f"Found field value: {value[:20]}...")
                    
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
