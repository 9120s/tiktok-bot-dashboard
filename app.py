import os
import threading
from flask import Flask, render_template, request, jsonify, redirect
from database import save_guild_config, get_all_configs

app = Flask(__name__)

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
    # إعادة توجيه لصفحة الرئسية مؤقتاً لحين ربط OAuth2 الخاص بـ Discord
    return redirect('/')

@app.route('/api/guilds', methods=['GET'])
def get_guilds():
    token = request.args.get('token')
    if not token:
        return jsonify({"guilds": []})
    
    # جلب السيرفرات المسجلة من قاعدة البيانات
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
