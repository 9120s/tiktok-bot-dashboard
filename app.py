import os
import time
import threading
from flask import Flask, render_template_string, request, redirect, url_for
from supabase import create_client, Client
import discord
from discord.ext import commands

# 1. إعدادات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. إعداد تطبيق Flask والبوت
app = Flask(__name__)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ذاكرة مؤقتة لمنع تكرار إرسال التنبيه لنفس البث
live_cache = {}

# 3. دالة فحص حالة البث وإرسال التنبيه
def check_user_live(guild_id, username, channel_id, platform):
    try:
        # هنا يتم التمييز بين المنصات
        is_live = False
        stream_url = ""
        
        if platform == "tiktok":
            # فحص تيك توك
            stream_url = f"https://www.tiktok.com/@{username}/live"
            # (يمكن إضافة مكتبة TikTokLive هنا للتحقق الفعلي)
        elif platform == "twitch":
            stream_url = f"https://www.twitch.tv/{username}"
        elif platform == "kick":
            stream_url = f"https://kick.com/{username}"

        cache_key = f"{guild_id}_{username}_{platform}"
        
        # إذا كان البث متصلاً ولم يُرسل تنبيه له سابقاً
        if is_live and not live_cache.get(cache_key):
            channel = bot.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title=f"🔴 {username} الآن في بث مباشر على {platform.capitalize()}!",
                    url=stream_url,
                    color=0xFE2C55 if platform == "tiktok" else (0x9146FF if platform == "twitch" else 0x53FC18)
                )
                embed.add_field(name="رابط البث", value=f"[اضغط هنا للانضمام للبث]({stream_url})")
                bot.loop.create_task(channel.send(embed=embed))
                live_cache[cache_key] = True
        elif not is_live:
            live_cache[cache_key] = False

    except Exception as e:
        print(f"خطأ في فحص حساب {username} على {platform}: {e}")

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
            print(f"خطأ أثناء مراقبة البث: {e}")
            
        time.sleep(60)

# 5. واجهة لوحة التحكم (Dashboard)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة التنبيهات التلقائية</title>
    <style>
        body { background-color: #0f0f12; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #18191c; border-radius: 16px; padding: 30px; width: 90%; max-width: 400px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); border: 1px solid #2f3136; text-align: center; }
        h2 { margin-bottom: 20px; font-size: 22px; }
        .form-group { margin-bottom: 15px; text-align: right; }
        label { display: block; margin-bottom: 5px; font-size: 14px; color: #b9bbbe; }
        input, select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #202225; background: #2f3136; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; border: none; border-radius: 8px; background: #fe2c55; color: #fff; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 16px; }
        button:hover { background: #e02648; }
    </style>
</head>
<body>
    <div class="card">
        <h2>إدارة التنبيهات التلقائية</h2>
        <form method="POST" action="/save">
            <div class="form-group">
                <label>اختر المنصة:</label>
                <select name="platform">
                    <option value="tiktok">TikTok</option>
                    <option value="twitch">Twitch</option>
                    <option value="kick">Kick</option>
                </select>
            </div>
            <div class="form-group">
                <label>اختر السيرفر الإداري (Guild ID):</label>
                <input type="text" name="guild_id" placeholder="مثال: 2s2" required>
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
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/save", methods=["POST"])
def save():
    guild_id = request.form.get("guild_id")
    username = request.form.get("username")
    channel_id = request.form.get("channel_id")
    platform = request.form.get("platform")
    
    supabase.table("bot_configs").upsert({
        "guild_id": guild_id,
        "tiktok_user": username,
        "channel_id": channel_id,
        "platform": platform
    }).execute()
    
    return redirect(url_for("index"))

# 6. تشغيل البوت والخدمة
def run_discord_bot():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    # تشغيل مراقبة البث في Thread مستقل
    monitor_thread = threading.Thread(target=check_streams, daemon=True)
    monitor_thread.start()
    
    # تشغيل بوت الديسكورد في Thread مستقل
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل Flask Web Server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
