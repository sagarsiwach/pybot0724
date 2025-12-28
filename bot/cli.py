#!/usr/bin/env python3
"""
Travian Bot - Minimal Keyboard CLI
Clean, minimal keyboard-only interface.
"""

import asyncio
import httpx
import os
import sys
from bs4 import BeautifulSoup
from datetime import datetime

# Suppress logging noise
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE_URL = "https://fun.gotravspeed.com"


def clear():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_number(num_str: str) -> str:
    """Format large numbers."""
    try:
        num = int(num_str)
        if num >= 1_000_000_000_000_000_000:
            return f"{num / 1_000_000_000_000_000_000:.2f}Q"
        elif num >= 1_000_000_000_000_000:
            return f"{num / 1_000_000_000_000_000:.2f}Qa"
        elif num >= 1_000_000_000_000:
            return f"{num / 1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.2f}K"
        return str(num)
    except:
        return num_str


class TravianCLI:
    def __init__(self):
        self.session_manager = None
        self.cookies = None
        self.conn = None
        self.username = None
        self.villages = []
        self.current_village = None
        self.resources = {}
        
    async def login(self, username: str, password: str):
        """Login to the game."""
        from bot.database import init_db
        from bot.session_manager import SessionManager
        
        self.conn = init_db()
        self.username = username
        self.session_manager = SessionManager(username, password, "roman", self.conn)
        self.cookies = await self.session_manager.login()
        
        if self.cookies:
            await self.fetch_villages()
            if self.villages:
                self.current_village = self.villages[0]
            await self.fetch_resources()
            return True
        return False
    
    async def fetch_villages(self):
        """Fetch all villages."""
        async with httpx.AsyncClient(cookies=self.cookies) as client:
            response = await client.get(f"{BASE_URL}/profile.php")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            self.villages = []
            village_table = soup.find('table', {'id': 'villages'})
            if village_table:
                rows = village_table.find('tbody').find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    name = cols[0].text.strip()
                    link = row.find('a')
                    vid = link['href'].split('=')[-1] if link else '0'
                    coords = cols[4].text.strip()[1:-1].split('|')
                    x, y = int(coords[0]), int(coords[1])
                    self.villages.append({'name': name, 'id': vid, 'x': x, 'y': y})
    
    async def fetch_resources(self):
        """Fetch current resources."""
        async with httpx.AsyncClient(cookies=self.cookies) as client:
            response = await client.get(f"{BASE_URL}/village1.php")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            res_div = soup.find('div', id='res')
            if res_div:
                for res_type in ['wood', 'clay', 'iron', 'crop']:
                    elem = res_div.find('div', class_=res_type)
                    self.resources[res_type] = elem.text.strip() if elem else '0'
                
                ware = res_div.find('div', class_='ware')
                gran = res_div.find('div', class_='gran')
                self.resources['warehouse'] = ware.text.strip() if ware else '0'
                self.resources['granary'] = gran.text.strip() if gran else '0'
    
    async def fetch_resource_fields(self):
        """Fetch resource fields (positions 1-18) with levels."""
        fields = []
        async with httpx.AsyncClient(cookies=self.cookies) as client:
            response = await client.get(f"{BASE_URL}/village1.php")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse resource field map
            map_div = soup.find('div', id='village_map')
            if map_div:
                for area in map_div.find_all('area'):
                    href = area.get('href', '')
                    title = area.get('title', '')
                    if 'id=' in href:
                        pos = int(href.split('id=')[1].split('&')[0])
                        if pos <= 18:
                            # Parse title for name and level
                            name = title.split(' level')[0] if ' level' in title else title
                            level = '0'
                            if 'level ' in title:
                                level = title.split('level ')[1].split()[0]
                            fields.append({'pos': pos, 'name': name, 'level': level})
        
        return sorted(fields, key=lambda x: x['pos'])
    
    async def fetch_buildings(self):
        """Fetch buildings (positions 19-40) with levels."""
        buildings = []
        async with httpx.AsyncClient(cookies=self.cookies) as client:
            response = await client.get(f"{BASE_URL}/village2.php")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse building map
            map_div = soup.find('div', id='village_map')
            if map_div:
                for area in map_div.find_all('area'):
                    href = area.get('href', '')
                    title = area.get('title', '')
                    if 'id=' in href:
                        pos = int(href.split('id=')[1].split('&')[0])
                        if pos > 18:
                            name = title.split(' level')[0] if ' level' in title else title
                            level = '0'
                            if 'level ' in title:
                                level = title.split('level ')[1].split()[0]
                            buildings.append({'pos': pos, 'name': name, 'level': level})
        
        return sorted(buildings, key=lambda x: x['pos'])
    
    async def switch_village(self, village_id: str):
        """Switch to a different village."""
        async with httpx.AsyncClient(cookies=self.cookies) as client:
            await client.get(f"{BASE_URL}/village1.php?newdid={village_id}")
        # Update current village
        for v in self.villages:
            if v['id'] == village_id:
                self.current_village = v
                break
        await self.fetch_resources()
    
    async def upgrade_resource(self, position: int, loops: int = 1):
        """Upgrade a resource field."""
        from bot.construction import build_or_upgrade_resource
        await build_or_upgrade_resource(self.cookies, position, loops)
    
    async def upgrade_building(self, position: int, building_id: int, loops: int = 1):
        """Upgrade a building."""
        from bot.construction import construct_and_upgrade_building
        await construct_and_upgrade_building(self.cookies, position, building_id, loops)
    
    def print_header(self):
        """Print minimal header."""
        print("=" * 60)
        print(f"  TRAVIAN BOT | {self.username or 'Not logged in'}")
        if self.current_village:
            print(f"  Village: {self.current_village['name']} ({self.current_village['x']}|{self.current_village['y']})")
        print("=" * 60)
    
    def print_resources(self):
        """Print resource bar."""
        if self.resources:
            print(f"\n  Wood: {format_number(self.resources.get('wood', '0')):>10} | "
                  f"Clay: {format_number(self.resources.get('clay', '0')):>10} | "
                  f"Iron: {format_number(self.resources.get('iron', '0')):>10} | "
                  f"Crop: {format_number(self.resources.get('crop', '0')):>10}")
            print(f"  Warehouse: {format_number(self.resources.get('warehouse', '0')):>10} | "
                  f"Granary: {format_number(self.resources.get('granary', '0')):>10}")
        print()
    
    async def main_menu(self):
        """Main menu loop."""
        while True:
            clear()
            self.print_header()
            self.print_resources()
            
            print("  [1] Production")
            print("  [2] Storage")
            print("  [3] Resource Fields")
            print("  [4] Buildings")
            print("  [5] Village Selection")
            print("  [6] View Village Details")
            print("  [7] Research Academy")
            print("  [8] Upgrade Armory")
            print("  [9] Upgrade Smithy")
            print("  [r] Refresh")
            print("  [q] Quit")
            print()
            
            choice = input("  > ").strip().lower()
            
            if choice == '1':
                await self.production_menu()
            elif choice == '2':
                await self.storage_menu()
            elif choice == '3':
                await self.resource_fields_menu()
            elif choice == '4':
                await self.buildings_menu()
            elif choice == '5':
                await self.village_selection_menu()
            elif choice == '6':
                await self.village_details_menu()
            elif choice == '7':
                await self.research_academy()
            elif choice == '8':
                await self.upgrade_armory()
            elif choice == '9':
                await self.upgrade_smithy()
            elif choice == 'r':
                await self.fetch_resources()
            elif choice == 'q':
                print("\n  Goodbye!")
                break
    
    async def production_menu(self):
        """Production increase menu."""
        clear()
        self.print_header()
        print("\n  PRODUCTION INCREASE")
        print("  " + "-" * 40)
        
        loops = input("  Number of loops [10]: ").strip()
        loops = int(loops) if loops.isdigit() else 10
        
        print(f"\n  Running {loops} production increases...")
        print("  (Note: May not work due to anti-bot protection)")
        
        from bot.production import increase_production_async
        from bot.database import init_db
        conn = init_db()
        await increase_production_async(self.username, "", loops, conn, self.cookies)
        
        await self.fetch_resources()
        input("\n  Press Enter to continue...")
    
    async def storage_menu(self):
        """Storage increase menu."""
        clear()
        self.print_header()
        print("\n  STORAGE INCREASE")
        print("  " + "-" * 40)
        
        loops = input("  Number of loops [10]: ").strip()
        loops = int(loops) if loops.isdigit() else 10
        
        print(f"\n  Running {loops} storage increases...")
        print("  (Note: May not work due to anti-bot protection)")
        
        from bot.storage import increase_storage_async
        from bot.database import init_db
        conn = init_db()
        await increase_storage_async(self.username, "", loops, conn, self.cookies)
        
        await self.fetch_resources()
        input("\n  Press Enter to continue...")
    
    async def resource_fields_menu(self):
        """Resource fields view and upgrade."""
        while True:
            clear()
            self.print_header()
            print("\n  RESOURCE FIELDS")
            print("  " + "-" * 50)
            
            fields = await self.fetch_resource_fields()
            
            print(f"\n  {'Pos':<5} {'Type':<20} {'Level':<10}")
            print("  " + "-" * 40)
            for f in fields:
                print(f"  {f['pos']:<5} {f['name']:<20} {f['level']:<10}")
            
            print("\n  Enter position to upgrade, or [b] to go back")
            choice = input("  > ").strip().lower()
            
            if choice == 'b':
                break
            elif choice.isdigit():
                pos = int(choice)
                loops = input(f"  Upgrade loops for position {pos} [1]: ").strip()
                loops = int(loops) if loops.isdigit() else 1
                print(f"\n  Upgrading position {pos} ({loops} times)...")
                await self.upgrade_resource(pos, loops)
                print("  Done!")
                await asyncio.sleep(1)
    
    async def buildings_menu(self):
        """Buildings view and upgrade."""
        while True:
            clear()
            self.print_header()
            print("\n  BUILDINGS")
            print("  " + "-" * 50)
            
            buildings = await self.fetch_buildings()
            
            print(f"\n  {'Pos':<5} {'Building':<25} {'Level':<10}")
            print("  " + "-" * 45)
            for b in buildings:
                print(f"  {b['pos']:<5} {b['name']:<25} {b['level']:<10}")
            
            print("\n  Enter position to upgrade, or [b] to go back")
            choice = input("  > ").strip().lower()
            
            if choice == 'b':
                break
            elif choice.isdigit():
                pos = int(choice)
                # For buildings, we need building ID - simplified here
                loops = input(f"  Upgrade loops for position {pos} [1]: ").strip()
                loops = int(loops) if loops.isdigit() else 1
                print(f"\n  Upgrading position {pos} ({loops} times)...")
                await self.upgrade_building(pos, 0, loops)  # building_id=0 for existing buildings
                print("  Done!")
                await asyncio.sleep(1)
    
    async def village_selection_menu(self):
        """Village selection."""
        while True:
            clear()
            self.print_header()
            print("\n  VILLAGE SELECTION")
            print("  " + "-" * 50)
            
            for i, v in enumerate(self.villages, 1):
                marker = " *" if v == self.current_village else ""
                print(f"  [{i}] {v['name']} ({v['x']}|{v['y']}){marker}")
            
            print("\n  Enter number to switch, or [b] to go back")
            choice = input("  > ").strip().lower()
            
            if choice == 'b':
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.villages):
                    print(f"\n  Switching to {self.villages[idx]['name']}...")
                    await self.switch_village(self.villages[idx]['id'])
                    break
    
    async def village_details_menu(self):
        """Show detailed village info."""
        clear()
        self.print_header()
        print("\n  VILLAGE DETAILS")
        print("  " + "-" * 50)
        
        print("\n  --- Resource Fields ---")
        fields = await self.fetch_resource_fields()
        for f in fields:
            print(f"  [{f['pos']:>2}] {f['name']:<15} Lv.{f['level']}")
        
        print("\n  --- Buildings ---")
        buildings = await self.fetch_buildings()
        for b in buildings:
            if b['name'] and b['name'] != 'Empty':
                print(f"  [{b['pos']:>2}] {b['name']:<20} Lv.{b['level']}")
        
        input("\n  Press Enter to continue...")
    
    async def research_academy(self):
        """Research in Academy."""
        clear()
        self.print_header()
        print("\n  RESEARCHING IN ACADEMY...")
        
        from bot.construction import research_academy
        await research_academy(self.session_manager)
        
        input("\n  Press Enter to continue...")
    
    async def upgrade_armory(self):
        """Upgrade in Armory."""
        clear()
        self.print_header()
        print("\n  UPGRADING IN ARMORY...")
        
        from bot.construction import upgrade_armory
        await upgrade_armory(self.session_manager)
        
        input("\n  Press Enter to continue...")
    
    async def upgrade_smithy(self):
        """Upgrade in Smithy."""
        clear()
        self.print_header()
        print("\n  UPGRADING IN SMITHY...")
        
        from bot.construction import upgrade_smithy
        await upgrade_smithy(self.session_manager)
        
        input("\n  Press Enter to continue...")


async def main():
    """Main entry point."""
    clear()
    print("=" * 60)
    print("  TRAVIAN BOT - Minimal CLI")
    print("=" * 60)
    print()
    
    cli = TravianCLI()
    
    # Login
    username = input("  Username: ").strip()
    password = input("  Password: ").strip()
    
    print("\n  Logging in...")
    
    try:
        if await cli.login(username, password):
            print("  Login successful!")
            await asyncio.sleep(1)
            await cli.main_menu()
        else:
            print("\n  Login failed!")
            print("  Possible causes:")
            print("    - Invalid username/password")
            print("    - Server is down or unreachable")
            print("    - Network connection issue")
            print("\n  Please try again later.")
    except Exception as e:
        print(f"\n  Error: {e}")
        print("  Please check your network connection and try again.")


def run():
    """Entry point for package."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Goodbye!")


if __name__ == "__main__":
    run()

