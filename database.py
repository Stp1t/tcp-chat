import sqlite3

conn = sqlite3.connect('chat_database.db', check_same_thread=False)
cursor = conn.cursor()


def setup_database():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            sender TEXT,
            message TEXT,
            timestamp TEXT,  
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')
    conn.commit()


def save_message(room_name, sender, message, timestamp):
    cursor.execute("SELECT id FROM rooms WHERE name = ?", (room_name,))
    room_id = cursor.fetchone()
    if room_id:
        room_id = room_id[0]
        cursor.execute("INSERT INTO messages (room_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                       (room_id, sender, message, timestamp))
        conn.commit()


def get_chat_history(room_name):
    cursor.execute("SELECT id FROM rooms WHERE name = ?", (room_name,))
    room_id = cursor.fetchone()
    if room_id:
        room_id = room_id[0]
        cursor.execute("SELECT sender, message, timestamp FROM messages WHERE room_id = ? ORDER BY timestamp ASC",
                       (room_id,))
        return cursor.fetchall()
    return []


def add_room(room_name):
    cursor.execute("INSERT OR IGNORE INTO rooms (name) VALUES (?)", (room_name,))
    conn.commit()


def get_all_rooms():
    cursor.execute("SELECT name FROM rooms")
    return cursor.fetchall()
