import httpx
import asyncio
import logging
from bs4 import BeautifulSoup
from database import get_buildings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Base URL for the game
base_url = "https://fun.gotravspeed.com"

async def switch_village(cookies, village_id):
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{base_url}/village2.php?vid={village_id}")
        if response.status_code == 200:
            logging.info(f"Switched to village ID {village_id}")
        else:
            logging.error(f"Failed to switch to village ID {village_id}")

async def build_or_upgrade_resource(cookies, position_id, loop):
    async with httpx.AsyncClient(cookies=cookies) as client:
        for _ in range(loop):
            position_response = await client.get(f"{base_url}/build.php?id={position_id}")
            position_soup = BeautifulSoup(position_response.text, "html.parser")
            build_link = position_soup.find("a", {"class": "build"})

            if build_link is None:
                logging.warning(f"No upgrade link found for resource at position {position_id}. Skipping...")
                break

            csrf_token = build_link["href"].split("&k=")[1]
            upgrade_response = await client.get(f"{base_url}/village2.php?id={position_id}&k={csrf_token}")
            if upgrade_response.status_code == 200:
                logging.info(f"Successfully upgraded resource at position {position_id}")
            else:
                logging.error(f"Failed to upgrade resource at position {position_id}. Status code: {upgrade_response.status_code}")

async def construct_and_upgrade_building(cookies, position_id, building_id, loops):
    async with httpx.AsyncClient(cookies=cookies) as client:
        for _ in range(loops):
            response = await client.get(f"{base_url}/build.php?id={position_id}")
            if response.status_code != 200:
                logging.error(f"Failed to access the construction page for position ID {position_id}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            build_link = soup.find('a', class_='build')
            if not build_link:
                logging.warning(f"Construction link not found for position ID {position_id}, building ID {building_id}. Skipping...")
                return
            href = build_link['href']
            csrf_token = href.split('&k=')[-1]

            upgrade_message = soup.find('p', class_='none')
            if upgrade_message:
                message_words = upgrade_message.text.split()
                if len(message_words) >= 3 and message_words[0] == "Updated" and message_words[-1] == "Fully":
                    building_name = " ".join(message_words[1:-1])
                    logging.info(f"{building_name} is fully upgraded. Skipping...")
                    break

            construct_url = f"{base_url}/village2.php?id={position_id}&b={building_id}&k={csrf_token}"
            response = await client.get(construct_url)
            if response.status_code == 200:
                logging.info(f"Successfully constructed/upgraded building ID {building_id} in position ID {position_id}")
            else:
                logging.error(f"Failed to construct/upgrade building ID {building_id} in position ID {position_id}")

async def construct_capital(cookies, village_id, conn):
    buildings = get_buildings(conn)
    await switch_village(cookies, village_id)
    for building in buildings:
        pid = building[0]
        bid = building[1]
        loop = building[2]
        if pid <= 18:  # Resource fields
            await build_or_upgrade_resource(cookies, position_id=pid, loop=loop)
        else:  # Other buildings
            await construct_and_upgrade_building(cookies, position_id=pid, building_id=bid, loops=loop)

async def research_academy(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        while True:
            response = await client.get(f"{base_url}/build.php?id=33")
            soup = BeautifulSoup(response.text, 'html.parser')
            research_links = soup.select('table.build_details .act a.build')
            if not research_links:
                logging.info("All troops in the Academy are fully researched.")
                break

            for link in research_links:
                research_url = f"{base_url}/{link['href']}"
                await client.get(research_url)
                logging.info("Researching new troop in the Academy")
                break

async def upgrade_armory(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        while True:
            response = await client.get(f"{base_url}/build.php?id=29")
            soup = BeautifulSoup(response.text, 'html.parser')
            upgrade_links = soup.select('table.build_details .act a.build')
            if not upgrade_links:
                logging.info("All troops in the Armory are fully upgraded.")
                break

            for link in upgrade_links:
                troop_info = link.find_previous('div', class_='tit').text
                troop_level = int(troop_info.split('(')[-1].split(')')[0].split(' ')[-1])
                if troop_level < 20:
                    upgrade_url = f"{base_url}/{link['href']}"
                    await client.get(upgrade_url)
                    logging.info(f"Upgrading {troop_info.split('(')[0].strip()} to level {troop_level + 1} in the Armory")
                    break

async def upgrade_smithy(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        while True:
            response = await client.get(f"{base_url}/build.php?id=21")
            soup = BeautifulSoup(response.text, 'html.parser')
            upgrade_links = soup.select('table.build_details .act a.build')
            if not upgrade_links:
                logging.info("All troops in the Smithy are fully upgraded.")
                break

            for link in upgrade_links:
                troop_info = link.find_previous('div', class_='tit').text
                troop_level = int(troop_info.split('(')[-1].split(')')[0].split(' ')[-1])
                if troop_level < 20:
                    upgrade_url = f"{base_url}/{link['href']}"
                    await client.get(upgrade_url)
                    logging.info(f"Upgrading {troop_info.split('('')[0].strip()} to level {troop_level + 1} in the Smithy")
                    break
