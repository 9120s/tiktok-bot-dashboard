import os
import asyncio
import requests
from flask import Flask, redirect, url_for, session, request, render_template_string
import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent

# -------------------------------------------------------------------
# 1. إعدادات Flask والمفاتيح
# -------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey12345")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME", "2vce4")

API_BASE_URL = "https://discord.com/api/v10"

# بيانات تخزين مؤقتة للإعدادات والمتفاعلين
CONFIG = {
    "channel_id": None,
    "top_title": "🏆 أفضل 3 متفاعلين في البث الحالي"
}
user_activity = {}  # {username: comment_count}

# -------------------------------------------------------------------
# 2. إعدادات بوت الديسكورد والتيك توك
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
    """إرسال أفضل 3 متفاعلين إلى قناة الديسكورد"""
    if not CONFIG["channel_id"]:
        return

    channel = bot.get_channel(int(CONFIG["channel_id"]))
    if not channel:
        return

    if not user_activity:
        return

    # ترتيب المتفاعلين حسب أكثرهم تعليقاً واختيار أعلى 3
    sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:3]
    
    embed = discord.Embed(
        title=CONFIG["top_title"],
        color=discord.Color.gold()
    )
    
    medals = ["🥇 المركز الأول", "🥈 المركز الثاني", "🥉 المركز الثالث"]
    for idx, (username, count) in enumerate(sorted_users):
        embed.add_field(
            name=f"{medals[idx]}: {username}",
            value=f"عدد المشاركات: **{count}**",
            inline=False
        )

    await channel.send(embed=embed)

# -------------------------------------------------------------------
# 3. لوحة التحكم (Flask Web Dashboard)
# -------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة التحكم</title>
    <style>
        body { font-family: sans-serif; background-color: #1e1e2e; color: #cdd6f4; text-align: center; padding: 40px; }
        .card { background: #313244; padding: 25px; border-radius: 12px; max-width: 500px; margin: 0 auto; }
        .btn { background-color: #5865F2; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }
        .form-group { margin-bottom: 15px; text-align: right; }
        input[type="text"], select { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #45475a; background: #1e1e2e; color: #cdd6f4; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="card">
        {% if user %}
            <h2>أهلاً بك، {{ user.username }}</h2>
            <form action="/save-settings" method="POST">
                <h3>إعدادات أفضل 3 متفاعلين</h3>
                <div class="form-group">
                    <label>السيرفر:</label>
                    <select name="guild_id">
                        {% for guild in guilds %}
                            <option value="{{ guild.id }}">{{ guild.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>عنوان الإشعار:</label>
                    <input type="text" name="top_title" value="{{ config.top_title }}" required>
                </div>
                <div class="form-group">
                    <label>معرّف القناة (Channel ID):</label>
                    <input type="text" name="channel_id" value="{{ config.channel_id or '' }}" placeholder="1234567890" required>
                </div>
                <button type="submit" class="btn">حفظ الإعدادات</button>
            </form>
            <br>
            <a href="/trigger-top" class="btn" style="background-color: #a6e3a1; color: #11111b;">إرسال أفضل 3 متفاعلين الآن</a>
            <br><br>
            <a href="/logout" style="color: #f38ba8;">تسجيل الخروج</a>
        {% else %}
            <h2>لوحة تحكم بوت تيك توك</h2>
            <a href="/login" class="btn">تسجيل الدخول بالديسكورد</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        INDEX_HTML,
        user=session.get('user'),
        guilds=session.get('guilds', []),
        config=CONFIG
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

    # فلترة السيرفرات لمنع تضخم حجم الـ Session
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

    session['user'] = {'id': user_data.get('id'), 'username': user_data.get('username')}
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
        asyncio.run_coroutine_threadsafe(send_top_active_users(), bot.loop)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------------------------------------------------------
# 4. تشغيل الخدمات بالتوازي
# -------------------------------------------------------------------
async def main():
    # تشغيل سيرفر Web الخاص باللوحة في الخلفية
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{os.environ.get('PORT', 10000)}"]

    # تشغيل بوت ديسكورد وتيك توك ولوحة التحكم معاً
    asyncio.create_task(serve(app, config))
    if BIKTOK_USERNAME := os.environ.get("TIKTOK_USERNAME"):
        asyncio.create_task(tiktok_client.start())
    
    await bot.start(BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
