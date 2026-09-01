import os
import threading
import requests
from flask import Flask, redirect, session, request, render_template_string
import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent

# -------------------------------------------------------------------
# 1. الإعدادات والمتغيرات
# -------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey12345")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME", "2vce4")

API_BASE_URL = "https://discord.com/api/v10"

CONFIG = {
    "channel_id": None,
    "top_title": "🏆 أفضل 3 متفاعلين في البث الحالي"
}
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

async def send_top_active_users():
    if not CONFIG["channel_id"]:
        return False

    channel = bot.get_channel(int(CONFIG["channel_id"]))
    if not channel or not user_activity:
        return False

    sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:3]
    embed = discord.Embed(title=CONFIG["top_title"], color=discord.Color.gold())
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
# 3. تصميم اللوحة بالقوائم الجانبية (Sidebar HTML/CSS)
# -------------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة تحكم البوت</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; }
        body { background-color: #1e1e2e; color: #cdd6f4; display: flex; height: 100vh; }
        
        /* القائمة الجانبية */
        .sidebar { width: 260px; background-color: #181825; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; border-left: 1px solid #313244; }
        .sidebar h2 { font-size: 20px; color: #cba6f7; margin-bottom: 30px; text-align: center; }
        .nav-links { list-style: none; }
        .nav-links li { margin-bottom: 10px; }
        .nav-links a { color: #a6adc8; text-decoration: none; padding: 12px 15px; display: flex; align-items: center; gap: 10px; border-radius: 8px; transition: 0.3s; cursor: pointer; }
        .nav-links a:hover, .nav-links a.active { background-color: #313244; color: #89b4fa; }
        
        /* المحتوى الرئيسي */
        .main-content { flex: 1; padding: 40px; overflow-y: auto; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .card { background-color: #313244; padding: 25px; border-radius: 12px; max-width: 600px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .form-group { margin-bottom: 20px; text-align: right; }
        label { display: block; margin-bottom: 8px; color: #bac2de; font-size: 14px; }
        input[type="text"], select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #45475a; background: #1e1e2e; color: #cdd6f4; outline: none; }
        
        .btn { background-color: #89b4fa; color: #11111b; padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { background-color: #b4befe; }
        .btn-danger { background-color: #f38ba8; color: #11111b; }
        
        .user-info { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .user-info img { border-radius: 50%; width: 45px; height: 45px; }

        .leaderboard-list { list-style: none; margin-top: 15px; }
        .leaderboard-item { background: #1e1e2e; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .badge { background: #f9e2af; color: #11111b; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; }
    </style>
</head>
<body>

    {% if user %}
    <!-- القائمة الجانبية -->
    <div class="sidebar">
        <div>
            <h2><i class="fa-brands fa-tiktok"></i> لوحة تيك توك</h2>
            <ul class="nav-links">
                <li><a onclick="showTab('settings')" id="nav-settings" class="active"><i class="fa-solid fa-gear"></i> الإعدادات العامة</a></li>
                <li><a onclick="showTab('top3')" id="nav-top3"><i class="fa-solid fa-trophy"></i> أفضل 3 متفاعلين</a></li>
            </ul>
        </div>
        <div class="user-info">
            <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
            <div>
                <p style="font-weight: bold; font-size: 14px;">{{ user.username }}</p>
                <a href="/logout" style="color: #f38ba8; font-size: 12px; text-decoration: none;">تسجيل الخروج</a>
            </div>
        </div>
    </div>

    <!-- المحتوى الرئيسي -->
    <div class="main-content">
        <!-- تبويب الإعدادات -->
        <div id="settings" class="tab-content active">
            <h1 style="margin-bottom: 20px;">⚙️ إعدادات البوت والربط</h1>
            <div class="card">
                <form action="/save-settings" method="POST">
                    <div class="form-group">
                        <label>اختر السيرفر:</label>
                        <select name="guild_id">
                            {% for guild in guilds %}
                                <option value="{{ guild.id }}">{{ guild.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>معرف القناة (Channel ID):</label>
                        <input type="text" name="channel_id" value="{{ config.channel_id or '' }}" placeholder="123456789012345678" required>
                    </div>
                    <div class="form-group">
                        <label>عنوان رسالة أفضل المتفاعلين:</label>
                        <input type="text" name="top_title" value="{{ config.top_title }}" required>
                    </div>
                    <button type="submit" class="btn"><i class="fa-solid fa-floppy-disk"></i> حفظ الإعدادات</button>
                </form>
            </div>
        </div>

        <!-- تبويب أفضل 3 متفاعلين -->
        <div id="top3" class="tab-content">
            <h1 style="margin-bottom: 20px;">🏆 المتفاعلين في البث الحالي</h1>
            <div class="card">
                <p style="color: #a6adc8;">يتم تحديث القائمة تلقائياً بناءً على تعليقات البث مباشر.</p>
                <ul class="leaderboard-list">
                    {% if top_users %}
                        {% for user, count in top_users %}
                            <li class="leaderboard-item">
                                <span><strong>#{{ loop.index }}</strong> {{ user }}</span>
                                <span class="badge">{{ count }} تعليق</span>
                            </li>
                        {% endfor %}
                    {% else %}
                        <li class="leaderboard-item" style="justify-content: center; color: #a6adc8;">لا يوجد تفاعل مسجل بعد في البث الحالي</li>
                    {% endif %}
                </ul>
                <br>
                <a href="/trigger-top" class="btn" style="background-color: #a6e3a1; color: #11111b;"><i class="fa-solid fa-paper-plane"></i> إرسال القائمة لإشعار الديسكورد الآن</a>
            </div>
        </div>
    </div>
    {% else %}
    <!-- صفحة تسجيل الدخول -->
    <div style="margin: auto; text-align: center;">
        <div class="card" style="width: 350px;">
            <h2 style="margin-bottom: 15px;">تسجيل الدخول</h2>
            <p style="color: #a6adc8; margin-bottom: 20px;">قم بالتسجيل بواسطة الديسكورد للوصول لإعدادات البث</p>
            <a href="/login" class="btn" style="background-color: #5865F2; color: white;"><i class="fa-brands fa-discord"></i> دخول بحساب Discord</a>
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
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:3] if user_activity else []
    return render_template_string(
        DASHBOARD_HTML,
        user=session.get('user'),
        guilds=session.get('guilds', []),
        config=CONFIG,
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

    # تصفية السيرفرات بحسب الصلاحيات لتجنب كبر حجم الـ Cookie
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

    CONFIG["top_title"] = request.form.get('top_title')
    CONFIG["channel_id"] = request.form.get('channel_id')
    return redirect('/')

@app.route('/trigger-top')
def trigger_top():
    if 'user' in session and bot.loop:
        bot.loop.create_task(send_top_active_users())
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------------------------------------------------------
# 5. تشغيل الخدمات بالتوازي
# -------------------------------------------------------------------
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # 1. تشغيل لوحة التحكم في مسار مستقل (Thread)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. تشغيل بوت ديسكورد
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
