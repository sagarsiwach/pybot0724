# troop_training.py

import httpx
import logging

BASE_URL = "https://fun.gotravspeed.com"

troop_ids = {
    'roman': {
        'legionnaire': 't[1]',
        'praetorian': 't[2]',
        'imperian': 't[3]',
        'equites legati': 't[4]',
        'equites imperatoris': 't[5]',
        'equites caesaris': 't[6]',
        'ram': 't[7]',
        'catapult': 't[8]',
        'senator': 't[9]',
        'settler': 't[0]'
    },
    'teuton': {
        'clubswinger': 't[11]',
        'spearman': 't[12]',
        'axeman': 't[13]',
        'scout': 't[14]',
        'paladin': 't[15]',
        'teutonic knight': 't[16]',
        'ram': 't[17]',
        'catapult': 't[18]',
        'chief': 't[19]',
        'settler': 't[10]'
    },
    'gaul': {
        'phalanx': 't[21]',
        'swordsman': 't[22]',
        'pathfinder': 't[23]',
        'theutates thunder': 't[24]',
        'druidrider': 't[25]',
        'haeduan': 't[26]',
        'ram': 't[27]',
        'catapult': 't[28]',
        'chieftain': 't[29]',
        'settler': 't[20]'
    }
}

async def train_troops(cookies, village_id, civilization, troop_type):
    async def send_train_request(session, troop_id):
        url = f"https://fun.gotravspeed.com/build.php?id=25"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
        data = f"{troop_id}=10&s1.x=50&s1.y=8"  # Adjust the number of troops as needed

        response = await session.post(url, headers=headers, data=data)
        if response.status_code == 200:
            logging.info(f"Training {troop_type} in the current village")
        else:
            logging.error(f"Error during {troop_type} training: {response.status_code}")

    troop_id = troop_ids[civilization].get(troop_type)
    if not troop_id:
        logging.error(f"Invalid troop type: {troop_type}")
        return

    async with httpx.AsyncClient(cookies=cookies) as session:
        tasks = [send_train_request(session, troop_id) for _ in range(3)]
        await asyncio.gather(*tasks)
