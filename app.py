import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'my_local_pc_secret_key'

CLIENT_ID = '1544289467853045861'
CLIENT_SECRET = 'ATbNyxdCRnjH8ItEog61XNCxGXTc25_H'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
DISCORD_BOT_TOKEN = 'MTU0NDI4OTQ2Nzg1MzA0NTg2MQ.Gy9z8P.79IVHdLyiitKCKLpCRkea6EoRWt_ftp_iM_dw8'
DISCORD_API_BASE = 'https://discord.com/api/v10'

def get_all_subscriptions():
    try:
        conn = sqlite3.connect('subscriptions.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                guild_id TEXT,
                channel_id TEXT,
                tiktok_username TEXT,
                PRIMARY KEY (guild_id, tiktok_username)
            )
        ''')
        cursor.execute('SELECT guild_id, channel_id, tiktok_username FROM subscriptions')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Database error:", e)
        return []

@app.route('/')
def index():
    user = session.get('user')
    guilds = session.get('guilds', [])
    subscriptions = get_all_subscriptions()
    return render_template('index.html', user=user, guilds=guilds, subscriptions=subscriptions)

@app.route('/login')
def login():
    discord_login_url = (
        f"{DISCORD_API_BASE}/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{DISCORD_API_BASE}/oauth2/token", data=data, headers=headers)
    access_token = r.json().get('access_token')

    if not access_token:
        return redirect(url_for('index'))

    headers_auth = {'Authorization': f'Bearer {access_token}'}
    user_req = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=headers_auth)
    guilds_req = requests.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers_auth)

    raw_guilds = guilds_req.json()
    clean_guilds = []
    if isinstance(raw_guilds, list):
        for g in raw_guilds:
            perms = int(g.get('permissions', 0))
            if (perms & 0x8) == 0x8 or (perms & 0x20) == 0x20 or g.get('owner', False):
                clean_guilds.append({'id': str(g.get('id')), 'name': g.get('name')})

    session['user'] = user_req.json()
    session['guilds'] = clean_guilds
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_subscription():
    if 'user' not in session:
        return redirect(url_for('login'))
    guild_id = request.form.get('guild_id')
    channel_id = request.form.get('channel_id')
    tiktok_username = request.form.get('tiktok_username')
    if guild_id and channel_id and tiktok_username:
        conn = sqlite3.connect('subscriptions.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO subscriptions VALUES (?, ?, ?)", (guild_id, channel_id, tiktok_username))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<guild_id>/<tiktok_username>', methods=['POST'])
def delete_subscription(guild_id, tiktok_username):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE guild_id = ? AND tiktok_username = ?", (guild_id, tiktok_username))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("Running Flask Server...")
    app.run(host='127.0.0.1', port=5000, debug=True)