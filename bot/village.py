import asyncio
import httpx
from bs4 import BeautifulSoup
from login import login
from database import save_village
import logging
from requests_toolbelt.multipart.encoder import MultipartEncoder

base_url = "https://fun.gotravspeed.com"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress httpx logging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)


async def fetch_villages(username, password, cookies, conn):
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{base_url}/profile.php")
        if response.status_code == 302:  # Session expired
            logger.warning("Session expired, re-authenticating...")
            cookies = await login(username, password, conn)  # Re-authenticate
            async with httpx.AsyncClient(cookies=cookies) as new_client:
                response = await new_client.get(f"{base_url}/profile.php")

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

        return village_data

async def rename_village(cookies, vid, new_name):
    async with httpx.AsyncClient(cookies=cookies) as client:
        # Get the profile edit page
        response = await client.get("https://fun.gotravspeed.com/profile.php?t=1")
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

        response = await client.post("https://fun.gotravspeed.com/profile.php", content=encoder.to_string(), headers=headers)
        response.raise_for_status()
        logger.info(f"Renamed village {vid} to {new_name}")
