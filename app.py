import os
from flask import Flask, render_template, request, jsonify
from database import save_guild_config, get_all_configs

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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
