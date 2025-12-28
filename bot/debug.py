#!/usr/bin/env python3
"""
Debug: Get correct building IDs from the game by checking empty slot options.
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
        
        # Find an empty building slot
        print("\n=== SCANNING FOR EMPTY SLOT ===")
        empty_slot = None
        for pos in range(19, 41):
            response = await client.get(f"{SERVER_URL}/build.php?id={pos}")
            if 'construction of a new building' in response.text.lower():
                empty_slot = pos
                print(f"Found empty slot at position {pos}")
                break
        
        if not empty_slot:
            print("No empty slots found!")
            return
        
        # Get the list of buildings we can construct
        print(f"\n=== AVAILABLE BUILDINGS AT SLOT {empty_slot} ===")
        response = await client.get(f"{SERVER_URL}/build.php?id={empty_slot}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for inspection
        with open('/tmp/empty_slot.html', 'w') as f:
            f.write(response.text)
        print("[Saved /tmp/empty_slot.html]")
        
        # Find all building options - usually in a table or list with links
        # The link format is typically: build.php?id=X&b=Y where Y is the building type ID
        print("\nLooking for build links (build.php?id=X&b=Y)...")
        
        build_links = soup.find_all('a', href=lambda x: x and '&b=' in str(x))
        print(f"Found {len(build_links)} build links\n")
        
        print(f"{'ID':<5} {'Building Name':<30}")
        print("-" * 40)
        
        buildings_found = {}
        for link in build_links:
            href = link.get('href', '')
            # Extract building ID from href like "build.php?id=25&b=19"
            if '&b=' in href:
                bid = href.split('&b=')[1].split('&')[0]
                # Get building name - usually in the parent or nearby element
                name = link.text.strip() or link.get('title', '') or 'Unknown'
                # Clean up name
                name = name.replace('\n', ' ').strip()
                if name and bid not in buildings_found:
                    buildings_found[bid] = name
                    print(f"{bid:<5} {name[:30]:<30}")
        
        # Also check for onclick or data attributes
        if not buildings_found:
            print("\nNo &b= links found. Checking other patterns...")
            
            # Check for contract building divs
            contracts = soup.find_all('div', class_='contractBuilding')
            for contract in contracts:
                title = contract.find(class_='title') or contract.find('h2')
                if title:
                    print(f"Contract: {title.text.strip()}")
        
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
