import os
import requests
import threading
from flask import Flask, render_template, request, jsonify, redirect
from database import save_guild_config, get_all_configs

app = Flask(__name__)

# بيانات تطبيق ديسكورد
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "") # يمكنك إضافته في Render Environment Variables
REDIRECT_URI = "https://tiktok-bot-2s2-dashboard.onrender.com/callback"

# تشغيل البوت في مسار منفصل
def run_discord_bot():
    from main_bot import bot
    bot_token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if bot_token:
        bot.run(bot_token)

threading.Thread(target=run_discord_bot, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    discord_auth_url = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify+guilds"
    return redirect(discord_auth_url)

# مسار استقبال الرمز من ديسكورد بعد الموافقة
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')
    
    # توجيه المستخدم إلى اللوحة مع إبقاء الرمز
    return redirect(f'/?token={code}')

@app.route('/api/guilds', methods=['GET'])
def get_guilds():
    token = request.args.get('token')
    if not token:
        return jsonify({"guilds": []})
    
    configs = get_all_configs()
    guilds_list = []
    for g_id in configs.keys():
        guilds_list.append({"id": g_id, "name": f"Server {g_id}"})
        
    return jsonify({"guilds": guilds_list})

@app.route('/api/config', methods=['GET'])
def get_config():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
        
    configs = get_all_configs()
    if configs:
        last_key = list(configs.keys())[-1]
        return jsonify(configs[last_key])
    return jsonify({})

@app.route('/api/config', methods=['POST'])
def save_config():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json or {}
    guild_id = data.get('guild_id')
    tiktok_username = data.get('tiktok_username')
    channel_id = data.get('channel_id')
    message_title = data.get('message_title')

    if not all([guild_id, tiktok_username, channel_id, message_title]):
        return jsonify({"error": "جميع الحقول مطلوبة"}), 400

    success = save_guild_config(guild_id, tiktok_username, channel_id, message_title)
    if success:
        return jsonify({"message": "Saved successfully"})
    return jsonify({"error": "Failed to save data"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
