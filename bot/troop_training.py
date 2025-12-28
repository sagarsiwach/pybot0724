# troop_training.py
"""
Troop training module for Travian.

Supports all tribes: Roman, Teuton, Gaul
"""

import asyncio
import httpx
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# Troop form input names by tribe
# These are the input field names in the training form (t[1], t[2], etc.)
TROOP_IDS = {
    'roman': {
        'legionnaire': 1,
        'praetorian': 2,
        'imperian': 3,
        'equites_legati': 4,
        'equites_imperatoris': 5,
        'equites_caesaris': 6,
        'ram': 7,
        'catapult': 8,
        'senator': 9,
        'settler': 10,
    },
    'teuton': {
        'clubswinger': 1,
        'spearman': 2,
        'axeman': 3,
        'scout': 4,
        'paladin': 5,
        'teutonic_knight': 6,
        'ram': 7,
        'catapult': 8,
        'chief': 9,
        'settler': 10,
    },
    'gaul': {
        'phalanx': 1,
        'swordsman': 2,
        'pathfinder': 3,
        'theutates_thunder': 4,
        'druidrider': 5,
        'haeduan': 6,
        'ram': 7,
        'catapult': 8,
        'chieftain': 9,
        'settler': 10,
    }
}

# Building positions for training (may vary by village)
TRAINING_BUILDINGS = {
    'barracks': 19,      # Infantry
    'stable': 20,        # Cavalry
    'siege_workshop': 21, # Siege weapons
    'residence': 25,     # Settlers
    'palace': 26,        # Settlers (capital)
}


async def get_training_page(client, server_url: str, building_position: int):
    """Fetch the training page and extract form data."""
    response = await client.get(f"{server_url}/build.php?id={building_position}")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get building name
    h1 = soup.find('h1')
    building_name = h1.text.strip() if h1 else "Unknown"
    
    # Find training form
    form = soup.find('form', {'action': 'build.php'})
    
    # Get CSRF token (hidden input or from s1 button)
    csrf = None
    if form:
        hidden = form.find('input', {'type': 'hidden'})
        if hidden:
            csrf = hidden.get('value')
    
    # Get available troops (input fields)
    available_troops = []
    troop_inputs = soup.find_all('input', {'name': lambda x: x and x.startswith('t[')})
    for inp in troop_inputs:
        name = inp.get('name', '')
        max_val = inp.get('maxlength', '0')
        # Try to find troop name from parent elements
        parent = inp.find_parent('tr') or inp.find_parent('div')
        if parent:
            img = parent.find('img', class_='unit')
            troop_name = img.get('alt', name) if img else name
            available_troops.append({
                'input_name': name,
                'troop_name': troop_name,
            })
    
    return {
        'building': building_name,
        'form': form,
        'csrf': csrf,
        'troops': available_troops,
        'html': response.text
    }


async def train_troops(cookies, server_url: str, building_position: int, troop_input: str, amount: int, callback=None):
    """
    Train troops at a specific building.
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        building_position: Position of barracks/stable/etc (19, 20, 21, etc.)
        troop_input: Input field name (e.g., 't[1]' for first troop type)
        amount: Number of troops to train
        callback: Optional callback for logging
    
    Returns:
        True if training was successful
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        # Get the training page to find the form
        response = await client.get(f"{server_url}/build.php?id={building_position}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Build form data
        form_data = {
            troop_input: str(amount),
            's1.x': '50',
            's1.y': '10',
        }
        
        # Submit training
        response = await client.post(f"{server_url}/build.php?id={building_position}", data=form_data)
        
        if response.status_code == 200:
            if callback:
                callback(f"Training {amount} troops ({troop_input}) at position {building_position}")
            logger.info(f"Training {amount} troops at position {building_position}")
            return True
        else:
            if callback:
                callback(f"Training failed: HTTP {response.status_code}")
            logger.error(f"Training failed: HTTP {response.status_code}")
            return False


async def train_max_troops(cookies, server_url: str, building_position: int, troop_index: int = 1, loops: int = 1, callback=None):
    """
    Train maximum troops continuously.
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        building_position: Barracks/Stable position
        troop_index: Which troop to train (1-10)
        loops: How many times to queue training
        callback: Progress callback
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        troop_input = f't[{troop_index}]'
        
        for i in range(loops):
            # Get training page to see max available
            response = await client.get(f"{server_url}/build.php?id={building_position}")
            
            # Just train a batch (game shows max available in the input maxlength)
            form_data = {
                troop_input: '999999',  # Will be capped to max available
                's1.x': '50',
                's1.y': '10',
            }
            
            response = await client.post(f"{server_url}/build.php?id={building_position}", data=form_data)
            
            if response.status_code == 200:
                if callback:
                    callback(f"Training batch {i+1}/{loops} at position {building_position}")
            else:
                if callback:
                    callback(f"Training failed in loop {i+1}")
                break


async def train_settlers(cookies, server_url: str, residence_position: int = 25, count: int = 3, callback=None):
    """
    Train settlers in Residence/Palace.
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        residence_position: Position of Residence (usually 25) or Palace (26)
        count: Number of settlers to train (usually 3 for settling)
        callback: Progress callback
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        # Get residence page
        response = await client.get(f"{server_url}/build.php?id={residence_position}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find settler input - it's usually t[10] but check the page
        settler_input = None
        for inp in soup.find_all('input'):
            name = inp.get('name', '')
            if name.startswith('t['):
                # Check if this is settler row
                parent = inp.find_parent('tr')
                if parent and 'settler' in parent.text.lower():
                    settler_input = name
                    break
        
        if not settler_input:
            # Default to t[10]
            settler_input = 't[10]'
        
        # Train settlers
        form_data = {
            settler_input: str(count),
            's1.x': '50',
            's1.y': '10',
        }
        
        response = await client.post(f"{server_url}/build.php?id={residence_position}", data=form_data)
        
        if response.status_code == 200:
            if callback:
                callback(f"Training {count} settlers")
            logger.info(f"Training {count} settlers")
            return True
        else:
            if callback:
                callback(f"Failed to train settlers: HTTP {response.status_code}")
            return False
