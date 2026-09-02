import os
import json
import threading
import requests
from flask import Flask, redirect, session, request, render_template_string
import discord
from discord.ext import commands
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

# --------------------------------------------------
# 1. الإعدادات وإدارة الحفظ
# --------------------------------------------------

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey12345")
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

API_BASE_URL = "https://discord.com/api/v10"
CONFIG_FILE = "guilds_config.json"

def load_configs():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_configs():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(GUILDS_CONFIG, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[Config Save Error] {e}")

GUILDS_CONFIG = load_configs()

# --------------------------------------------------
# 2. إعدادات بوت ديسكورد (Discord Bot)
# --------------------------------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

def run_bot():
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("Error: BOT_TOKEN is missing!")

# --------------------------------------------------
# 3. لوحة التحكم (Flask Web Server)
# --------------------------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>TikTok Bot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; text-align: center; padding: 50px; }
        .card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
        .btn { background-color: #ff0050; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 15px; }
        select, input { padding: 10px; margin: 10px 0; width: 80%; border-radius: 5px; border: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>TikTok Bot 🎵</h2>
        {% if not logged_in %}
            <p>سجل الدخول بواسطة ديسكورد للتحكم باللوحة</p>
            <a class="btn" href="/login">دخول بحساب Discord</a>
        {% else %}
            <h3>أهلاً بك، {{ user['username'] }}</h3>
            <form action="/save-settings" method="POST">
                <label>اختر السيرفر:</label><br>
                <select name="guild_id">
                    {% for guild in guilds %}
                        <option value="{{ guild['id'] }}">{{ guild['name'] }}</option>
                    {% endfor %}
                </select><br>

                <label>رقم روم التنبيهات (Channel ID):</label><br>
                <input type="text" name="channel_id" placeholder="123456789..." required><br>

                <label>عنوان التنبيه:</label><br>
                <input type="text" name="top_title" placeholder="بث جديد للأن!"><br>

                <button type="submit" class="btn">حفظ الإعدادات</button>
            </form>
            <br>
            <a href="/logout" style="color: #bbb;">تسجيل الخروج</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    logged_in = 'user' in session
    user = session.get('user', None)
    guilds = session.get('guilds', [])
    return render_template_string(DASHBOARD_HTML, logged_in=logged_in, user=user, guilds=guilds)

@app.route('/login')
def login():
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        token_res = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
        access_token = token_res.json().get('access_token')

        if not access_token:
            print(f"[Auth Error Token Response]: {token_res.json()}")
            return redirect('/')

        user_headers = {'Authorization': f"Bearer {access_token}"}
        user_data = requests.get(f"{API_BASE_URL}/users/@me", headers=user_headers).json()
        all_guilds = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers=user_headers).json()

        filtered_guilds = []
        if isinstance(all_guilds, list):
            for g in all_guilds:
                permissions = int(g.get('permissions', 0))
                if (permissions & 0x8) == 0x8 or g.get('owner', False):
                    filtered_guilds.append({'id': str(g['id']), 'name': g['name'], 'icon': g.get('icon')})

        session['user'] = {'id': user_data.get('id'), 'username': user_data.get('username'), 'avatar': user_data.get('avatar')}
        session['guilds'] = filtered_guilds

    except Exception as e:
        print(f"[Auth Exception Error]: {e}")

    return redirect('/')

@app.route('/save-settings', methods=['POST'])
def save_settings():
    if 'user' not in session:
        return redirect('/login')

    guild_id = request.form.get('guild_id')
    if not guild_id and session.get('guilds'):
        guild_id = session['guilds'][0]['id']

    if guild_id:
        GUILDS_CONFIG[str(guild_id)] = {
            "channel_id": request.form.get('channel_id'),
            "top_title": request.form.get('top_title')
        }
        save_configs()
        return redirect(f'/?guild_id={guild_id}')

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --------------------------------------------------
# 4. تشغيل البوت واللوحة معاً
# --------------------------------------------------

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port)
