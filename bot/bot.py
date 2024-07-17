import asyncio
import sqlite3
from login import login
from village import fetch_villages, rename_village
from construction import construct_capital, research_academy, upgrade_smithy, upgrade_armory
from storage import increase_storage_async
from production import increase_production_async
from database import init_db, save_user
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main_menu(username, password):
    conn = init_db()
    cookies = await login(username, password, conn)

    while True:
        print("\nMain Menu")
        print("1. Increase Storage")
        print("2. Increase Production")
        print("3. Fetch Villages")
        print("4. Rename Villages")
        print("5. Construct Capital")
        print("6. Research Academy")
        print("7. Upgrade Smithy")
        print("8. Upgrade Armory")
        print("9. Exit")
        action = input("Select an action: ")

        if action == '1':
            loops = int(input("Number of loops: "))
            await increase_storage_async(username, password, loops, conn)
        elif action == '2':
            loops = int(input("Number of loops: "))
            await increase_production_async(username, password, loops, conn)
        elif action == '3':
            villages = await fetch_villages(username, password, cookies, conn)
            for village in villages:
                logging.info(f"Village: {village}")
        elif action == '4':
            villages = await fetch_villages(username, password, cookies, conn)
            for village in villages:
                new_name = input(f"Enter new name for village {village[0]} (ID: {village[1]}): ")
                await rename_village(cookies, village[1], new_name)
        elif action == '5':
            villages = await fetch_villages(username, password, cookies, conn)
            capital = next((v for v in villages if 'Capital' in v[0]), None)
            if capital:
                await construct_capital(cookies, capital[1], conn)
            else:
                print("No capital village found.")
        elif action == '6':
            await research_academy(cookies)
        elif action == '7':
            await upgrade_smithy(cookies)
        elif action == '8':
            await upgrade_armory(cookies)
        elif action == '9':
            print("Exiting...")
            break
        else:
            print("Invalid action. Please try again.")

if __name__ == "__main__":
    print("Welcome to Bot for Fun Server")
    username = input("Username: ")
    password = input("Password: ")
    asyncio.run(main_menu(username, password))
