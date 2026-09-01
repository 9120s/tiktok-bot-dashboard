import os
import sqlite3
import asyncio
import threading
from flask import Flask, render_template, request, redirect, url_for, session
import discord
from discord.ext import commands

# --- 1. إعداد قاعدة البيانات SQLite ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            guild_id TEXT,
            channel_id TEXT,
            tiktok_username TEXT,
            PRIMARY KEY (guild_id, tiktok_username)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 2. إعداد تطبيق Flask (لوحة التحكم) ---
app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'  # مفتاح جلسة Flask

@app.route('/')
def index():
    # استرجاع التنبيهات من قاعدة البيانات
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT guild_id, channel_id, tiktok_username FROM subscriptions')
    subscriptions = cursor.fetchall()
    conn.close()

    # قائمة السيرفرات المتصلة بالبوت (أمثلة تجريبية للواجهة)
    guilds = [
        {'id': '123456789012345678', 'name': 'سيرفر مجتمع التيك توك'},
        {'id': '987654321098765432', 'name': 'سيرفر البثوث والمباشر'}
    ]

    return render_template('index.html', subscriptions=subscriptions, guilds=guilds)

@app.route('/add', methods=['POST'])
def add_subscription():
    guild_id = request.form.get('guild_id')
    channel_id = request.form.get('channel_id')
    tiktok_username = request.form.get('tiktok_username', '').strip().replace('@', '')

    if guild_id and channel_id and tiktok_username:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO subscriptions (guild_id, channel_id, tiktok_username)
            VALUES (?, ?, ?)
        ''', (guild_id, channel_id, tiktok_username))
        conn.commit()
        conn.close()

    return redirect(url_for('index'))

@app.route('/delete/<guild_id>/<tiktok_username>', methods=['POST'])
def delete_subscription(guild_id, tiktok_username):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM subscriptions WHERE guild_id = ? AND tiktok_username = ?
    ''', (guild_id, tiktok_username))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# --- 3. إعداد بوت الديسكورد (discord.py) ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ تم تسجيل الدخول بنجاح باسم البوت: {bot.user}')

# --- 4. تشغيل سيرفر الويب والبوت معاً ---
if __name__ == '__main__':
    # تشغيل Flask في مسار فرعي (Thread)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # وضع توكن البوت الخاص بك هنا
    TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE'

    if TOKEN != 'YOUR_DISCORD_BOT_TOKEN_HERE':
        bot.run(TOKEN)
    else:
        print("⚠️ يرجى إضافة توكن البوت الخارجي في المتغير TOKEN داخل ملف main_bot.py")
        # إبقاء السيرفر يعمل حتى لو لم يتوفر التوكن فوراً
        flask_thread.join()