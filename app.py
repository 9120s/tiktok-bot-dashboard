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

live_cache = {}

# 3. دالة فحص حالة البث وإرسال التنبيه
def check_user_live(guild_id, username, channel_id, platform):
    try:
        stream_url = f"https://www.tiktok.com/@{username}/live" if platform == "tiktok" else (
            f"https://www.twitch.tv/{username}" if platform == "twitch" else f"https://kick.com/{username}"
        )
        cache_key = f"{guild_id}_{username}_{platform}"
        
        # معالجة إرسال التنبيه
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

# 5. واجهة لوحة التحكم والتصميم الأصلي
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
        label { display: block; margin-bottom: 8px; font-size: 13px; font-weight: 700; color: #ffffff; }
        input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid #23242c; background: #000000; color: #8e92a2; font-size: 14px; direction: ltr; text-align: center; outline: none; }
        select { direction: rtl; text-align: right; appearance: none; }
        .status-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 229, 153, 0.1); border: 1px solid #00e599; color: #00e599; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 20px; }
        button { width: 100%; padding: 14px; border: none; border-radius: 12px; background: #fe2c55; color: #ffffff; font-weight: bold; cursor: pointer; font-size: 15px; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 8px; }
        button:active { transform: scale(0.98); }
    </style>
</head>
<body>
    <div class="card">
        <h2>إدارة التنبيهات التلقائية</h2>
        <div class="subtitle">قم بإعداد حساب المنصة وروم الديسكورد للتنبيه المباشر</div>
        
        <form method="POST" action="/save">
            <div class="form-group">
                <label style="text-align: center;">اختر السيرفر الإداري:</label>
                <select name="guild_id" style="text-align-last: center;">
                    <option value="2s2">2s2</option>
                </select>
            </div>

            <div class="status-badge">
                ⚡ المراقبة المباشرة تعمل الآن
            </div>

            <div class="form-group">
                <label style="text-align: center;">اختر المنصة:</label>
                <select name="platform" style="text-align-last: center; color: #ffffff;">
                    <option value="tiktok">TikTok</option>
                    <option value="twitch">Twitch</option>
                    <option value="kick">Kick</option>
                </select>
            </div>

            <div class="form-group">
                <label style="text-align: center;">يوزر الحساب (Username):</label>
                <input type="text" name="username" placeholder="مثال: os_in7" required>
            </div>

            <div class="form-group">
                <label style="text-align: center;">رقم/آيدي روم التنبيهات (Channel ID):</label>
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

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=check_streams, daemon=True)
    monitor_thread.start()
    
    bot_thread = threading.Thread(target=lambda: bot.run(BOT_TOKEN), daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
