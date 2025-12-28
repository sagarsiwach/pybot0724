# session_manager.py

import httpx
import logging
import asyncio
from .database import save_user

INITIAL_BASE_URL = "https://gotravspeed.com"
POST_LOGIN_BASE_URL = "https://fun.gotravspeed.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': INITIAL_BASE_URL,
    'Upgrade-Insecure-Requests': '1'
}

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages login sessions and cookies for the application.
    """

    def __init__(self, username, password, civilization, conn):
        self.username = username
        self.password = password
        self.civilization = civilization
        self.conn = conn
        self.cookies = None

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
                        'value': '9'
                    }
                    response = await client.post(INITIAL_BASE_URL + "/game/servers", data=server_data, headers=HEADERS)
                    response.raise_for_status()

                    server_login_data = {
                        'action': 'serverLogin',
                        'value[pid]': '9',
                        'value[server]': '9'
                    }
                    response = await client.post(INITIAL_BASE_URL + "/game/servers", data=server_login_data, headers=HEADERS)
                    response.raise_for_status()

                    response = await client.get(POST_LOGIN_BASE_URL + "/village1.php", headers=HEADERS)
                    response.raise_for_status()

                    logger.info("Successfully logged in and accessed the game page")
                    save_user(self.conn, self.username, self.password)
                    self.cookies = client.cookies

                    return self.cookies
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    logger.warning(f"Server error ({e.response.status_code}), attempt {attempt + 1}/{retries}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
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
