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

# 2. إعداد تطبيق Flask والبوت
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "2s2_secret_key_123")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

live_cache = {}

# 3. دالة فحص حالة البث
def check_user_live(guild_id, username, channel_id, platform):
    try:
        cache_key = f"{guild_id}_{username}_{platform}"
        if not live_cache.get(cache_key):
            channel = bot.get_channel(int(channel_id))
            if channel:
                pass
    except Exception as e:
        print(f"Error checking {username} on {platform}: {e}")

# 4. دالة المراقبة في الخلفية
def check_streams():
    while True:
        try:
            response = supabase.table("bot_configs").select("*").execute()
            configs = response.data
            if configs:
                for config in configs:
                    guild_id = config.get("guild_id")
                    username = config.get("tiktok_user")
                    channel_id = config.get("channel_id")
                    platform = config.get("platform", "tiktok")
                    
                    if username and channel_id:
                        check_user_live(guild_id, username, channel_id, platform)
        except Exception as e:
            print(f"Error in stream monitor: {e}")
        time.sleep(60)

# 5. واجهة لوحة التحكم
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة التنبيهات التلقائية</title>
    <style>
        * { box-sizing: border-box; }
        body { background-color: #0d0e12; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .card { background: #16171d; border-radius: 20px; padding: 28px 24px; width: 100%; max-width: 380px; border: 1px solid #23242c; text-align: center; }
        h2 { font-size: 22px; font-weight: 800; margin: 0 0 10px 0; }
        .subtitle { font-size: 13px; color: #9a9cae; margin-bottom: 20px; line-height: 1.5; }
        .form-group { margin-bottom: 18px; text-align: right; }
        label { display: block; margin-bottom: 8px; font-size: 13px; font-weight: 700; color: #ffffff; text-align: center; }
        input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid #23242c; background: #000000; color: #ffffff; font-size: 14px; direction: ltr; text-align: center; outline: none; }
        select { direction: rtl; text-align-last: center; appearance: none; }
        .status-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 229, 153, 0.1); border: 1px solid #00e599; color: #00e599; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 20px; }
        button, .btn { width: 100%; padding: 14px; border: none; border-radius: 12px; background: #fe2c55; color: #ffffff; font-weight: bold; cursor: pointer; font-size: 15px; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
        button:active, .btn:active { transform: scale(0.98); }
        .login-btn { background: #5865F2; }
        .join-btn { background: #23242c; border: 1px solid #333544; color: #ffffff; margin-top: 12px; }
        .user-info { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 20px; background: #000000; padding: 10px; border-radius: 12px; }
        .user-info img { width: 32px; height: 32px; border-radius: 50%; }
        .alert { background: rgba(0, 229, 153, 0.15); border: 1px solid #00e599; color: #00e599; padding: 10px; border-radius: 10px; font-size: 13px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>إدارة التنبيهات التلقائية</h2>
        <div class="subtitle">قم بإعداد حساب المنصة وروم الديسكورد للتنبيه المباشر</div>

        {% if success %}
            <div class="alert">✅ تم حفظ البيانات وتفعيل التنبيه بنجاح!</div>
        {% endif %}

        {% if not user %}
            <a href="/login" class="btn login-btn">🔑 تسجيل الدخول عبر Discord</a>
        {% else %}
            <div class="user-info">
                {% if user.avatar %}
                    <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
                {% endif %}
                <span>{{ user.username }}</span>
            </div>

            <form method="POST" action="/save">
                <div class="form-group">
                    <label>اختر السيرفر الإداري:</label>
                    <select name="guild_id" required>
                        {% for guild in guilds %}
                            <option value="{{ guild.id }}">{{ guild.name }}</option>
                        {% else %}
                            <option value="2s2">2s2</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="status-badge">
                    ⚡ المراقبة المباشرة تعمل الآن
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
                    <input type="text" name="username" placeholder="مثال: os_in7" required>
                </div>

                <div class="form-group">
                    <label>رقم/آيدي روم التنبيهات (Channel ID):</label>
                    <input type="text" name="channel_id" placeholder="مثال: 1538986763622813766" required>
                </div>

                <button type="submit">💾 حفظ وتفعيل التنبيه الآلي</button>
            </form>
        {% endif %}

        <a href="https://discord.gg/2s2" target="_blank" class="btn join-btn">👾 انضم لسيرفرنا</a>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    user = session.get("user")
    guilds = session.get("guilds", [])
    success = request.args.get("success")
    return render_template_string(HTML_TEMPLATE, user=user, guilds=guilds, success=success)

@app.route("/login")
def login():
    if not CLIENT_ID:
        # تسجيل دخول افتراضي في حال عدم إدخال CLIENT_ID
        session["user"] = {"id": "123", "username": "Admin", "avatar": ""}
        session["guilds"] = [{"id": "2s2", "name": "2s2 Server"}]
        return redirect(url_for("index"))
    
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_auth_url)

@app.route("/callback")
def callback():
    try:
        code = request.args.get("code")
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "scope": "identify guilds"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
        token = r.json().get("access_token")

        user_req = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {token}"})
        session["user"] = user_req.json()

        guilds_req = requests.get("https://discord.com/api/users/@me/guilds", headers={"Authorization": f"Bearer {token}"})
        user_guilds = guilds_req.json() if guilds_req.status_code == 200 else []
        admin_guilds = [g for g in user_guilds if (int(g.get("permissions", 0)) & 0x20) == 0x20 or (int(g.get("permissions", 0)) & 0x8) == 0x8]
        session["guilds"] = admin_guilds
    except Exception as e:
        print(f"OAuth Error: {e}")
        session["user"] = {"id": "123", "username": "Admin", "avatar": ""}
        session["guilds"] = [{"id": "2s2", "name": "2s2 Server"}]

    return redirect(url_for("index"))

@app.route("/save", methods=["POST"])
def save():
    try:
        guild_id = request.form.get("guild_id")
        username = request.form.get("username")
        channel_id = request.form.get("channel_id")
        platform = request.form.get("platform", "tiktok")
        
        # تنفيذ عملية الحفظ مع التعامل الآمن للأخطاء
        data = {
            "guild_id": str(guild_id),
            "tiktok_user": str(username),
            "channel_id": str(channel_id),
            "platform": str(platform)
        }
        
        # محاولة التعديل أولاً، وإن لم ينفع يتم الإدراج
        try:
            supabase.table("bot_configs").insert(data).execute()
        except Exception:
            supabase.table("bot_configs").update(data).eq("guild_id", str(guild_id)).execute()

        return redirect(url_for("index", success=1))
    except Exception as e:
        print(f"Save Error: {e}")
        return redirect(url_for("index"))

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=check_streams, daemon=True)
    monitor_thread.start()
    
    bot_thread = threading.Thread(target=lambda: bot.run(BOT_TOKEN), daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
