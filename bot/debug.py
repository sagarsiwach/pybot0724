#!/usr/bin/env python3
"""
Test: Re-login for each request.
"""

import asyncio
import httpx
import random
from bs4 import BeautifulSoup
from bot.session_manager import SessionManager
from bot.database import init_db


async def main():
    username = "abaddon"
    password = "bristleback"
    
    print("=" * 60)
    print("TESTING WITH FRESH LOGIN EACH TIME")
    print("=" * 60)
    
    conn = init_db()
    success = 0
    
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://fun.gotravspeed.com',
        'Referer': 'https://fun.gotravspeed.com/buy2.php?t=2',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    print(f"\n{'#':<3} {'Status':<6} {'Key':<8} {'Result'}")
    print("-" * 40)
    
    for i in range(5):
        # Fresh login each time
        session_manager = SessionManager(username, password, "roman", conn)
        cookies = await session_manager.login()
        
        if not cookies:
            print(f"{i+1:<3} -      -        ❌ Login failed")
            continue
        
        async with httpx.AsyncClient(cookies=cookies, headers=headers, follow_redirects=False) as client:
            # Get key
            response = await client.get("https://fun.gotravspeed.com/buy2.php?t=2")
            soup = BeautifulSoup(response.text, 'html.parser')
            key_input = soup.find('input', {'name': 'key'})
            key = key_input['value'] if key_input else 'N/A'
            
            # Random coordinates
            x = random.randint(710, 730)
            y = random.randint(578, 590)
            
            data = {
                'selected_res': '4',
                'xor': '100',
                'key_x': str(x),
                'key_y': str(y),
                'key': key
            }
            
            response = await client.post(
                "https://fun.gotravspeed.com/buy2.php?t=2&Shop=done",
                data=data
            )
            
            status = response.status_code
            
            if status == 302:
                result = "✅ 302!"
                success += 1
            else:
                result = "❌ FAIL"
            
            print(f"{i+1:<3} {status:<6} {key:<8} {result}")
        
        await asyncio.sleep(0.5)
    
    print("-" * 40)
    print(f"\n📊 Success: {success}/5")


if __name__ == "__main__":
    asyncio.run(main())
