import sqlite3

DB_NAME = 'subscriptions.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            guild_id TEXT,
            channel_id TEXT,
            tiktok_username TEXT,
            PRIMARY KEY (guild_id, tiktok_username)
        )
    ''')
    conn.commit()
    conn.close()

def add_subscription(guild_id, channel_id, tiktok_username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO subscriptions (guild_id, channel_id, tiktok_username)
        VALUES (?, ?, ?)
    ''', (guild_id, channel_id, tiktok_username))
    conn.commit()
    conn.close()

def delete_subscription(guild_id, tiktok_username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM subscriptions 
        WHERE guild_id = ? AND tiktok_username = ?
    ''', (guild_id, tiktok_username))
    conn.commit()
    conn.close()

def get_all_subscriptions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT guild_id, channel_id, tiktok_username FROM subscriptions')
    rows = cursor.fetchall()
    conn.close()
    return rows