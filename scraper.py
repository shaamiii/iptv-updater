import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        # Launch a real browser in the cloud
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("Navigating to site...")
            await page.goto("https://freeiptv2023-d.ottc.xyz/?action=view", wait_until="networkidle")
            
            # Wait for Cloudflare Turnstile to initialize
            await page.wait_for_timeout(4000)
            
            print("Clicking the generate button...")
            # Click the button (adjust text if needed)
            await page.get_by_role("button", name="Create Free IPTV").click()
            
            # Wait for the page to update with new credentials
            await page.wait_for_timeout(5000)
            
            # Get the page HTML
            content = await page.content()
            
            # Extract the username and password using regex
            import re
            match = re.search(r'username=(\d+)&password=(\d+)', content)
            
            if match:
                username = match.group(1)
                password = match.group(2)
                print(f"Success! Found User: {username}, Pass: {password}")
                
                # Construct the direct M3U link
                m3u_url = f"http://freeiptv.ottc.xyz:80/get.php?username={username}&password={password}&type=m3u_plus&output=ts"
                
                # Fetch the actual playlist content
                import urllib.request
                req = urllib.request.Request(m3u_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    playlist_data = response.read().decode('utf-8')
                
                # Save to file
                with open("playlist.m3u", "w", encoding="utf-8") as f:
                    f.write(playlist_data)
                print("Saved playlist.m3u successfully!")
            else:
                print("Failed to find credentials. Saving debug HTML.")
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
