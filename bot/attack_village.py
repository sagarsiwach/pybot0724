# attack_village.py

import httpx
from bs4 import BeautifulSoup
import asyncio
from tabulate import tabulate

BASE_URL = "https://fun.gotravspeed.com"

async def attack_village(cookies, village_url, troop_data):
    try:
        village_id = village_url.split('=')[-1]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://fun.gotravspeed.com",
            "Referer": village_url,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

        async with httpx.AsyncClient(cookies=cookies) as client:
            response = await client.get(village_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            key = soup.find('input', {'name': 'key'})['value']

            data = {
                'id': village_id,
                'c': '4',  # Attack: raid
                **troop_data,
                'key': key
            }

            attack_response = await client.post(f"{BASE_URL}/v2v.php", headers=headers, data=data)
            if attack_response.status_code == 200:
                print(f"Attacked village with ID {village_id}")
            else:
                print(f"Error attacking village with ID {village_id}: {attack_response.status_code}")

            await asyncio.sleep(0.05)

    except Exception as e:
        print(f"Error attacking village with ID {village_id}: {e}")

async def select_and_attack_village(session_manager, conn):
    """
    Select a player, then a village, and specify the number of troops to send.
    """
    # Fetch villages first to ensure the list is up to date
    villages = await fetch_villages(session_manager.username, session_manager, conn)
    print("\nAvailable Villages:")
    print(tabulate(villages, headers=["Village Name", "Village ID", "X Coordinate", "Y Coordinate"], tablefmt="pretty"))

    village_choice = int(input("Select a village to attack from (enter the index): ")) - 1
    if 0 <= village_choice < len(villages):
        selected_village = villages[village_choice]
    else:
        print("Invalid choice. Returning to main menu.")
        return

    # Logic to select the target player and village
    # Placeholder: Assuming you have a function to fetch players and their villages
    target_players = [
        {"player_name": "Player1", "villages": [{"name": "Village1", "url": f"{BASE_URL}/village2.php?vid=1"}]},
        {"player_name": "Player2", "villages": [{"name": "Village2", "url": f"{BASE_URL}/village2.php?vid=2"}]}
    ]

    print("\nAvailable Players:")
    for index, player in enumerate(target_players):
        print(f"{index + 1}. {player['player_name']}")

    player_choice = int(input("Select a player to attack (enter the index): ")) - 1
    if 0 <= player_choice < len(target_players):
        selected_player = target_players[player_choice]
    else:
        print("Invalid choice. Returning to main menu.")
        return

    print("\nAvailable Villages of Selected Player:")
    for index, village in enumerate(selected_player['villages']):
        print(f"{index + 1}. {village['name']} (URL: {village['url']})")

    village_choice = int(input("Select a village to attack (enter the index): ")) - 1
    if 0 <= village_choice < len(selected_player['villages']):
        target_village = selected_player['villages'][village_choice]
    else:
        print("Invalid choice. Returning to main menu.")
        return

    # Get troop data
    troop_data = {
        't[1]': input("Enter number of Phalanx: ") or '0',
        't[2]': input("Enter number of Swordsman: ") or '0',
        't[3]': input("Enter number of Pathfinder: ") or '0',
        't[4]': input("Enter number of Theutates Thunder: ") or '0',
        't[5]': input("Enter number of Druidrider: ") or '0',
        't[6]': input("Enter number of Haeduan: ") or '0',
        't[7]': input("Enter number of Battering Ram: ") or '0',
        't[8]': input("Enter number of Trebuchet: ") or '0',
        't[9]': input("Enter number of Chief: ") or '0',
        't[0]': input("Enter number of Settler: ") or '0'
    }

    cookies = await session_manager.get_cookies()
    await attack_village(cookies, target_village['url'], troop_data)
