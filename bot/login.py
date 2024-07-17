import httpx
from bs4 import BeautifulSoup
from database import save_user

base_url = "https://gotravspeed.com"

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

async def login(username, password, conn):
    async with httpx.AsyncClient() as client:
        response = await client.get(base_url, headers=headers)
        response.raise_for_status()

        login_data = {
            'name': username,
            'password': password
        }
        response = await client.post(base_url, data=login_data, headers=headers)
        if "Login failed" in response.text:
            print(f"Login failed")
            return None
        else:
            print("Login successful")

        response = await client.get(base_url + "/game/servers", headers=headers)
        response.raise_for_status()

        server_data = {
            'action': 'server',
            'value': '9'
        }
        response = await client.post(base_url + "/game/servers", data=server_data, headers=headers)
        response.raise_for_status()

        server_login_data = {
            'action': 'serverLogin',
            'value[pid]': '9',
            'value[server]': '9'
        }
        response = await client.post(base_url + "/game/servers", data=server_login_data, headers=headers)
        response.raise_for_status()

        response = await client.get("https://fun.gotravspeed.com/village1.php", headers=headers)
        response.raise_for_status()

        print(f"Successfully logged in and accessed the game page")
        save_user(conn, username, password)
        return client.cookies
