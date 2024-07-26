# bot.py

import asyncio
import logging
from session_manager import SessionManager
from village import fetch_villages, rename_village
from construction import construct_capital, construct_village, research_academy, upgrade_smithy, upgrade_armory
from storage import increase_storage_async
from production import increase_production_async
from database import init_db, get_all_users, delete_all_users, get_all_empty_spots
from map_finder import generate_spiral_village_ids, find_empty_village_spots
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main_menu(session_manager):
    """
    Display the main menu and handle user actions.
    """
    await session_manager.login()

    while True:
        print("\nMain Menu")
        print("1. Increase Storage")
        print("2. Increase Production")
        print("3. Combined Operations")
        print("4. Fetch Villages")
        print("5. Rename Villages")
        print("6. Construct Capital")
        print("7. Construct Village")
        print("8. Research Academy")
        print("9. Upgrade Smithy")
        print("10. Upgrade Armory")
        print("11. Forget All Usernames")
        print("12. Fetch All Player Villages")
        print("13. Attack Village")
        print("14. Find Empty Village Spots")
        print("0. Exit")
        action = input("Select an action: ")

        if action == '14':
            villages = await fetch_villages(session_manager.username, session_manager, session_manager.conn)
            capital = next((v for v in villages if 'Capital' in v[0]), None)
            if capital:
                center_village_id = int(capital[1])  # Ensure the ID is an integer
                potential_village_ids = generate_spiral_village_ids(center_village_id)
                await find_empty_village_spots(await session_manager.get_cookies(), potential_village_ids, session_manager.conn)
                empty_spots = get_all_empty_spots(session_manager.conn)
                print("Empty village spots:")
                for spot in empty_spots:
                    print(f"Village ID: {spot[0]}, Settled: {spot[1]}")
            else:
                print("No capital village found.")


        if action == '1':
            while True:
                print("\nStorage Menu")
                print("1. Single Operation")
                print("2. Loop until Escape")
                print("9. Back to Main Menu")
                sub_action = input("Select sub-action: ")
                if sub_action == '9':
                    break
                loops = int(input("Number of loops: "))
                if sub_action == '1':
                    await increase_storage_async(session_manager.username, session_manager.password, loops, session_manager.conn)
                elif sub_action == '2':
                    loop_task = asyncio.create_task(loop_task_until_escape('1', session_manager, logger.info))
                    try:
                        await asyncio.gather(loop_task)
                    except asyncio.CancelledError:
                        loop_task.cancel()
                        await loop_task

        elif action == '2':
            while True:
                print("\nProduction Menu")
                print("1. Single Operation")
                print("2. Loop until Escape")
                print("9. Back to Main Menu")
                sub_action = input("Select sub-action: ")
                if sub_action == '9':
                    break
                loops = int(input("Number of loops: "))
                if sub_action == '1':
                    await increase_production_async(session_manager.username, session_manager.password, loops, session_manager.conn)
                elif sub_action == '2':
                    loop_task = asyncio.create_task(loop_task_until_escape('2', session_manager, logger.info))
                    try:
                        await asyncio.gather(loop_task)
                    except asyncio.CancelledError:
                        loop_task.cancel()
                        await loop_task

        elif action == '3':
            while True:
                print("\nCombined Operations Menu")
                print("1. Equal Prod + Storage: 6250 of production and 1250 of Storage")
                print("2. Production++: 20000 of production and 2000 of Storage")
                print("3. Storage++: 25000 of storage and 6250 of production")
                print("9. Back to Main Menu")
                combined_action = input("Select combined action: ")
                if combined_action == '9':
                    break
                if combined_action == '1':
                    await increase_production_async(session_manager.username, session_manager.password, 6250, session_manager.conn)
                    await increase_storage_async(session_manager.username, session_manager.password, 1250, session_manager.conn)
                elif combined_action == '2':
                    await increase_production_async(session_manager.username, session_manager.password, 20000, session_manager.conn)
                    await increase_storage_async(session_manager.username, session_manager.password, 2000, session_manager.conn)
                elif combined_action == '3':
                    await increase_storage_async(session_manager.username, session_manager.password, 25000, session_manager.conn)
                    await increase_production_async(session_manager.username, session_manager.password, 6250, session_manager.conn)

        elif action == '4':
            await fetch_villages(session_manager.username, session_manager, session_manager.conn)

        elif action == '5':
            await rename_village(session_manager, session_manager.conn, session_manager.username)

        elif action == '6':
            villages = await fetch_villages(session_manager.username, session_manager, session_manager.conn)
            capital = next((v for v in villages if 'Capital' in v[0]), None)
            if capital:
                await construct_capital(session_manager, capital[1], session_manager.conn)
            else:
                print("No capital village found.")

        elif action == '7':
            villages = await fetch_villages(session_manager.username, session_manager, session_manager.conn)
            print("Select a village to construct:")
            for index, village in enumerate(villages):
                print(f"{index + 1}. {village[0]} (ID: {village[1]})")
            village_choice = int(input("Enter your choice: ")) - 1
            if 0 <= village_choice < len(villages):
                selected_village = villages[village_choice]
                await construct_village(session_manager, selected_village[1], session_manager.conn)
            else:
                print("Invalid choice. Please try again.")

        elif action == '8':
            await research_academy(session_manager)

        elif action == '9':
            await upgrade_smithy(session_manager)

        elif action == '10':
            await upgrade_armory(session_manager)

        elif action == '11':
            delete_all_users(session_manager.conn)
            print("All saved usernames have been deleted.")

        elif action == '12':
            await fetch_villages(session_manager.username, session_manager, session_manager.conn)

        elif action == '13':
            await select_and_attack_village(session_manager, session_manager.conn)

        elif action == '0':
            print("Exiting...")
            break

        else:
            print("Invalid action. Please try again.")

async def login_menu():
    """
    Display the login menu and handle user login.
    """
    conn = init_db()
    while True:
        print("Login Menu")
        print("1. Select a user to login")
        print("2. Login with new credentials")
        print("3. Forget all saved usernames")
        print("0. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            users = get_all_users(conn)
            if users:
                print("Select a user to login:")
                for index, user in enumerate(users, start=1):
                    print(f"{index}. {user[0]}")

                user_choice = int(input("Enter your choice: ")) - 1
                if 0 <= user_choice < len(users):
                    username = users[user_choice][0]
                    cursor = conn.cursor()
                    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
                    password = cursor.fetchone()[0]
                    return SessionManager(username, password, conn)
                else:
                    print("Invalid choice. Please try again.")
            else:
                print("No users found in the database.")
        elif choice == '2':
            username = input("Username: ")
            password = input("Password: ")
            return SessionManager(username, password, conn)
        elif choice == '3':
            delete_all_users(conn)
            print("All saved usernames have been deleted.")
        elif choice == '0':
            print("Exiting...")
            exit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    print("Welcome to Bot for Fun Server")
    session_manager = asyncio.run(login_menu())
    asyncio.run(main_menu(session_manager))
