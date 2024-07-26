# fetch_all_villages.py

import httpx
from bs4 import BeautifulSoup
import logging
import asyncio
from database import save_village

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://fun.gotravspeed.com"

async def fetch_statistics(cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/statistics.php")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        player_rows = soup.select('#player tbody tr')
        players = []

        for row in player_rows:
            player_link = row.select_one('td.pla a')
            if player_link:
                player_id = player_link['href'].split('=')[-1]
                player_name = player_link.text.strip()
                players.append((player_id, player_name))

        logger.info(f"Found {len(players)} players in the statistics.")
        return players

async def fetch_villages_for_player(cookies, player_id, player_name, conn):
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/profile.php?uid={player_id}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        village_rows = soup.select('#villages tbody tr')

        for row in village_rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            village_name = cols[0].text.strip()
            village_id = row.select_one('a')['href'].split('=')[-1]
            population = int(cols[1].text.strip())
            coords = cols[4].text.strip()[1:-1].split('|')
            x_coord = int(coords[0])
            y_coord = int(coords[1])

            save_village(conn, player_name, village_id, village_name, x_coord, y_coord)
            logger.info(f"Saved village {village_name} (ID: {village_id}) for player {player_name}")

async def fetch_and_store_all_villages(session_manager, conn):
    cookies = await session_manager.get_cookies()
    players = await fetch_statistics(cookies)

    for player_id, player_name in players:
        await fetch_villages_for_player(cookies, player_id, player_name, conn)

if __name__ == "__main__":
    from session_manager import SessionManager
    from database import init_db

    async def main():
        conn = init_db()
        session_manager = SessionManager('your_username', 'your_password', conn)
        await session_manager.login()
        await fetch_and_store_all_villages(session_manager, conn)

    asyncio.run(main())
