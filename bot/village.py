import httpx
from bs4 import BeautifulSoup
from tabulate import tabulate
from database import save_village, delete_all_villages_for_user
import logging
from utils import switch_village
from requests_toolbelt.multipart.encoder import MultipartEncoder

BASE_URL = "https://fun.gotravspeed.com"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_villages(username, session_manager, conn):
    """
    Fetch and save villages for a user.
    """
    # Clear existing data for the user
    delete_all_villages_for_user(conn, username)

    cookies = await session_manager.get_cookies()
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/profile.php")
        if response.status_code == 302:  # Session expired
            logger.warning("Session expired, re-authenticating...")
            cookies = await session_manager.login()  # Re-authenticate
            async with httpx.AsyncClient(cookies=cookies) as new_client:
                response = await new_client.get(f"{BASE_URL}/profile.php")

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        village_data = []
        village_table = soup.find('table', {'id': 'villages'})
        if village_table:
            rows = village_table.find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                name = cols[0].text.strip()
                vid = row.find('a')['href'].split('=')[-1]
                coords = cols[4].text.strip()[1:-1].split('|')
                x = int(coords[0])
                y = int(coords[1])
                village_data.append((name, vid, x, y))
                save_village(conn, username, vid, name, x, y)

        print(tabulate(village_data, headers=["Village Name", "Village ID", "X Coordinate", "Y Coordinate"], tablefmt="pretty"))
        return village_data


async def rename_village(session_manager, conn, username):
    """
    Rename a village selected from the list.
    """
    villages = await fetch_villages(username, session_manager, conn)
    village_dict = {str(index + 1): village for index, village in enumerate(villages)}
    village_dict['0'] = 'Back'

    while True:
        print("\nSelect a village to rename (or press '0' to go back):")
        for index, (name, vid, x, y) in village_dict.items():
            if index == '0':
                print(f"{index}. Back")
            else:
                print(f"{index}. {name} (ID: {vid})")

        choice = input("Enter your choice: ")

        if choice == '0':
            return

        if choice in village_dict:
            selected_village = village_dict[choice]
            new_name = input(f"Enter new name for village {selected_village[0]} (ID: {selected_village[1]}): ")

            await switch_village(session_manager, selected_village[1])
            cookies = await session_manager.get_cookies()

            async with httpx.AsyncClient(cookies=cookies) as client:
                # Get the profile edit page
                response = await client.get(f"{BASE_URL}/profile.php?t=1")
                response.raise_for_status()

                # Extract form data
                soup = BeautifulSoup(response.text, 'html.parser')
                form = soup.find('form', {'action': 'profile.php'})
                data = {tag['name']: tag.get('value', '') for tag in form.find_all('input')}

                # Add missing fields
                data.update({
                    'oldavatar': '/assets/default/img/q/l6.jpg',
                    'jahr': '',
                    'monat': '0',
                    'tag': '',
                    'be1': '',
                    'mw': '0',
                    'ort': '',
                    's1.x': '18',
                    's1.y': '10'
                })

                # Update the village name
                data['dname'] = new_name

                # Prepare multipart/form-data payload
                encoder = MultipartEncoder(fields=data)

                # Post the new village name
                headers = {
                    'Content-Type': encoder.content_type
                }

                response = await client.post(f"{BASE_URL}/profile.php", content=encoder.to_string(), headers=headers)
                response.raise_for_status()
                logger.info(f"Renamed village {selected_village[1]} to {new_name}")
                break
