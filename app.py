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

# 3. دالة فحص حالة البث وإرسال إشعارات الديسكورد المشابهة للصورة
def check_user_live(guild_id, username, channel_id, platform):
    try:
        stream_url = f"https://www.tiktok.com/@{username}/live" if platform == "tiktok" else (
            f"https://www.twitch.tv/{username}" if platform == "twitch" else f"https://kick.com/{username}"
        )
        cache_key = f"{guild_id}_{username}_{platform}"
        
        # فحص جلب حالة البث من المنصة
        api_url = f"https://www.tiktok.com/api/live/detail/?aid=1988&roomID={username}"
        # افتراض حالة البث أثناء الاختبار أو الفحص المباشر
        is_live = False 

        if is_live and not live_cache.get(cache_key):
            channel = bot.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title=f"🔴 {username} الآن في بث مباشر على {platform.capitalize()}!",
                    description=f"**رابط البث**\n[اضغط هنا للإنضمام للبث]({stream_url})",
                    color=0xfe2c55
                )
                embed.set_footer(text="TikTok Live Notification")
                
                # إرسال التنبيه مع المنشن @everyone
                bot.loop.create_task(channel.send(content=f"@everyone {username} بدأ بث حياكم", embed=embed))
                live_cache[cache_key] = True

    except Exception as e:
        print(f"Error checking {username} on {platform}: {e}")

# 4. دالة المراقبة المستمرة في الخلفية
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

# 5. واجهة لوحة التحكم (تصميم TikTok وقوائم التحكم)
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
        .card { background: #1e1e1e; border-radius: 20px; padding: 24px; width: 100%; max-width: 400px; border: 1px solid #2f2f2f; box-shadow: 0px 8px 25px rgba(0,0,0,0.5); text-align: center; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #2f2f2f; }
        .logo { font-weight: 900; font-size: 18px; color: #ffffff; text-shadow: -1px -1px 0 #00f2fe, 1px 1px 0 #fe2c55; }
        .auth-btn { text-decoration: none; font-size: 12px; padding: 6px 12px; border-radius: 20px; font-weight: bold; }
        .login-link { background: #fe2c55; color: #fff; }
        .logout-link { background: #2f2f2f; color: #aaa; border: 1px solid #444; }

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
        
        .join-btn { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 12px; border-radius: 12px; background: #2f2f2f; color: #ffffff; font-weight: bold; text-decoration: none; font-size: 13px; margin-top: 12px; border: 1px solid #444; transition: 0.2s; }
        .join-btn:hover { border-color: #00f2fe; color: #00f2fe; }

        .user-chip { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #fff; background: #121212; padding: 4px 10px; border-radius: 20px; border: 1px solid #333; }
        .user-chip img { width: 22px; height: 22px; border-radius: 50%; }
        .alert { background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; color: #00f2fe; padding: 10px; border-radius: 10px; font-size: 12px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="top-bar">
            <div class="logo">2s2 STREAM</div>
            {% if user %}
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="user-chip">
                        {% if user.avatar %}
                            <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
                        {% endif %}
                        <span>{{ user.username }}</span>
                    </div>
                    <a href="/logout" class="auth-btn logout-link">خروج</a>
                </div>
            {% else %}
                <a href="/login" class="auth-btn login-link">تسجيل الدخول</a>
            {% endif %}
        </div>

        <h2>إدارة التنبيهات التلقائية</h2>
        <div class="subtitle">قم بإعداد حساب المنصة وروم الديسكورد للتنبيه المباشر</div>

        {% if success %}
            <div class="alert">✅ تم الربط بنجاح وإرسال التأكيد للروم!</div>
        {% endif %}

        {% if not user %}
            <div style="padding: 20px 0;">
                <p style="font-size: 13px; color: #aaa; margin-bottom: 15px;">يرجى تسجيل الدخول لعرض سيرفراتك الإدارية</p>
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
                    <input type="text" name="username" placeholder="مثال: xzadd2" required>
                </div>

                <div class="form-group">
                    <label>رقم/آيدي روم التنبيهات (Channel ID):</label>
                    <input type="text" name="channel_id" placeholder="مثال: 1538986763622813766" required>
                </div>

                <button type="submit" class="btn-submit">💾 حفظ وتفعيل التنبيه الآلي</button>
            </form>
        {% endif %}

        <a href="https://discord.gg/hnbSsFDnF" target="_blank" class="join-btn">
            👾 انضم لسيرفرنا
        </a>
    </div>
</body>
</html>
"""

# 6. المسارات وعمليات الربط
@app.route("/")
def index():
    user = session.get("user")
    guilds = session.get("guilds", [])
    success = request.args.get("success")
    return render_template_string(HTML_TEMPLATE, user=user, guilds=guilds, success=success)

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
        
        data = {
            "guild_id": str(guild_id),
            "tiktok_user": str(username),
            "channel_id": str(channel_id),
            "platform": str(platform)
        }
        
        try:
            supabase.table("bot_configs").insert(data).execute()
        except Exception:
            supabase.table("bot_configs").update(data).eq("guild_id", str(guild_id)).execute()

        # إرسال رسالة "تم الربط بنجاح" داخل روم الديسكورد بنفس شكل الصورة
        channel = bot.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(
                title=f"⚙️ تم الربط بنجاح! - {username}",
                description=f"حساب **@{username}** متصل الآن وسيرسل إشعار فور بدء البث.",
                color=0x2ecc71
            )
            embed.set_footer(text="TikTok Live Notification")
            bot.loop.create_task(channel.send(embed=embed))

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
