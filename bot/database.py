import sqlite3

def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_type TEXT,
        loops INTEGER,
        FOREIGN KEY (username) REFERENCES users(username)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task_type TEXT,
        requested INTEGER,
        completed INTEGER,
        FOREIGN KEY (username) REFERENCES users(username)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS villages (
        username TEXT,
        village_id INTEGER,
        village_name TEXT,
        x_coord INTEGER,
        y_coord INTEGER,
        PRIMARY KEY (username, village_id),
        FOREIGN KEY (username) REFERENCES users(username)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buildings (
        pid INTEGER,
        bid INTEGER,
        tgt INTEGER,
        name TEXT
    )''')

    # Insert initial building data including resource fields
    buildings = [
        # Resource fields
        (1, 1, 30, 'Woodcutter'),
        (2, 2, 30, 'Woodcutter'),
        (3, 3, 30, 'Woodcutter'),
        (4, 4, 30, 'Woodcutter'),
        (5, 5, 30, 'Clay Pit'),
        (6, 6, 30, 'Clay Pit'),
        (7, 7, 30, 'Clay Pit'),
        (8, 8, 30, 'Clay Pit'),
        (9, 9, 30, 'Iron Mine'),
        (10, 10, 30, 'Iron Mine'),
        (11, 11, 30, 'Iron Mine'),
        (12, 12, 30, 'Iron Mine'),
        (13, 13, 30, 'Cropland'),
        (14, 14, 30, 'Cropland'),
        (15, 15, 30, 'Cropland'),
        (16, 16, 30, 'Cropland'),
        (17, 17, 30, 'Cropland'),
        (18, 18, 30, 'Cropland'),
        # Existing buildings
        (26, 15, 20, 'Main Building'),
        (39, 16, 20, 'Rally Point'),
        (40, 33, 20, 'City Wall'),
        (25, 19, 20, 'Barracks'),
        (33, 22, 20, 'Academy'),
        (30, 25, 20, 'Residence'),
        (29, 13, 20, 'Armory'),
        (21, 12, 20, 'Smithy'),
        (34, 7, 20, 'Iron Foundry'),
        (31, 5, 20, 'Sawmill'),
        (27, 6, 20, 'Brickworks'),
        (24, 37, 20, "Hero's Mansion"),
        (24, 44, 1, 'Christmas Tree'),
        (22, 11, 20, 'Granary'),
        (20, 17, 20, 'Marketplace'),
        (19, 20, 20, 'Stable'),
        (28, 21, 20, 'Siege Workshop'),
        (32, 14, 20, 'Tournament Square'),
        (35, 24, 20, 'Town Hall'),
        (38, 18, 20, 'Embassy'),
        (37, 27, 20, 'Treasure')
    ]

    cursor.executemany('INSERT INTO buildings (pid, bid, tgt, name) VALUES (?, ?, ?, ?)', buildings)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empty_spots (
            id INTEGER PRIMARY KEY,
            settled INTEGER
        )''')

    conn.commit()
    return conn

def save_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    return cursor.fetchall()


def save_task(conn, username, task_type, loops):
    """
    Save a task to the database.
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (username, task_type, loops) VALUES (?, ?, ?)", (username, task_type, loops))
    conn.commit()


def save_stats(conn, username, task_type, requested, completed):
    """
    Save statistics to the database.
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stats (username, task_type, requested, completed) VALUES (?, ?, ?, ?)",
                   (username, task_type, requested, completed))
    conn.commit()


def save_village(conn, username, village_id, village_name, x_coord, y_coord):
    """
    Save a village's information to the database.
    """
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO villages (username, village_id, village_name, x_coord, y_coord) VALUES (?, ?, ?, ?, ?)",
                   (username, village_id, village_name, x_coord, y_coord))
    conn.commit()


def get_user(conn, username):
    """
    Retrieve a user's information from the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    return cursor.fetchone()


def get_tasks(conn, username):
    """
    Retrieve all tasks for a user from the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE username=?", (username,))
    return cursor.fetchall()


def get_stats(conn, username):
    """
    Retrieve all statistics for a user from the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stats WHERE username=?", (username,))
    return cursor.fetchall()


def get_villages(conn, username):
    """
    Retrieve all villages for a user from the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM villages WHERE username=?", (username,))
    return cursor.fetchall()


def get_buildings(conn):
    """
    Retrieve all buildings from the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buildings")
    return cursor.fetchall()

def delete_all_users(conn):
    """
    Delete all saved usernames from the database.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()


def delete_all_villages_for_user(conn, username):
    """
    Delete all village data for a specific user.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM villages WHERE username=?", (username,))
    conn.commit()

def save_empty_spot(conn, village_id, settled):
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO empty_spots (id, settled) VALUES (?, ?)", (village_id, settled))
    conn.commit()

def get_all_empty_spots(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empty_spots")
    return cursor.fetchall()

def delete_all_empty_spots(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empty_spots")
    conn.commit()
