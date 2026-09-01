import os
import json
import threading
import requests
from flask import Flask, redirect, session, request, render_template_string
import discord
from discord.ext import commands
from waitress import serve

# -------------------------------------------------------------------
# 1. الإعدادات وإدارة الحفظ
# -------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey12345")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

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
        print(f"[Save Error] {e}")

GUILDS_CONFIG = load_configs()

# -------------------------------------------------------------------
# 2. إعداد بوت الديسكورد
# -------------------------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[Discord Bot] تم تسجيل الدخول بنجاح باسم: {bot.user}")

async def send_top_active_users(guild_id):
    config = GUILDS_CONFIG.get(str(guild_id))
    if not config or not config.get("channel_id"):
        return False

    try:
        channel = bot.get_channel(int(config["channel_id"]))
        if not channel:
            channel = await bot.fetch_channel(int(config["channel_id"]))
    except Exception as e:
        print(f"[Channel Error] {e}")
        return False

    embed = discord.Embed(
        title=config.get("top_title", "🏆 إشعار البث المباشر"),
        description="تم التحديث بنجاح من لوحة التحكم!",
        color=discord.Color.from_rgb(254, 44, 85)
    )
    
    try:
        await channel.send(embed=embed)
        return True
    except Exception as e:
        print(f"[Send Error] {e}")
        return False

# -------------------------------------------------------------------
# 3. تصميم اللوحة
# -------------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>TikTok Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; }
        body { background-color: #121212; color: #ffffff; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background-color: #000000; padding: 25px 20px; display: flex; flex-direction: column; justify-content: space-between; border-left: 1px solid #222222; }
        .brand { font-size: 22px; font-weight: 800; color: #ffffff; margin-bottom: 35px; text-align: center; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .brand i { color: #FE2C55; text-shadow: -2px 0 #25F4EE; }
        .nav-links { list-style: none; }
        .nav-links li { margin-bottom: 12px; }
        .nav-links a { color: #a6a6a6; text-decoration: none; padding: 14px 18px; display: flex; align-items: center; gap: 12px; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; }
        .nav-links a.active { background: linear-gradient(90deg, rgba(254,44,85,0.15) 0%, rgba(37,244,238,0.15) 100%); color: #ffffff; border-right: 4px solid #FE2C55; }
        .main-content { flex: 1; padding: 40px; overflow-y: auto; background-color: #121212; }
        .card { background-color: #1a1a1a; padding: 30px; border-radius: 16px; max-width: 650px; border: 1px solid #2a2a2a; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 25px; }
        .form-group { margin-bottom: 22px; text-align: right; }
        label { display: block; margin-bottom: 10px; color: #b0b0b0; font-size: 14px; }
        input[type="text"], select { width: 100%; padding: 14px 18px; border-radius: 10px; border: 1px solid #333333; background-color: #000000; color: #ffffff; font-size: 15px; text-align: right; }
        .btn-tiktok { background: linear-gradient(45deg, #FE2C55, #ff4468); color: #ffffff; padding: 14px 24px; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-size: 15px; }
        .btn-cyan { background: #25F4EE; color: #000000; padding: 14px 24px; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-size: 15px; margin-top: 15px; }
        .user-info { display: flex; align-items: center; gap: 14px; padding-top: 20px; border-top: 1px solid #222222; }
        .user-info img { border-radius: 50%; width: 48px; height: 48px; border: 2px solid #FE2C55; }
    </style>
</head>
<body>
    {% if user %}
    <div class="sidebar">
        <div>
            <div class="brand"><i class="fa-brands fa-tiktok"></i><span>TikTok Bot</span></div>
            <ul class="nav-links">
                <li><a class="active"><i class="fa-solid fa-sliders"></i> الإعدادات العامة</a></li>
            </ul>
        </div>
        <div class="user-info">
            {% if user.avatar %}
            <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
            {% else %}
            <img src="https://cdn.discordapp.com/embed/avatars/0.png" alt="Avatar">
            {% endif %}
            <div>
                <p style="font-weight: 700; font-size: 14px;">{{ user.username }}</p>
                <a href="/logout" style="color: #FE2C55; font-size: 12px; text-decoration: none; font-weight: 600;">تسجيل الخروج</a>
            </div>
        </div>
    </div>

    <div class="main-content">
        <h1 style="margin-bottom: 25px; font-weight: 800; font-size: 26px;">⚙️ إعدادات البوت والسيرفرات</h1>
        <div class="card">
            <form action="/save-settings" method="POST">
                <div class="form-group">
                    <label>اختر السيرفر:</label>
                    <select name="guild_id" onchange="window.location.href='/?guild_id=' + this.value">
                        {% for guild in guilds %}
                            <option value="{{ guild.id }}" {% if selected_guild_id == guild.id %}selected{% endif %}>
                                {{ guild.name }}
                            </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>معرف قناة الديسكورد (Channel ID):</label>
                    <input type="text" name="channel_id" value="{{ current_config.channel_id or '' }}" placeholder="123456789012345678" required>
                </div>
                <div class="form-group">
                    <label>عنوان رسالة الإشعار:</label>
                    <input type="text" name="top_title" value="{{ current_config.top_title or '🏆 إشعار البث المباشر' }}" required>
                </div>
                <button type="submit" class="btn-tiktok"><i class="fa-solid fa-check"></i> حفظ إعدادات السيرفر</button>
            </form>
            
            {% if selected_guild_id %}
                <hr style="border-color: #222; margin: 25px 0;">
                <a href="/trigger-top?guild_id={{ selected_guild_id }}" class="btn-cyan"><i class="fa-solid fa-paper-plane"></i> إرسال تجربة للقناة</a>
            {% endif %}
        </div>
    </div>
    {% else %}
    <div style="margin: auto; text-align: center;">
        <div class="card" style="width: 380px;">
            <div class="brand" style="margin-bottom: 20px;"><i class="fa-brands fa-tiktok" style="font-size: 32px;"></i><span style="font-size: 26px;">TikTok Bot</span></div>
            <p style="color: #888888; margin-bottom: 25px;">سجل الدخول بواسطة ديسكورد للتحكم باللوحة</p>
            <a href="/login" class="btn-tiktok" style="justify-content: center; width: 100%;"><i class="fa-brands fa-discord"></i> دخول بحساب Discord</a>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

# -------------------------------------------------------------------
# 4. مسارات Flask
# -------------------------------------------------------------------
@app.route('/')
def index():
    user_guilds = session.get('guilds', [])
    selected_guild_id = request.args.get('guild_id')
    
    if not selected_guild_id and user_guilds:
        selected_guild_id = user_guilds[0]['id']
        
    current_config = GUILDS_CONFIG.get(str(selected_guild_id), {})

    return render_template_string(
        DASHBOARD_HTML,
        user=session.get('user'),
        guilds=user_guilds,
        selected_guild_id=selected_guild_id,
        current_config=current_config
    )

@app.route('/login')
def login():
    scope = "identify guilds"
    discord_auth_url = (
        f"{API_BASE_URL}/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope}"
    )
    return redirect(discord_auth_url)

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
            return redirect('/')

        user_headers = {'Authorization': f"Bearer {access_token}"}
        user_data = requests.get(f"{API_BASE_URL}/users/@me", headers=user_headers).json()
        all_guilds = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers=user_headers).json()

        filtered_guilds = []
        if isinstance(all_guilds, list):
            for g in all_guilds:
                permissions = int(g.get('permissions', 0))
                if (permissions & 0x8) == 0x8 or g.get('owner', False):
                    filtered_guilds.append({'id': g['id'], 'name': g['name'], 'icon': g.get('icon')})

        session['user'] = {'id': user_data.get('id'), 'username': user_data.get('username'), 'avatar': user_data.get('avatar')}
        session['guilds'] = filtered_guilds
    except Exception as e:
        print(f"[Auth Error] {e}")

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

@app.route('/trigger-top')
def trigger_top():
    guild_id = request.args.get('guild_id')
    if 'user' in session and bot.loop and guild_id:
        bot.loop.create_task(send_top_active_users(guild_id))
    return redirect(f'/?guild_id={guild_id}')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------------------------------------------------------
# 5. تشغيل التطبيق
# -------------------------------------------------------------------
def run_discord_bot():
    if BOT_TOKEN:
        try:
            bot.run(BOT_TOKEN)
        except Exception as e:
            print(f"[Discord Bot Error] {e}")

    if __name__ == '__main__':
    threading.Thread(target=run_discord_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
