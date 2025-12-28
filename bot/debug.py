#!/usr/bin/env python3
"""
Debug: Resource field upgrade on Netus.
"""

import asyncio
import httpx
from bs4 import BeautifulSoup

INITIAL_BASE_URL = "https://gotravspeed.com"
SERVER_URL = "https://netus.gotravspeed.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
}


async def main():
    username = "abaddon"
    password = "bristleback"
    server_id = 32
    
    print("Logging into Netus...")
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, headers=HEADERS) as client:
        await client.get(INITIAL_BASE_URL)
        await client.post(INITIAL_BASE_URL, data={'name': username, 'password': password})
        await client.get(INITIAL_BASE_URL + "/game/servers")
        await client.post(INITIAL_BASE_URL + "/game/servers", data={'action': 'server', 'value': str(server_id)})
        await client.post(INITIAL_BASE_URL + "/game/servers", data={'action': 'serverLogin', 'value[pid]': str(server_id), 'value[server]': str(server_id)})
        
        # Get village1.php to see resource fields
        print("\nFetching resource fields...")
        response = await client.get(SERVER_URL + "/village1.php")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for map areas
        map_div = soup.find('div', id='village_map')
        if map_div:
            areas = map_div.find_all('area')
            print(f"Found {len(areas)} map areas")
            for area in areas[:5]:
                print(f"  {area.get('href', '')} - {area.get('title', '')[:40]}")
        else:
            print("No village_map div found")
        
        # Try build.php?id=1 directly
        print("\n--- Checking build.php?id=1 ---")
        response = await client.get(SERVER_URL + "/build.php?id=1")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title')
        print(f"Page title: {title.text if title else 'N/A'}")
        
        # Find building/field name
        h1 = soup.find('h1')
        print(f"H1: {h1.text if h1 else 'N/A'}")
        
        # Find current level
        level_span = soup.find('span', class_='level')
        print(f"Level: {level_span.text if level_span else 'N/A'}")
        
        # Find upgrade link
        build_link = soup.find('a', class_='build')
        if build_link:
            print(f"\n✅ Found upgrade link: {build_link.get('href', '')}")
            print(f"   Text: {build_link.text.strip()[:50]}")
        else:
            print("\n❌ No 'a.build' link found")
            
            # Look for other build options
            all_builds = soup.find_all('a', href=lambda x: x and 'k=' in str(x))
            if all_builds:
                print(f"   Found {len(all_builds)} links with k= (CSRF):")
                for b in all_builds[:3]:
                    print(f"     {b.get('href', '')[:60]}")
        
        # Check for build button (green)
        green_btn = soup.find('button', class_='green') or soup.find('a', class_='green')
        if green_btn:
            print(f"\n✅ Found green button: {green_btn.text.strip()[:40]}")
        
        # Check for construction section
        contract = soup.find('div', class_='contractBuilding') or soup.find('div', id='contract')
        if contract:
            print("\nContract/build section found")
            links = contract.find_all('a')
            for l in links[:3]:
                print(f"  {l.get('href', '')[:60]} - {l.text.strip()[:30]}")
        
        # Save HTML for inspection
        with open('/tmp/build_id1.html', 'w') as f:
            f.write(response.text)
        print("\n[Saved to /tmp/build_id1.html]")


if __name__ == "__main__":
    asyncio.run(main())
