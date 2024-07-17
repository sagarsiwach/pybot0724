import asyncio
import httpx
from bs4 import BeautifulSoup
# from config import read_config
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable httpx logging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

# Read configuration from the CSV file
# config = read_config()

# Base URL for the website
base_url = "https://gotravspeed.com"

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': base_url,
    'Upgrade-Insecure-Requests': '1'
}

async def main():
    while True:
        cookies = await login()
        # await start_large_celebration(120500, cookies)
        # await increase_storage_async(5000, cookies)
        await increase_production_async(1250000, cookies)

async def login():
    # Create a new client instance for each login attempt
    async with httpx.AsyncClient() as client:
        # Step 1: Navigate to the main page
        response = await client.get(base_url, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to access the main page")
            raise Exception("Failed to access the main page")

        # Step 2: Submit login credentials
        login_data = {
            'name': 'abaddon',
            'password': 'avernus'
        }
        response = await client.post(base_url, data=login_data, headers=headers)
        if "Login failed" in response.text:
            logger.error("Login failed")
            raise Exception("Login failed")
        else:
            logger.info("Login successful")

        # Step 3: Navigate to the server selection page
        response = await client.get(base_url + "/game/servers", headers=headers)
        if response.status_code != 200:
            logger.error("Failed to access the server selection page")
            raise Exception("Failed to access the server selection page")

        # Step 4: Select a server (server ID 9 in this example)
        server_data = {
            'action': 'server',
            'value': '9'
        }
        response = await client.post(base_url + "/game/servers", data=server_data, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to select server")
            raise Exception("Failed to select server")

        # Step 5: Log in to the selected server
        server_login_data = {
            'action': 'serverLogin',
            'value[pid]': '9',
            'value[server]': '9'
        }
        response = await client.post(base_url + "/game/servers", data=server_login_data, headers=headers)
        if response.status_code != 200:
            logger.error("Failed to log in to server")
            raise Exception("Failed to log in to server")

        # Step 6: Access a specific page in the game (e.g., village1.php)
        response = await client.get("https://fun.gotravspeed.com/village1.php", headers=headers)
        if response.status_code != 200:
            logger.error("Failed to access the game page")
            raise Exception("Failed to access the game page")

        logger.info("Successfully logged in and accessed the game page")
        # Return the cookies from the new client instance
        return client.cookies


async def increase_production_async(loop_count, cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        for _ in range(loop_count):
            get_response = await client.get("https://fun.gotravspeed.com/buy2.php?t=0")
            soup = BeautifulSoup(get_response.text, 'html.parser')
            key_element = soup.find('input', {'name': 'key'})

            if key_element is None:
                logger.error("Failed to find key for increasing production. Clearing cache and cookies, and restarting...")
                client.cookies.clear()
                await asyncio.sleep(1)
                raise Exception("Failed to find key for increasing production. Script exiting.")

            key = key_element['value']
            data = {
                'selected_res': 4,
                'g-recaptcha-response': 'xxxx',
                'xor': 100,
                'key': key
            }
            await client.post("https://fun.gotravspeed.com/buy2.php?t=0&Shop=done", data=data)
            logger.info("Production Increased")


async def increase_storage_async(loop_count, cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        for _ in range(loop_count):
            get_response = await client.get("https://fun.gotravspeed.com/buy2.php?t=2")
            soup = BeautifulSoup(get_response.text, 'html.parser')
            key_element = soup.find('input', {'name': 'key'})

            if key_element is None:
                logger.error("Failed to find key for increasing storage. Clearing cache and cookies, and restarting...")
                client.cookies.clear()
                await asyncio.sleep(1)
                raise Exception("Failed to find key for increasing storage. Script exiting.")

            key = key_element['value']
            data = {
                'selected_res': 4,
                'g-recaptcha-response': 'xxxx',
                'xor': 100,
                'key': key
            }
            await client.post("https://fun.gotravspeed.com/buy2.php?t=2&Shop=done", data=data)
            logger.info("Storage Increased")

async def start_large_celebration(loop_count, cookies):
    async with httpx.AsyncClient(cookies=cookies) as client:
        url = "https://fun.gotravspeed.com/build.php?id=35"

        for _ in range(loop_count):
            get_response = await client.get(url)
            soup = BeautifulSoup(get_response.text, 'html.parser')
            celebration_link = soup.find('a', {'class': 'build', 'href': True})

            if celebration_link:
                celebration_url = celebration_link['href']
                url = f"https://fun.gotravspeed.com/{celebration_url}"
                logger.info("Large Celebration Started")
            else:
                logger.error("Failed to parse celebration key")
                continue



if __name__ == "__main__":
    asyncio.run(main())