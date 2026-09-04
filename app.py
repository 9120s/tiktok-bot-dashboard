import os
import time
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session
from supabase import create_client, Client
import discord
from discord.ext import commands

# 1. إعدادات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://tiktok-bot-2s2-dashboard.onrender.com/callback")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. إعداد Flask والبوت
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "2s2_secret_key_123")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

live_cache = {}

# دالة خفيفة وسريعة للتحقق من حالة البث
def is_tiktok_live(username):
    try:
        url = f"https://www.tiktok.com/@{username}/live"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return '"status":2' in res.text or 'live-room' in res.text
    except Exception as e:
        print(f"Error checking status for {username}: {e}")
    return False

# 3. إرسال الإشعارات
def check_user_live(guild_id, username, channel_id, platform):
    try:
        cache_key = f"{guild_id}_{username}_{platform}"
        stream_url = f"https://www.tiktok.com/@{username}/live" if platform == "tiktok" else (
            f"https://www.twitch.tv/{username}" if platform == "twitch" else f"https://kick.com/{username}"
        )
        
        is_live = is_tiktok_live(username) if platform == "tiktok" else False

        if is_live and not live_cache.get(cache_key):
            channel = bot.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title=f"🔴 {username} الآن في بث مباشر!",
                    description=f"**رابط البث:**\n[اضغط هنا للإنضمام للبث]({stream_url})",
                    color=0xfe2c55
                )
                bot.loop.create_task(channel.send(content=f"@everyone {username} بدأ بث حياكم", embed=embed))
                live_cache[cache_key] = True
        elif not is_live:
            live_cache[cache_key] = False
    except Exception as e:
        print(f"Error in check_user_live: {e}")

# 4. مراقبة خلفية السيرفرات
def check_streams():
    while True:
        try:
            res = supabase.table("bot_configs").select("*").execute()
            if res.data:
                for item in res.data:
                    g_id = item.get("guild_id")
                    u_name = item.get("tiktok_user")
                    c_id = item.get("channel_id")
                    plat = item.get("platform", "tiktok")
                    if u_name and c_id:
                        check_user_live(g_id, u_name, c_id, plat)
        except Exception as e:
            print(f"Monitor error: {e}")
        time.sleep(30)

# 5. تصميم القالب والواجهة
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم التنبيهات التلقائية</title>
    <style>
        * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        body { background-color: #121212; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: #1e1e1e; border-radius: 20px; padding: 24px; width: 100%; max-width: 400px; border: 1px solid #2f2f2f; text-align: center; position: relative; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #2f2f2f; padding-bottom: 10px; }
        .logo { font-weight: 900; font-size: 18px; color: #fff; text-shadow: -1px -1px 0 #00f2fe, 1px 1px 0 #fe2c55; }
        .menu-btn { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; }
        .sidebar { position: fixed; top: 0; right: -300px; width: 300px; height: 100%; background: #181818; border-left: 1px solid #2f2f2f; z-index: 1000; transition: 0.3s; padding: 20px; text-align: right; overflow-y: auto; }
        .sidebar.active { right: 0; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 999; display: none; }
        .overlay.active { display: block; }
        .section-title { font-size: 13px; font-weight: bold; color: #00f2fe; margin: 15px 0 8px 0; text-transform: uppercase; }
        .sidebar-item { display: flex; align-items: center; gap: 10px; padding: 12px; color: #fff; text-decoration: none; border-radius: 10px; margin-bottom: 8px; background: #222; font-size: 13px; border: 1px solid #2f2f2f; }
        .server-card { background: #121212; border: 1px solid #333; padding: 10px 12px; border-radius: 10px; margin-bottom: 8px; font-size: 13px; }
        .server-card .user-name { font-weight: bold; color: #fe2c55; font-size: 14px; }
        .server-card .server-id { color: #aaa; font-size: 11px; }
        .form-group { margin-bottom: 16px; text-align: right; }
        label { display: block; margin-bottom: 6px; font-size: 12px; font-weight: bold; }
        select, input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #333; background: #121212; color: #fff; text-align: center; outline: none; }
        select { direction: rtl; }
        .btn-submit { width: 100%; padding: 14px; border: none; border-radius: 12px; background: linear-gradient(45deg, #fe2c55, #ff0050); color: #fff; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .alert { background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; color: #00f2fe; padding: 10px; border-radius: 10px; font-size: 12px; margin-bottom: 15px; }
    </style>
</head>
<body>

    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
    <div class="sidebar" id="sidebar">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <span style="font-weight:bold;">القائمة الجانبية</span>
            <button onclick="toggleSidebar()" style="background:none; border:none; color:#fe2c55; font-size:20px; cursor:pointer;">✕</button>
        </div>

        <div class="section-title">الحساب</div>
        {% if user %}
            <div class="sidebar-item">👤 {{ user.username }}</div>
            <a href="/logout" class="sidebar-item" style="color: #fe2c55;">🚪 تسجيل الخروج</a>
        {% else %}
            <a href="/login" class="sidebar-item" style="color: #00f2fe;">🔑 تسجيل الدخول عبر Discord</a>
        {% endif %}

        <div class="section-title">الروابط</div>
        <a href="https://discord.gg/hnbSsFDnF" target="_blank" class="sidebar-item">👾 انضم لسيرفرنا</a>

        <div class="section-title">السيرفرات المحفوظة</div>
        {% for item in saved_configs %}
            <div class="server-card">
                <div class="user-name">👤 @{{ item.tiktok_user }}</div>
                <div class="server-id">🆔 سيرفر: {{ item.guild_id }}</div>
                <div class="server-id">📢 روم: {{ item.channel_id }}</div>
            </div>
        {% else %}
            <div style="font-size: 12px; color: #666; padding: 10px 0;">لا توجد سيرفرات محفوظة حالياً</div>
        {% endfor %}
    </div>

    <div class="card">
        <div class="top-bar">
            <div class="logo">2s2 STREAM</div>
            <button class="menu-btn" onclick="toggleSidebar()">☰</button>
        </div>

        <h2 style="font-size:20px; margin:10px 0 6px 0;">إدارة التنبيهات التلقائية</h2>
        <div style="font-size:12px; color:#aaa; margin-bottom:20px;">قم بإعداد حساب المنصة وروم الديسكورد للتنبيه المباشر</div>

        {% if success %}
            <div class="alert">✅ تم حفظ البيانات وإرسال التنبيه التجريبي!</div>
        {% endif %}

        {% if not user %}
            <a href="/login" class="btn-submit" style="display:block; text-decoration:none; margin-top:20px;">🔑 تسجيل الدخول عبر Discord</a>
        {% else %}
            <form method="POST" action="/save">
                <div class="form-group">
                    <label>اختر السيرفر الإداري:</label>
                    <select name="guild_id" required>
                        {% for guild in guilds %}
                            <option value="{{ guild.id }}">{{ guild.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-group">
                    <label>اختر المنصة:</label>
                    <select name="platform">
                        <option value="tiktok">TikTok</option>
                        <option value="twitch">Twitch</option>
                        <option value="kick">Kick</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>يوزر الحساب (Username):</label>
                    <input type="text" name="username" placeholder="مثال: xzadd2" required>
                </div>

                <div class="form-group">
                    <label>رقم/آيدي روم التنبيهات (Channel ID):</label>
                    <input type="text" name="channel_id" placeholder="مثال: 1538986763622813766" required>
                </div>

                <button type="submit" class="btn-submit">💾 حفظ وتفعيل التنبيه الآلي</button>
            </form>
        {% endif %}
    </div>

    <script>
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }
    </script>
</body>
</html>
"""

# 6. المسارات
@app.route("/")
def index():
    user = session.get("user")
    guilds = session.get("guilds", [])
    success = request.args.get("success")
    
    saved_configs = []
    try:
        res = supabase.table("bot_configs").select("*").execute()
        saved_configs = res.data if res.data else []
    except Exception as e:
        print(f"Fetch error: {e}")

    return render_template_string(HTML_TEMPLATE, user=user, guilds=guilds, success=success, saved_configs=saved_configs)

@app.route("/login")
def login():
    if not CLIENT_ID:
        session["user"] = {"id": "123", "username": "Admin"}
        session["guilds"] = [{"id": "2s2", "name": "2s2 Server"}]
        return redirect(url_for("index"))
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/callback")
def callback():
    try:
        code = request.args.get("code")
        data = {
            "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": REDIRECT_URI, "scope": "identify guilds"
        }
        r = requests.post("https://discord.com/api/oauth2/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        token = r.json().get("access_token")

        user_req = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {token}"})
        session["user"] = user_req.json()

        guilds_req = requests.get("https://discord.com/api/users/@me/guilds", headers={"Authorization": f"Bearer {token}"})
        user_guilds = guilds_req.json() if guilds_req.status_code == 200 else []
        session["guilds"] = [g for g in user_guilds if (int(g.get("permissions", 0)) & 0x20) == 0x20 or (int(g.get("permissions", 0)) & 0x8) == 0x8]
    except Exception as e:
        print(f"OAuth Error: {e}")
        session["user"] = {"id": "123", "username": "Admin"}
        session["guilds"] = [{"id": "2s2", "name": "2s2 Server"}]
    return redirect(url_for("index"))

@app.route("/save", methods=["POST"])
def save():
    try:
        guild_id = str(request.form.get("guild_id", "")).strip()
        username = str(request.form.get("username", "")).strip()
        channel_id = str(request.form.get("channel_id", "")).strip()
        platform = str(request.form.get("platform", "tiktok")).strip()
        
        payload = {
            "guild_id": guild_id,
            "tiktok_user": username,
            "channel_id": channel_id,
            "platform": platform
        }
        
        # حفظ أو تحديث في قاعدة البيانات Supabase
        supabase.table("bot_configs").upsert(payload, on_conflict="guild_id").execute()

        # إرسال رسالة تجريبية
        channel = bot.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(
                title="⚙️ تم الحفظ والربط بنجاح!",
                description=f"تم ربط حساب **@{username}** بهذه الروم، وسأقوم بإرسال إشعار تلقائي هنا عند بدء البث المباشر.",
                color=0x2ecc71
            )
            bot.loop.create_task(channel.send(embed=embed))

        return redirect(url_for("index", success=1))
    except Exception as e:
        print(f"Save error: {e}")
        return redirect(url_for("index"))

if __name__ == "__main__":
    threading.Thread(target=check_streams, daemon=True).start()
    threading.Thread(target=lambda: bot.run(BOT_TOKEN), daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
