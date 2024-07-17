import sqlite3

def init_db():
    conn = sqlite3.connect('game.db')
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

    # Insert initial building data
    buildings = [
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

    conn.commit()
    return conn

def save_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

def save_task(conn, username, task_type, loops):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (username, task_type, loops) VALUES (?, ?, ?)", (username, task_type, loops))
    conn.commit()

def save_stats(conn, username, task_type, requested, completed):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stats (username, task_type, requested, completed) VALUES (?, ?, ?, ?)", (username, task_type, requested, completed))
    conn.commit()

def save_village(conn, username, village_id, village_name, x_coord, y_coord):
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO villages (username, village_id, village_name, x_coord, y_coord) VALUES (?, ?, ?, ?, ?)", (username, village_id, village_name, x_coord, y_coord))
    conn.commit()

def get_user(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    return cursor.fetchone()

def get_tasks(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE username=?", (username,))
    return cursor.fetchall()

def get_stats(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stats WHERE username=?", (username,))
    return cursor.fetchall()

def get_villages(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM villages WHERE username=?", (username,))
    return cursor.fetchall()

def get_buildings(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buildings")
    return cursor.fetchall()
