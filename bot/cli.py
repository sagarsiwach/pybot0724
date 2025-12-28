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


class TaskManager:
    """Manages background tasks and their logs."""
    def __init__(self):
        self.tasks = []  # List of (name, task_object, start_time)
        self.logs = []   # Global log buffer
    
    def add_task(self, name, coro):
        """Start a coroutine as a background task."""
        task = asyncio.create_task(coro)
        self.tasks.append({
            'name': name,
            'task': task,
            'start_time': datetime.now(),
            'status': 'Running'
        })
        task.add_done_callback(lambda t: self._task_done(t, name))
        return task
    
    def _task_done(self, task, name):
        """Callback when task finishes."""
        for t in self.tasks:
            if t['name'] == name:
                t['status'] = 'Done' if not task.cancelled() else 'Cancelled'
                # Log any exceptions
                try:
                    exc = task.exception()
                    if exc:
                        t['status'] = f'Error: {exc}'
                except:
                    pass
    
    def get_active_tasks(self):
        """Return list of running tasks."""
        # Cleanup old finished tasks (optional policy: keep them for history)
        return [t for t in self.tasks if t['status'] == 'Running']
    
    def log(self, msg):
        """Add to global log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {msg}")
        # Keep only last 50 logs
        if len(self.logs) > 50:
            self.logs.pop(0)


class TravianCLI:
    def __init__(self):
        self.session_manager = None
        self.cookies = None
        self.conn = None
        self.username = None
        self.server_id = 9
        self.server_name = "Fun"
        self.server_url = "https://fun.gotravspeed.com"
        self.villages = []
        self.current_village = None
        self.resources = {}
        self.tm = TaskManager()  # New TaskManager
        
    async def login(self, username: str, password: str, server_id: int = 9):
        """Login to the game."""
        from bot.database import init_db
        from bot.session_manager import SessionManager, SERVERS
        
        self.conn = init_db()
        self.username = username
        self.server_id = server_id
        server_info = SERVERS.get(server_id, SERVERS[9])
        self.server_name = server_info['name']
        self.server_url = server_info['url']
        
        self.session_manager = SessionManager(username, password, "roman", self.conn, server_id)
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
        from bot.session_manager import HEADERS
        
        async with httpx.AsyncClient(cookies=self.cookies, headers=HEADERS) as client:
            response = await client.get(f"{self.server_url}/profile.php")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            self.villages = []
            village_table = soup.find('table', {'id': 'villages'})
            
            if village_table:
                tbody = village_table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        # Handle different table formats
                        if len(cols) >= 5:
                            # Full format with coordinates
                            name = cols[0].text.strip()
                            link = row.find('a')
                            vid = link['href'].split('=')[-1] if link else '0'
                            try:
                                coords = cols[4].text.strip()[1:-1].split('|')
                                x, y = int(coords[0]), int(coords[1])
                            except:
                                x, y = 0, 0
                            self.villages.append({'name': name, 'id': vid, 'x': x, 'y': y})
                        elif len(cols) >= 1:
                            # Simple format (single village, beginner protection)
                            # Get village from sidebar instead
                            pass
            
            # If no villages found from table, try sidebar
            if not self.villages:
                # Get current village from village1.php
                response = await client.get(f"{self.server_url}/village1.php")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find village name from title or sidebar
                title = soup.find('title')
                village_name = title.text.split(' - ')[0] if title else 'Village'
                
                # Add default village
                self.villages.append({'name': village_name, 'id': '0', 'x': 0, 'y': 0})
    
    async def fetch_resources(self):
        """Fetch current resources."""
        from bot.session_manager import HEADERS
        
        async with httpx.AsyncClient(cookies=self.cookies, headers=HEADERS) as client:
            response = await client.get(f"{self.server_url}/village1.php")
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
        from bot.session_manager import HEADERS
        fields = []
        async with httpx.AsyncClient(cookies=self.cookies, headers=HEADERS) as client:
            response = await client.get(f"{self.server_url}/village1.php")
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
        from bot.session_manager import HEADERS
        buildings = []
        async with httpx.AsyncClient(cookies=self.cookies, headers=HEADERS) as client:
            response = await client.get(f"{self.server_url}/village2.php")
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
        from bot.session_manager import HEADERS
        async with httpx.AsyncClient(cookies=self.cookies, headers=HEADERS) as client:
            await client.get(f"{self.server_url}/village1.php?newdid={village_id}")
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
    
    async def main_menu(self):
        """Main interaction loop."""
        while True:
            clear()
            self.print_dashboard()  # Use new dashboard view
            
            print("\n  COMMANDS")
            print("  [1] Production (Upgrade fields)")
            print("  [2] Storage/Granary")
            print("  [3] Resource Fields (View/Upgrade)")
            print("  [4] Buildings (View/Upgrade)")
            print("  [5] Village Selection")
            print("  [6] Train Troops")
            print("  [7] Find Empty Spots & Settle")
            print("  [l] Logs (View background task logs)")
            print("  [r] Refresh")
            print("  [q] Quit")
            
            cmd = input("\n  > ").strip().lower()
            
            if cmd == '1':
                # Simplified production increase (background)
                loops = input("  Loops [5]: ").strip()
                loops = int(loops) if loops.isdigit() else 5
                self.tm.add_task(f"Increase Production ({loops})", self.increase_production_task(loops))
                print(f"  Started production increase ({loops} loops) in background...")
                await asyncio.sleep(1)
                
            elif cmd == '2':
                # Storage increase (background)
                loops = input("  Loops [5]: ").strip()
                loops = int(loops) if loops.isdigit() else 5
                self.tm.add_task(f"Increase Storage ({loops})", self.increase_storage_task(loops))
                print(f"  Started storage increase ({loops} loops) in background...")
                await asyncio.sleep(1)
                
            elif cmd == '3':
                await self.resource_fields_menu()
            elif cmd == '4':
                await self.buildings_menu()
            elif cmd == '5':
                await self.village_selection_menu()
            elif cmd == '6':
                await self.troop_training_menu()
            elif cmd == '7':
                await self.settling_menu()
            elif cmd == 'l':  # View logs
                await self.view_logs() 
            elif cmd == 'r':
                await self.fetch_resources()
            elif cmd == 'q':
                print("  Goodbye!")
                return
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
        """Resource fields upgrade - Background Task version."""
        clear()
        self.print_header()
        print("\n  RESOURCE FIELDS UPGRADE")
        print("  " + "-" * 50)
        
        # Show current levels
        # (This blocks briefly to fetch data, which is fine for UI responsiveness)
        print("\n  Fetching current levels...")
        from bot.construction import get_field_info, upgrade_all_resources, HEADERS
        
        async with httpx.AsyncClient(cookies=self.cookies, headers=HEADERS) as client:
            print(f"\n  {'Pos':<5} {'Type':<20} {'Level':<10}")
            print("  " + "-" * 40)
            for pos in range(1, 19):
                info = await get_field_info(client, self.server_url, pos)
                print(f"  {pos:<5} {info['name']:<20} {info['level']:<10}")
        
        print("\n  [Enter] Upgrade ALL to Level 30")
        print("  [b] Back")
        
        target = input("\n  Target Level [30]: ").strip()
        if target.lower() == 'b':
            return
            
        target = int(target) if target.isdigit() else 30
        
        # Define the background task
        async def task_wrapper():
            self.tm.log(f"Started upgrading all resources to Lv {target}")
            # We pass a callback to log progress to TaskManager
            await upgrade_all_resources(self.cookies, self.server_url, target, lambda msg: self.tm.log(msg))
            self.tm.log("Finished upgrading resources")

        self.tm.add_task(f"Upgrade Resources -> Lv {target}", task_wrapper())
        print(f"\n  Task started in background! Check Dashboard.")
        await asyncio.sleep(1.5)
    
    async def buildings_menu(self):
        """Buildings upgrade with presets - Background Task version."""
        clear()
        self.print_header()
        print("\n  VILLAGE BUILD MODE")
        print("  " + "-" * 50)
        
        from bot.presets import PRESETS, get_preset_summary
        from bot.construction import upgrade_all_buildings, upgrade_all_resources, HEADERS
        
        print("\n  [0] Standard Upgrade (upgrade all existing buildings)")
        print()
        print("  --- Build Presets ---")
        for pid, preset in PRESETS.items():
            res_info = f"Resources→{preset['resource_target']}" if preset['resource_target'] else "Resources→SKIP"
            print(f"  [{pid}] {preset['name']}")
            print(f"      {preset['description'][:50]}...")
            print(f"      {res_info} | {len(preset['buildings'])} buildings")
            print()
        
        print("  [d] Demolish (destroy a building)")
        print("  [b] Back")
        
        choice = input("\n  > ").strip().lower()
        if choice == 'b':
            return
        
        if choice == '0':
            # Standard upgrade - upgrade all existing buildings
            target = input("  Target Level [20]: ").strip()
            target = int(target) if target.isdigit() else 20
            
            async def standard_upgrade():
                self.tm.log(f"Standard upgrade: upgrading all buildings to Lv {target}")
                await upgrade_all_buildings(self.cookies, self.server_url, target, lambda msg: self.tm.log(msg))
                self.tm.log("Standard upgrade complete!")
            
            self.tm.add_task(f"Standard Upgrade → Lv {target}", standard_upgrade())
            print(f"\n  ✓ Standard upgrade started!")
            await asyncio.sleep(1.5)
            return
        
        if choice == 'd':
            await self.demolish_menu()
            return
            
        task_name = "Village Build"
        target_coro = None
        
        if choice in PRESETS:
            preset = PRESETS[choice]
            print(f"\n  ✓ Selected: {preset['name']}")
            print(f"    Resources: {'Level ' + str(preset['resource_target']) if preset['resource_target'] else 'SKIP'}")
            print(f"    Buildings: {len(preset['buildings'])} total")
            
            confirm = input("\n  Start build? [y/N]: ").strip().lower()
            if confirm != 'y':
                return
            
            task_name = f"Build: {preset['name']}"
            resource_target = preset['resource_target']
            
            async def preset_wrapper():
                self.tm.log(f"Started: {preset['name']}")
                
                # Step 1: Upgrade resource fields if target > 0
                if resource_target > 0:
                    self.tm.log(f"Upgrading resource fields to level {resource_target}...")
                    await upgrade_all_resources(self.cookies, self.server_url, resource_target, lambda msg: self.tm.log(msg))
                else:
                    self.tm.log("Skipping resource fields (Quick Settle mode)")
                
                # Step 2: Upgrade buildings to their target levels
                # For now, upgrade all existing buildings to level 20 (simplified)
                # TODO: Implement full preset-specific building construction
                self.tm.log("Upgrading buildings...")
                await upgrade_all_buildings(self.cookies, self.server_url, 20, lambda msg: self.tm.log(msg))
                
                self.tm.log(f"Finished: {preset['name']}")
            
            target_coro = preset_wrapper()
            
        elif choice == '5':
            target = input("  Target Level [20]: ").strip()
            target = int(target) if target.isdigit() else 20
            task_name = f"Upgrade Buildings → Lv {target}"
            
            async def all_wrapper():
                self.tm.log(f"Started upgrading all buildings to Lv {target}")
                await upgrade_all_buildings(self.cookies, self.server_url, target, lambda msg: self.tm.log(msg))
                self.tm.log("Finished upgrading buildings")
            
            target_coro = all_wrapper()
            
        else:
            print("  Invalid choice.")
            await asyncio.sleep(1)
            return

        self.tm.add_task(task_name, target_coro)
        print(f"\n  ✓ Task started in background!")
        print(f"    Check Dashboard or [l] Logs for progress.")
        await asyncio.sleep(2)
    
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

    async def demolish_menu(self):
        """Demolish/destroy a building."""
        clear()
        self.print_header()
        print("\n  DEMOLISH BUILDING")
        print("  " + "-" * 50)
        print("  WARNING: This will destroy a building!")
        
        # Show current buildings
        buildings = await self.fetch_buildings()
        print("\n  Current buildings:")
        for b in buildings:
            if b['name'] and b['name'] != 'Empty' and 'construction' not in b['name'].lower():
                print(f"  [{b['pos']:>2}] {b['name']:<20} Lv.{b['level']}")
        
        pos = input("\n  Enter building position to demolish (or 'b' to cancel): ").strip()
        if pos.lower() == 'b':
            return
        
        try:
            pos = int(pos)
            if pos < 19 or pos > 40:
                print("  Invalid position!")
                await asyncio.sleep(1)
                return
            
            confirm = input(f"  Demolish building at position {pos}? [y/N]: ").strip().lower()
            if confirm != 'y':
                return
            
            async def demolish_task():
                from bot.construction import demolish_building
                self.tm.log(f"Demolishing building at position {pos}...")
                success = await demolish_building(self.cookies, self.server_url, pos, lambda m: self.tm.log(m))
                if success:
                    self.tm.log(f"✓ Building at position {pos} demolished!")
                else:
                    self.tm.log(f"Failed to demolish building at {pos}")
            
            self.tm.add_task(f"Demolish pos {pos}", demolish_task())
            print(f"\n  ✓ Demolishing in background!")
            
        except ValueError:
            print("  Invalid position!")
        
        await asyncio.sleep(1.5)
    
    
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

    async def troop_training_menu(self):
        """Troop training menu."""
        clear()
        self.print_header()
        print("\n  TROOP TRAINING")
        print("  " + "-" * 50)
        
        print("\n  Select building:")
        print("  [1] Barracks (Infantry)")
        print("  [2] Stable (Cavalry)")
        print("  [3] Siege Workshop")
        print("  [4] Residence (Train Settlers)")
        print("  [b] Back")
        
        choice = input("\n  > ").strip().lower()
        if choice == 'b':
            return
        
        building_positions = {'1': 19, '2': 20, '3': 21, '4': 25}
        
        if choice not in building_positions:
            print("  Invalid choice.")
            await asyncio.sleep(1)
            return
        
        building_pos = building_positions[choice]
        
        # For settlers
        if choice == '4':
            count = input("  How many settlers? [3]: ").strip()
            count = int(count) if count.isdigit() else 3
            
            async def train_settlers_task():
                from bot.troop_training import train_settlers
                self.tm.log(f"Training {count} settlers...")
                await train_settlers(self.cookies, self.server_url, building_pos, count, lambda m: self.tm.log(m))
                self.tm.log("Settlers training queued!")
            
            self.tm.add_task(f"Train {count} Settlers", train_settlers_task())
            print(f"\n  ✓ Training {count} settlers in background!")
        else:
            # Regular troops
            troop_idx = input("  Troop type (1-6) [1]: ").strip()
            troop_idx = int(troop_idx) if troop_idx.isdigit() else 1
            
            loops = input("  Training loops [10]: ").strip()
            loops = int(loops) if loops.isdigit() else 10
            
            async def train_troops_task():
                from bot.troop_training import train_max_troops
                self.tm.log(f"Training troops (type {troop_idx}) at position {building_pos}...")
                await train_max_troops(self.cookies, self.server_url, building_pos, troop_idx, loops, lambda m: self.tm.log(m))
                self.tm.log("Troop training complete!")
            
            self.tm.add_task(f"Train Troops ({loops} loops)", train_troops_task())
            print(f"\n  ✓ Training troops in background!")
        
        await asyncio.sleep(1.5)

    async def settling_menu(self):
        """Find empty spots and settle menu."""
        clear()
        self.print_header()
        print("\n  VILLAGE SETTLING")
        print("  " + "-" * 50)
        
        print("\n  Options:")
        print("  [1] Find Empty Spots (scan nearby)")
        print("  [2] Auto Settle (find + settle)")
        print("  [3] Settle at specific coordinates")
        print("  [b] Back")
        
        choice = input("\n  > ").strip().lower()
        if choice == 'b':
            return
        
        if choice == '1':
            # Find empty spots
            print("\n  Scanning for empty spots...")
            
            async def find_spots_task():
                from bot.settling import find_empty_spots, get_coordinates_from_id
                self.tm.log("Scanning for empty spots...")
                spots = await find_empty_spots(self.cookies, self.server_url, max_spots=10, max_radius=20, callback=lambda m: self.tm.log(m))
                if spots:
                    for spot in spots:
                        coords = await get_coordinates_from_id(spot)
                        self.tm.log(f"Empty: ({coords[0]}|{coords[1]}) - ID {spot}")
                    self.tm.log(f"Found {len(spots)} empty spots!")
                else:
                    self.tm.log("No empty spots found nearby.")
            
            self.tm.add_task("Find Empty Spots", find_spots_task())
            print("  ✓ Scanning in background! Check logs.")
            
        elif choice == '2':
            # Auto settle
            print("\n  Starting auto-settle...")
            print("  Make sure you have 3 settlers trained!")
            
            async def auto_settle_task():
                from bot.settling import auto_settle
                self.tm.log("Starting auto-settle...")
                success = await auto_settle(self.cookies, self.server_url, callback=lambda m: self.tm.log(m))
                if success:
                    self.tm.log("✓ Village settled successfully!")
                else:
                    self.tm.log("Settling failed - check if you have 3 settlers")
            
            self.tm.add_task("Auto Settle", auto_settle_task())
            print("  ✓ Auto-settle started in background!")
            
        elif choice == '3':
            # Settle at coordinates
            x = input("  Enter X coordinate: ").strip()
            y = input("  Enter Y coordinate: ").strip()
            
            try:
                x, y = int(x), int(y)
                # Convert to village ID: id = (200 + y) * 401 + (200 + x) + 1
                target_id = (200 + y) * 401 + (200 + x) + 1
                
                print(f"\n  Target: ({x}|{y}) - ID {target_id}")
                
                async def settle_task():
                    from bot.settling import settle_village
                    self.tm.log(f"Attempting to settle at ({x}|{y})...")
                    success = await settle_village(self.cookies, self.server_url, target_id, callback=lambda m: self.tm.log(m))
                    if success:
                        self.tm.log(f"✓ Settled at ({x}|{y})!")
                    else:
                        self.tm.log(f"Failed to settle at ({x}|{y})")
                
                self.tm.add_task(f"Settle ({x}|{y})", settle_task())
                print("  ✓ Settling in background!")
                
            except ValueError:
                print("  Invalid coordinates!")
        
        await asyncio.sleep(1.5)

    async def increase_production_task(self, loops):
        """Wrapper task for production."""
        from bot.production import increase_production_async
        self.tm.log(f"Starting production increase ({loops} loops)")
        # Create a custom callback or pass db connection
        # For now reusing existing function which prints to stdout (might interfere with UI slightly but OK)
        await increase_production_async(self.username, "", loops, self.conn, self.cookies)
        self.tm.log("Finished production increase")

    async def increase_storage_task(self, loops):
        """Wrapper task for storage."""
        from bot.storage import increase_storage_async
        self.tm.log(f"Starting storage increase ({loops} loops)")
        await increase_storage_async(self.username, "", loops, self.conn, self.cookies)
        self.tm.log("Finished storage increase")

    async def view_logs(self):
        """View full log history."""
        while True:
            clear()
            print("=" * 60)
            print("  SYSTEM LOGS")
            print("=" * 60)
            for log in self.tm.logs[-20:]:
                print(f"  {log}")
            print("-" * 60)
            print("  [b] Back")
            if input("  > ").lower() == 'b':
                break
            await asyncio.sleep(0.5)

    def print_dashboard(self):
        """Print full dashboard with stats and tasks."""
        print("=" * 60)
        print(f"  TRAVIAN BOT | {self.username} @ {self.server_name}")
        
        # Village Info
        v_name = self.current_village['name'] if self.current_village else "Unknown"
        v_coords = f"({self.current_village['x']}|{self.current_village['y']})" if self.current_village else ""
        print(f"  Village: {v_name} {v_coords}")
        
        # Resources
        print("-" * 60)
        if self.resources:
            w = self.resources.get('wood', '0')
            c = self.resources.get('clay', '0')
            i = self.resources.get('iron', '0')
            cr = self.resources.get('crop', '0')
            ware = self.resources.get('warehouse', '0')
            gran = self.resources.get('granary', '0')
            
            print(f"  Wood: {format_number(w):<10} Clay: {format_number(c):<10}")
            print(f"  Iron: {format_number(i):<10} Crop: {format_number(cr):<10}")
            print(f"  Ware: {format_number(ware):<10} Gran: {format_number(gran):<10}")
        else:
            print("  Fetching resources...")
            
        print("-" * 60)
        
        # Active Tasks
        active_tasks = self.tm.get_active_tasks()
        if active_tasks:
            print(f"  ACTIVE TASKS ({len(active_tasks)})")
            for t in active_tasks:
                duration = datetime.now() - t['start_time']
                print(f"  • {t['name']} - {str(duration).split('.')[0]} elapsed")
        else:
            print("  No active tasks.")
            
        # Recent Log (last 1 line)
        if self.tm.logs:
            print("-" * 60)
            print(f"  Last Log: {self.tm.logs[-1]}")
        
        print("=" * 60)

    def print_header(self):
        """Alias for print_dashboard for backwards compatibility."""
        self.print_dashboard()

async def main():
    """Main entry point."""
    clear()
    print("=" * 60)
    print("  TRAVIAN BOT - Minimal CLI")
    print("=" * 60)
    print()
    
    cli = TravianCLI()
    
    # Login credentials with defaults
    print("  Press Enter for defaults (abaddon/bristleback)")
    username = input("  Username [abaddon]: ").strip() or "abaddon"
    password = input("  Password [bristleback]: ").strip() or "bristleback"
    
    print("\n  Logging in to gotravspeed.com...")
    
    try:
        # Fetch available servers first
        from bot.session_manager import SessionManager
        servers = await SessionManager.fetch_servers(username, password)
        
        if servers is None:
            print("\n  ❌ Login failed! Check your credentials.")
            return
        
        if not servers:
            print("\n  ❌ No servers available!")
            return
        
        # Display servers - separate registered vs not
        clear()
        print("=" * 60)
        print("  SERVER SELECTION")
        print("=" * 60)
        
        # Check if server has 'registered' flag (from fetch_servers)
        # For now we mark first 2 as "My Servers" based on typical pattern
        my_servers = [s for s in servers if s.get('registered', False)]
        other_servers = [s for s in servers if not s.get('registered', False)]
        
        if my_servers:
            print("\n  💾 MY SERVERS (Already Registered)")
            print(f"  {'ID':<4} {'Name':<12} {'Speed':<18} {'Players'}")
            print("  " + "-" * 50)
            for s in my_servers:
                print(f"  {s['id']:<4} {s['name']:<12} {s['speed']:<18} {s['players']}")
        
        print("\n  🌍 ALL SERVERS")
        print(f"  {'ID':<4} {'Name':<12} {'Speed':<18} {'Players'}")
        print("  " + "-" * 50)
        print("  " + "-" * 50)
        
        for s in servers:
            print(f"  {s['id']:<4} {s['name']:<12} {s['speed']:<18} {s['players']}")
        
        print()
        server_choice = input("  Enter server ID [9]: ").strip()
        server_id = int(server_choice) if server_choice.isdigit() else 9
        
        # Find server name
        server_name = "Fun"
        for s in servers:
            if s['id'] == server_id:
                server_name = s['name']
                break
        
        # Check if user needs to select tribe (new registration)
        print(f"\n  Connecting to {server_name} (ID: {server_id})...")
        
        # Try login first
        if await cli.login(username, password, server_id):
            print("  ✅ Connected!")
            await asyncio.sleep(1)
            await cli.main_menu()
        else:
            # May need registration - ask for tribe
            print("\n  ⚠️ Not registered on this server yet.")
            print("\n  Select your tribe:")
            print("  [1] Roman")
            print("  [2] Teuton")
            print("  [3] Gaul")
            tribe = input("\n  Tribe (1/2/3) [1]: ").strip()
            if tribe not in ['1', '2', '3']:
                tribe = '1'
            
            tribe_names = {'1': 'Roman', '2': 'Teuton', '3': 'Gaul'}
            print(f"\n  Registering as {tribe_names[tribe]}...")
            
            # TODO: Implement registration with tribe selection
            print("\n  ❌ Registration not yet implemented.")
            print("  Please register manually in browser first, then try again.")
            
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()


def run():
    """Entry point for package."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Goodbye!")


if __name__ == "__main__":
    run()
