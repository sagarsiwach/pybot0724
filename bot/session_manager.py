# session_manager.py

import httpx
import logging
import asyncio
from bs4 import BeautifulSoup
from .database import save_user

INITIAL_BASE_URL = "https://gotravspeed.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Server configurations
SERVERS = {
    1: {'name': 'Pvp', 'url': 'https://pvp.gotravspeed.com', 'speed': '10M'},
    2: {'name': 'Alpha', 'url': 'https://alpha.gotravspeed.com', 'speed': '5M'},
    3: {'name': 'Beta', 'url': 'https://beta.gotravspeed.com', 'speed': '250K'},
    4: {'name': 'Hyper', 'url': 'https://hyper.gotravspeed.com', 'speed': '500K'},
    5: {'name': 'Slow', 'url': 'https://slow.gotravspeed.com', 'speed': '500'},
    6: {'name': 'Test', 'url': 'https://test.gotravspeed.com', 'speed': '1M'},
    9: {'name': 'Fun', 'url': 'https://fun.gotravspeed.com', 'speed': '20M'},
    32: {'name': 'Netus', 'url': 'https://netus.gotravspeed.com', 'speed': '20M'},
}

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages login sessions and cookies for the application.
    """

    def __init__(self, username, password, civilization, conn, server_id=9):
        self.username = username
        self.password = password
        self.civilization = civilization
        self.conn = conn
        self.cookies = None
        self.server_id = server_id
        self.server_url = SERVERS.get(server_id, SERVERS[9])['url']

    async def login(self, retries=3):
        """
        Perform the login operation and store cookies.
        Retries on server errors.
        """
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(INITIAL_BASE_URL, headers=HEADERS)
                    response.raise_for_status()

                    login_data = {
                        'name': self.username,
                        'password': self.password
                    }
                    response = await client.post(INITIAL_BASE_URL, data=login_data, headers=HEADERS)
                    if "Login failed" in response.text:
                        logger.error("Login failed - invalid credentials")
                        return None
                    logger.info("Login successful")

                    response = await client.get(INITIAL_BASE_URL + "/game/servers", headers=HEADERS)
                    response.raise_for_status()

                    server_data = {
                        'action': 'server',
                        'value': str(self.server_id)
                    }
                    response = await client.post(INITIAL_BASE_URL + "/game/servers", data=server_data, headers=HEADERS)
                    response.raise_for_status()

                    server_login_data = {
                        'action': 'serverLogin',
                        'value[pid]': str(self.server_id),
                        'value[server]': str(self.server_id)
                    }
                    response = await client.post(INITIAL_BASE_URL + "/game/servers", data=server_login_data, headers=HEADERS)
                    response.raise_for_status()

                    response = await client.get(self.server_url + "/village1.php", headers=HEADERS)
                    response.raise_for_status()

                    logger.info(f"Successfully logged in to server {SERVERS.get(self.server_id, {}).get('name', self.server_id)}")
                    save_user(self.conn, self.username, self.password)
                    self.cookies = client.cookies

                    return self.cookies
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    logger.warning(f"Server error ({e.response.status_code}), attempt {attempt + 1}/{retries}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        logger.error(f"Server error after {retries} attempts: {e}")
                        return None
                else:
                    logger.error(f"HTTP error: {e}")
                    return None
            except httpx.RequestError as e:
                logger.warning(f"Network error, attempt {attempt + 1}/{retries}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error(f"Network error after {retries} attempts: {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error during login: {e}")
                return None
        
        return None

    async def get_cookies(self):
        """
        Return stored cookies or login if not authenticated.
        """
        if self.cookies is None:
            self.cookies = await self.login()
        return self.cookies
    
    @staticmethod
    async def fetch_servers(username: str, password: str):
        """Fetch available servers from the website."""
        servers = []
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, headers=HEADERS) as client:
                await client.get(INITIAL_BASE_URL)
                
                login_data = {'name': username, 'password': password}
                response = await client.post(INITIAL_BASE_URL, data=login_data)
                
                if "Login failed" in response.text:
                    return None
                
                response = await client.get(INITIAL_BASE_URL + "/game/servers")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find "My servers" section (servers user is registered on)
                my_servers_section = False
                current_section = "other"
                
                for elem in soup.find_all(['h2', 'div']):
                    # Check for section headers
                    if elem.name == 'h2':
                        text = elem.text.strip().lower()
                        if 'my server' in text:
                            current_section = "my"
                        elif 'server' in text:
                            current_section = "other"
                    
                    # Check for server divs
                    if elem.name == 'div' and 'server' in elem.get('class', []):
                        onclick = elem.get('onclick', '')
                        if 'serverSelected(' in onclick:
                            server_id = int(onclick.split('(')[1].split(')')[0])
                            name_elem = elem.find('h2', class_='server__name')
                            name = name_elem.text.strip() if name_elem else f"Server {server_id}"
                            
                            cells = elem.find_all('span', class_='server__cell')
                            speed = cells[0].text.replace('Speed: ', '') if cells else 'N/A'
                            players = cells[1].text.replace('Players: ', '') if len(cells) > 1 else 'N/A'
                            
                            servers.append({
                                'id': server_id,
                                'name': name,
                                'speed': speed,
                                'players': players,
                                'registered': current_section == "my"
                            })
                
        except Exception as e:
            logger.error(f"Error fetching servers: {e}")
            return None
        
        return servers
