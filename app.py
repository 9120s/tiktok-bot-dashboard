import os
import time
import threading
import asyncio
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from supabase import create_client, Client
import discord
from discord.ext import commands

# 1. إعداد متغيرات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://tiktok-bot-2s2-dashboard.onrender.com/callback")

# الاتصال بقاعدة البيانات Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. إعداد تطبيق Flask والبوت
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "2s2_secret_key_123")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

live_cache = {}

# دالة التحقق من حالة البث على منصة تيك توك
def check_tiktok_live_status(username):
    try:
        url = f"https://www.tiktok.com/@{username}/live"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            content = response.text
            if '"status":2' in content or 'live-room' in content or 'room_id' in content:
                return True
    except Exception as e:
        print(f"Error checking TikTok status for {username}: {e}")
    return False

# دالة إرسال التنبيهات في الديسكورد بأمان
async def send_discord_message_async(channel_id, content=None, embed=None):
    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            channel = await bot.fetch_channel(int(channel_id))
        if channel:
            await channel.send(content=content, embed=embed)
            print(f"Message sent successfully to channel {channel_id}")
    except Exception as e:
        print(f"Failed to send message to channel {channel_id}: {e}")

# 3. دالة فحص وإرسال إشعار البث المباشر الفعلي
def check_user_live(guild_id, username, channel_id, platform):
    try:
        stream_url = f"https://www.tiktok.com/@{username}/live" if platform == "tiktok" else (
            f"https://www.twitch.tv/{username}" if platform == "twitch" else f"https://kick.com/{username}"
        )
        cache_key = f"{guild_id}_{username}_{platform}"
        
        is_live = check_tiktok_live_status(username) if platform == "tiktok" else False

        if is_live and not live_cache.get(cache_key):
            embed = discord.Embed(
                title=f"🔴 {username} الآن في بث مباشر على {platform.capitalize()}!",
                description=f"**رابط البث**\n[اضغط هنا للإنضمام للبث]({stream_url})",
                color=0xfe2c55
            )
            embed.set_footer(text="TikTok Live Notification")
            
            if bot.loop and bot.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    send_discord_message_async(channel_id, content=f"@everyone {username} بدأ بث حياكم", embed=embed),
                    bot.loop
                )
            live_cache[cache_key] = True
        elif not is_live:
            live_cache[cache_key] = False

    except Exception as e:
        print(f"Error in check_user_live: {e}")

# 4. دالة الخلفية لمراقبة الحسابات في قاعدة البيانات
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
            print(f"Error in stream monitor thread: {e}")
        time.sleep(30)

# 5. الواجهة والتصميم
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم التنبيهات التلقائية</title>
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: #121212; color: #ffffff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        
        .card { background: #1e1e1e; border-radius: 20px; padding: 24px; width: 100%; max-width: 400px; border: 1px solid #2f2f2f; box-shadow: 0px 8px 25px rgba(0,0,0,0.5); text-align: center; position: relative; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #2f2f2f; }
        .logo { font-weight: 900; font-size: 18px; color: #ffffff; text-shadow: -1px -1px 0 #00f2fe, 1px 1px 0 #fe2c55; }
        .menu-btn { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; padding: 0; width: auto; }

        .sidebar { position: fixed; top: 0; right: -300px; width: 300px; height: 100%; background: #181818; border-left: 1px solid #2f2f2f; z-index: 1000; transition: 0.3s ease; padding: 20px; text-align: right; overflow-y: auto; box-shadow: -5px 0 15px rgba(0,0,0,0.5); }
        .sidebar.active { right: 0; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 999; display: none; }
        .overlay.active { display: block; }
        
        .sidebar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #2f2f2f; padding-bottom: 10px; }
        .close-btn { background: none; border: none; color: #fe2c55; font-size: 20px; cursor: pointer; font-weight: bold; width: auto; }

        .section-title { font-size: 13px; font-weight: 800; color: #00f2fe; margin: 15px 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px; }

        .sidebar-item { display: flex; align-items: center; gap: 10px; padding: 12px; color: #fff; text-decoration: none; border-radius: 10px; margin-bottom: 8px; background: #222; font-size: 13px; font-weight: bold; transition: 0.2s; border: 1px solid #2f2f2f; }
        .sidebar-item:hover { background: #2f2f2f; border-color: #00f2fe; }

        .server-card { background: #121212; border: 1px solid #333; padding: 10px 12px; border-radius: 10px; font-size: 13px; margin-bottom: 8px; display: flex; flex-direction: column; gap: 4px; }
        .server-card .user-name { font-weight: bold; color: #fe2c55; font-size: 14px; }
        .server-card .server-id { color: #aaa; font-size: 11px; }

        h2 { font-size: 20px; font-weight: 800; margin: 10px 0 6px 0; }
        .subtitle { font-size: 12px; color: #a0a0a0; margin-bottom: 20px; }
        
        .form-group { margin-bottom: 16px; text-align: right; }
        label { display: block; margin-bottom: 6px; font-size: 12px; font-weight: 700; color: #e0e0e0; }
        
        select, input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #333; background: #121212; color: #ffffff; font-size: 13px; outline: none; transition: 0.2s; }
        select { direction: rtl; text-align-last: center; appearance: none; cursor: pointer; }
        select:focus, input:focus { border-color: #00f2fe; box-shadow: 0 0 5px rgba(0, 242, 254, 0.4); }
        input { text-align: center; direction: ltr; }
        
        .status-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 242, 254, 0.1); border: 1px solid #00f2fe; color: #00f2fe; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-bottom: 18px; }
        
        .btn-submit { width: 100%; padding: 14px; border: none; border-radius: 12px; background: linear-gradient(45deg, #fe2c55, #ff0050); color: #ffffff; font-weight: bold; cursor: pointer; font-size: 14px; margin-top: 10px; transition: 0.2s; }
        .btn-submit:active { transform: scale(0.98); }
        
        .user-chip { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #fff; background: #121212; padding: 8px 12px; border-radius: 12px; border: 1px solid #333; margin-bottom: 10px; }
        .user-chip img { width: 26px; height: 26px; border-radius: 50%; }
        .alert { background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; color: #00f2fe; padding: 10px; border-radius: 10px; font-size: 12px; margin-bottom: 15px; }
    </style>
</head>
<body>

    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span style="font-weight: bold; font-size: 16px;">القائمة الجانبية</span>
            <button class="close-btn" onclick="toggleSidebar()">✕</button>
        </div>

        <div class="section-title">الحساب</div>
        {% if user %}
            <div class="user-chip">
                {% if user.get('avatar') %}
                    <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
                {% endif %}
                <span>{{ user.get('username', 'User') }}</span>
            </div>
            <a href="/logout" class="sidebar-item" style="color: #fe2c55;">🚪 تسجيل الخروج</a>
        {% else %}
            <a href="/login" class="sidebar-item" style="color: #00f2fe;">🔑 تسجيل الدخول عبر Discord</a>
        {% endif %}

        <div class="section-title">الروابط</div>
        <a href="https://discord.gg/hnbSsFDnF" target="_blank" class="sidebar-item">👾 انضم لسيرفرنا</a>

        <div class="section-title">السيرفرات المحفوظة</div>
        {% for item in saved_configs %}
            <div class="server-card">
                <div class="user-name">👤 @{{ item.get('tiktok_user') }}</div>
                <div class="server-id">🆔 سيرفر: {{ item.get('guild_id') }}</div>
                <div class="server-id">📢 روم: {{ item.get('channel_id') }}</div>
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

        <h2>إدارة التنبيهات التلقائية</h2>
        <div class="subtitle">قم بإعداد حساب المنصة وروم الديسكورد للتنبيه المباشر</div>

        {% if success %}
            <div class="alert">✅ تم حفظ البيانات وتفعيل التنبيه بنجاح!</div>
        {% endif %}

        {% if not user %}
            <div style="padding: 20px 0;">
                <p style="font-size: 13px; color: #aaa; margin-bottom: 15px;">يرجى تسجيل الدخول لعرض سيرفراتك والتحكم بالتنبيهات</p>
                <a href="/login" class="btn-submit" style="display: block; text-decoration: none;">🔑 تسجيل الدخول عبر Discord</a>
            </div>
        {% else %}
            <form method="POST" action="/save">
                <div class="form-group">
                    <label>اختر السيرفر الإداري:</label>
                    <select name="guild_id" required>
                        {% for guild in guilds %}
                            <option value="{{ guild.id }}">{{ guild.name }}</option>
                        {% else %}
                            <option value="" disabled selected>لا توجد سيرفرات بصلاحيات إدارية</option>
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
                    <input type="text" name="username" value="xzadd2" required>
                </div>

                <div class="form-group">
                    <label>رقم/آيدي روم التنبيهات (Channel ID):</label>
                    <input type="text" name="channel_id" value="1538986763622813766" required>
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

# 6. مسارات التطبيق
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
        print(f"Error fetching saved configs: {e}")

    return render_template_string(HTML_TEMPLATE, user=user, guilds=guilds, success=success, saved_configs=saved_configs)

@app.route("/login")
def login():
    if not CLIENT_ID:
        session["user"] = {"id": "123", "username": "Admin", "avatar": ""}
        session["guilds"] = [{"id": "2s2", "name": "2s2 Server"}]
        return redirect(url_for("index"))
    
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_auth_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

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

        if not guild_id or not username or not channel_id:
            return "<h2 style='color:red; text-align:center;'>خطأ: إحدى الخانات فارغة!</h2><div style='text-align:center;'><a href='/'>رجوع</a></div>"

        payload = {
            "guild_id": str(guild_id).strip(),
            "tiktok_user": str(username).strip(),
            "channel_id": str(channel_id).strip(),
            "platform": str(platform).strip(),
            "created_at": datetime.utcnow().isoformat()
        }

        # حفظ البيانات في Supabase
        response = supabase.table("bot_configs").upsert(payload).execute()
        print(f"DEBUG Supabase Response: {response}")

        # إرسال التنبيه التجريبي المعدل إلى الديسكورد
        try:
            embed = discord.Embed(
                title=f"🧪 رسالة تجريبية - اختبار نظام التنبيهات",
                description=f"تم ربط حساب **@{username}** بنجاح في هذا الروم.\nسيعمل التنبيه الآلي فور بدء البث المباشر على منصة **{platform.capitalize()}**.",
                color=0x00f2fe
            )
            embed.set_footer(text="2s2 STREAM • Test Notification")

            if bot.loop and bot.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    send_discord_message_async(channel_id, embed=embed),
                    bot.loop
                )
        except Exception as bot_err:
            print(f"Discord notice send error: {bot_err}")

        return redirect(url_for("index", success=1))

    except Exception as e:
        return f"""
        <div style="background:#121212; color:#ff4d4d; padding:30px; font-family:sans-serif; direction:rtl; min-height:100vh;">
            <h2 style="border-bottom:1px solid #333; padding-bottom:10px;">❌ حدث خطأ أثناء الحفظ في قاعدة البيانات:</h2>
            <p style="background:#1e1e1e; padding:15px; border-radius:8px; color:#fff; direction:ltr; text-align:left;">{str(e)}</p>
            <a href="/" style="display:inline-block; margin-top:15px; padding:10px 20px; background:#00f2fe; color:#000; text-decoration:none; font-weight:bold; border-radius:8px;">العودة للوحة التحكم</a>
        </div>
        """

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=check_streams, daemon=True)
    monitor_thread.start()
    
    bot_thread = threading.Thread(target=lambda: bot.run(BOT_TOKEN), daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
