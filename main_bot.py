import os
import threading
import requests
from flask import Flask, redirect, session, request, render_template_string
import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent

# -------------------------------------------------------------------
# 1. الإعدادات ومتغيرات البيئة
# -------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey12345")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME", "2vce4")

API_BASE_URL = "https://discord.com/api/v10"

# قاموس لتخزين إعدادات كل سيرفر بناءً على ID السيرفر
# الهيكل: { guild_id: {"channel_id": "...", "top_title": "..."} }
GUILDS_CONFIG = {}
user_activity = {}

# -------------------------------------------------------------------
# 2. بوت الديسكورد والتيك توك
# -------------------------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tiktok_client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)

@tiktok_client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    global user_activity
    user_activity.clear()
    print(f"[TikTok] تم الاتصال ببث: {TIKTOK_USERNAME}")

@tiktok_client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    user = event.user.nickname or event.user.unique_id
    user_activity[user] = user_activity.get(user, 0) + 1

async def send_top_active_users(guild_id):
    config = GUILDS_CONFIG.get(str(guild_id))
    if not config or not config.get("channel_id"):
        return False

    channel = bot.get_channel(int(config["channel_id"]))
    if not channel or not user_activity:
        return False

    sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:3]
    embed = discord.Embed(title=config.get("top_title", "🏆 أفضل المتفاعلين"), color=discord.Color.from_rgb(254, 44, 85))
    medals = ["🥇 المركز الأول", "🥈 المركز الثاني", "🥉 المركز الثالث"]
    
    for idx, (username, count) in enumerate(sorted_users):
        embed.add_field(
            name=f"{medals[idx]}: {username}",
            value=f"عدد الرسائل: **{count}**",
            inline=False
        )

    await channel.send(embed=embed)
    return True

# -------------------------------------------------------------------
# 3. تصميم اللوحة بثيم تيك توك وتدعم التعدد
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
        .nav-links a { color: #a6a6a6; text-decoration: none; padding: 14px 18px; display: flex; align-items: center; gap: 12px; border-radius: 10px; font-size: 15px; font-weight: 600; transition: all 0.25s ease; cursor: pointer; }
        .nav-links a:hover { color: #ffffff; background: #1a1a1a; }
        .nav-links a.active { background: linear-gradient(90deg, rgba(254,44,85,0.15) 0%, rgba(37,244,238,0.15) 100%); color: #ffffff; border-right: 4px solid #FE2C55; }
        .nav-links a.active i { color: #25F4EE; }
        
        .main-content { flex: 1; padding: 40px; overflow-y: auto; background-color: #121212; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .card { background-color: #1a1a1a; padding: 30px; border-radius: 16px; max-width: 650px; border: 1px solid #2a2a2a; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 25px; }
        .form-group { margin-bottom: 22px; text-align: right; }
        label { display: block; margin-bottom: 10px; color: #b0b0b0; font-size: 14px; font-weight: 500; }
        
        input[type="text"] {
            width: 100%;
            padding: 14px 18px;
            border-radius: 10px;
            border: 1px solid #333333;
            background-color: #000000;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            transition: 0.2s;
        }

        .select-wrapper {
            position: relative;
            width: 100%;
        }

        .select-wrapper::after {
            content: '\\f078';
            font-family: 'Font Awesome 6 Free';
            font-weight: 900;
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: #FE2C55;
            pointer-events: none;
            font-size: 14px;
        }

        select { 
            width: 100%; 
            padding: 14px 18px; 
            padding-left: 45px;
            border-radius: 10px; 
            border: 1px solid #333333; 
            background-color: #000000; 
            color: #ffffff; 
            font-size: 15px; 
            outline: none; 
            transition: 0.2s;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            cursor: pointer;
            text-align: right;
            direction: rtl;
        }
        
        select option {
            background-color: #141414;
            color: #ffffff;
            padding: 12px;
        }

        input[type="text"]:focus, select:focus { 
            border-color: #25F4EE; 
            box-shadow: 0 0 8px rgba(37,244,238,0.3); 
        }
        
        .btn-tiktok { background: linear-gradient(45deg, #FE2C55, #ff4468); color: #ffffff; padding: 14px 24px; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-size: 15px; transition: 0.3s; box-shadow: 0 4px 15px rgba(254,44,85,0.3); }
        .btn-tiktok:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(254,44,85,0.5); }
        
        .btn-cyan { background: #25F4EE; color: #000000; padding: 14px 24px; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 10px; font-size: 15px; transition: 0.3s; }
        .btn-cyan:hover { background: #1ee0da; transform: translateY(-2px); }

        .user-info { display: flex; align-items: center; gap: 14px; padding-top: 20px; border-top: 1px solid #222222; }
        .user-info img { border-radius: 50%; width: 48px; height: 48px; border: 2px solid #FE2C55; }

        .leaderboard-list { list-style: none; margin-top: 20px; }
        .leaderboard-item { background: #000000; padding: 18px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #282828; }
        .badge { background: #FE2C55; color: #ffffff; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; }
    </style>
</head>
<body>

    {% if user %}
    <div class="sidebar">
        <div>
            <div class="brand">
                <i class="fa-brands fa-tiktok"></i>
                <span>TikTok Bot</span>
            </div>
            <ul class="nav-links">
                <li><a onclick="showTab('settings')" id="nav-settings" class="active"><i class="fa-solid fa-sliders"></i> الإعدادات العامة</a></li>
                <li><a onclick="showTab('top3')" id="nav-top3"><i class="fa-solid fa-fire"></i> أوب توب البث (Top 3)</a></li>
            </ul>
        </div>
        <div class="user-info">
            <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
            <div>
                <p style="font-weight: 700; font-size: 14px;">{{ user.username }}</p>
                <a href="/logout" style="color: #FE2C55; font-size: 12px; text-decoration: none; font-weight: 600;">تسجيل الخروج</a>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div id="settings" class="tab-content active">
            <h1 style="margin-bottom: 25px; font-weight: 800; font-size: 26px;">⚙️ إعدادات البوت والربط</h1>
            <div class="card">
                <form action="/save-settings" method="POST">
                    <div class="form-group">
                        <label>اختر السيرفر المراد تعديله:</label>
                        <div class="select-wrapper">
                            <select name="guild_id" onchange="window.location.href='/?guild_id=' + this.value">
                                <option value="" disabled {% if not selected_guild_id %}selected{% endif %}>-- اختر سيرفر --</option>
                                {% for guild in guilds %}
                                    <option value="{{ guild.id }}" {% if selected_guild_id == guild.id %}selected{% endif %}>
                                        {{ guild.name }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>معرف قناة الديسكورد (Channel ID):</label>
                        <input type="text" name="channel_id" value="{{ current_config.channel_id or '' }}" placeholder="123456789012345678" required>
                    </div>
                    <div class="form-group">
                        <label>عنوان رسالة التفاعل:</label>
                        <input type="text" name="top_title" value="{{ current_config.top_title or '🏆 أفضل 3 متفاعلين في البث الحالي' }}" required>
                    </div>
                    <button type="submit" class="btn-tiktok"><i class="fa-solid fa-check"></i> حفظ إعدادات السيرفر</button>
                </form>
            </div>
        </div>

        <div id="top3" class="tab-content">
            <h1 style="margin-bottom: 25px; font-weight: 800; font-size: 26px;">🔥 أفضل المتفاعلين في البث</h1>
            <div class="card">
                <p style="color: #888888; margin-bottom: 15px;">يتم فرز أكثر الأشخاص كتابة للتعليقات تلقائياً من البث المباشر.</p>
                <ul class="leaderboard-list">
                    {% if top_users %}
                        {% for user, count in top_users %}
                            <li class="leaderboard-item">
                                <span style="font-size: 16px;"><strong>#{{ loop.index }}</strong> {{ user }}</span>
                                <span class="badge">{{ count }} تعليق</span>
                            </li>
                        {% endfor %}
                    {% else %}
                        <li class="leaderboard-item" style="justify-content: center; color: #777777;">لا يوجد متفاعلين حالياً في البث</li>
                    {% endif %}
                </ul>
                <br>
                {% if selected_guild_id %}
                    <a href="/trigger-top?guild_id={{ selected_guild_id }}" class="btn-cyan"><i class="fa-solid fa-paper-plane"></i> إرسال القائمة لهذا السيرفر</a>
                {% else %}
                    <p style="color: #FE2C55;">قم باختيار سيرفر أولاً لإرسال الرسالة إليه.</p>
                {% endif %}
            </div>
        </div>
    </div>
    {% else %}
    <div style="margin: auto; text-align: center;">
        <div class="card" style="width: 380px;">
            <div class="brand" style="margin-bottom: 20px;">
                <i class="fa-brands fa-tiktok" style="font-size: 32px;"></i>
                <span style="font-size: 26px;">TikTok Bot</span>
            </div>
            <p style="color: #888888; margin-bottom: 25px;">سجل الدخول بواسطة ديسكورد للتحكم باللوحة والإشعارات</p>
            <a href="/login" class="btn-tiktok" style="justify-content: center; width: 100%;"><i class="fa-brands fa-discord"></i> دخول بحساب Discord</a>
        </div>
    </div>
    {% endif %}

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-links a').forEach(nav => nav.classList.remove('active'));
            
            document.getElementById(tabName).classList.add('active');
            document.getElementById('nav-' + tabName).classList.add('active');
        }
    </script>
</body>
</html>
"""

# -------------------------------------------------------------------
# 4. مسارات Flask (Routes)
# -------------------------------------------------------------------
@app.route('/')
def index():
    user_guilds = session.get('guilds', [])
    selected_guild_id = request.args.get('guild_id')
    
    if not selected_guild_id and user_guilds:
        selected_guild_id = user_guilds[0]['id']
        
    current_config = GUILDS_CONFIG.get(str(selected_guild_id), {})
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:3] if user_activity else []

    return render_template_string(
        DASHBOARD_HTML,
        user=session.get('user'),
        guilds=user_guilds,
        selected_guild_id=selected_guild_id,
        current_config=current_config,
        top_users=top_users
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
    token_res = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    token_json = token_res.json()
    access_token = token_json.get('access_token')

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
                filtered_guilds.append({
                    'id': g['id'],
                    'name': g['name'],
                    'icon': g.get('icon')
                })

    session['user'] = {
        'id': user_data.get('id'),
        'username': user_data.get('username'),
        'avatar': user_data.get('avatar')
    }
    session['guilds'] = filtered_guilds
    return redirect('/')

@app.route('/save-settings', methods=['POST'])
def save_settings():
    if 'user' not in session:
        return redirect('/login')

    guild_id = request.form.get('guild_id')
    if guild_id:
        GUILDS_CONFIG[str(guild_id)] = {
            "channel_id": request.form.get('channel_id'),
            "top_title": request.form.get('top_title')
        }
    return redirect(f'/?guild_id={guild_id}')

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
# 5. تشغيل الخدمات بالتوازي
# -------------------------------------------------------------------
def run_discord_bot():
    if BOT_TOKEN:
        try:
            bot.run(BOT_TOKEN)
        except Exception as e:
            print(f"[Bot Error] {e}")

if __name__ == '__main__':
    threading.Thread(target=run_discord_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
