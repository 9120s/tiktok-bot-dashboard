import os
import json
import asyncio
import threading
import requests
from flask import Flask, request, jsonify, redirect, render_template_string
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("CLIENT_ID", os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")).strip()
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET", os.getenv("DISCORD_CLIENT_SECRET", "")).strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

CONFIG_FILE = "config.json"
active_monitors = {}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_discord_alert(channel_id, tiktok_user):
    if not BOT_TOKEN:
        return False, "BOT_TOKEN مفقود في متغيرات البيئة"
    
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "embeds": [{
            "title": "🔴 بث جديد مباشر الان!",
            "description": f"بدأ **@{tiktok_user}** بث جديد على تيك توك الآن! 🔥\n\n[اضغط هنا لمشاهدة البث مباشرة](https://www.tiktok.com/@{tiktok_user}/live)",
            "color": 16657493
        }]
    }
    try:
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code in [200, 201]:
            return True, "تم الإرسال بنجاح"
        else:
            return False, f"خطأ من ديسكورد (كود: {res.status_code})"
    except Exception as e:
        return False, str(e)

async def start_tiktok_listener(tiktok_user, channel_id):
    client = TikTokLiveClient(unique_id=tiktok_user)
    
    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        send_discord_alert(channel_id, tiktok_user)

    try:
        await client.start()
    except Exception as e:
        print(f"[TIKTOK ERROR] {tiktok_user}: {e}")

def run_listener_in_thread(tiktok_user, channel_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_tiktok_listener(tiktok_user, channel_id))

def restart_all_listeners():
    configs = load_config()
    for guild_id, settings in configs.items():
        tiktok_user = settings.get("tiktok_user")
        channel_id = settings.get("channel_id")
        
        if tiktok_user and channel_id and guild_id not in active_monitors:
            t = threading.Thread(target=run_listener_in_thread, args=(tiktok_user, channel_id), daemon=True)
            t.start()
            active_monitors[guild_id] = t

# --- HTML Layout ---

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم | TikTok Live</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-main: #121212;
            --bg-sidebar: #000000;
            --bg-card: #1e1e1e;
            --tiktok-pink: #fe2c55;
            --tiktok-cyan: #25f4ee;
            --text-main: #ffffff;
            --text-muted: #a1a1aa;
            --border-color: #27272a;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-main); color: var(--text-main); display: flex; min-height: 100vh; }

        .sidebar {
            width: 260px; background: var(--bg-sidebar); border-left: 1px solid var(--border-color);
            display: flex; flex-direction: column; justify-content: space-between; padding: 1.5rem 1rem;
            position: fixed; top: 0; bottom: 0; right: 0; z-index: 100;
        }

        .brand {
            display: flex; align-items: center; gap: 12px; font-size: 1.3rem; font-weight: 800;
            color: var(--text-main); padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);
            text-shadow: 2px 2px var(--tiktok-pink), -2px -2px var(--tiktok-cyan);
        }

        .nav-menu { list-style: none; margin-top: 1.5rem; display: flex; flex-direction: column; gap: 8px; }
        .nav-item a {
            display: flex; align-items: center; gap: 12px; padding: 12px 16px;
            color: var(--text-muted); text-decoration: none; border-radius: 8px; font-weight: 600; cursor: pointer;
        }
        .nav-item a:hover, .nav-item.active a { background: #27272a; color: var(--tiktok-cyan); }

        .auth-btn { background: rgba(254, 44, 85, 0.15); color: var(--tiktok-pink) !important; border: 1px solid var(--tiktok-pink); margin-bottom: 8px; }
        .auth-btn:hover { background: var(--tiktok-pink) !important; color: #fff !important; }

        .main-content { margin-right: 260px; flex: 1; padding: 2.5rem; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; padding: 2.5rem; width: 100%; max-width: 520px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8); text-align: right; }
        .card h2 { text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; }
        .card p.desc { text-align: center; color: var(--text-muted); margin-bottom: 2rem; }

        .btn-tiktok {
            display: inline-flex; align-items: center; justify-content: center; gap: 10px;
            background: var(--tiktok-pink); color: #fff; padding: 14px 28px; border-radius: 10px;
            font-weight: bold; font-size: 1rem; width: 100%; border: none; cursor: pointer; margin-top: 10px;
        }

        .btn-send-now {
            background: #25f4ee;
            color: #000;
            box-shadow: 0 0 15px rgba(37, 244, 238, 0.4);
        }

        .btn-send-now:hover { background: #1ee0da; }

        .form-group { margin-bottom: 1.2rem; }
        .form-group label { display: block; margin-bottom: 6px; font-weight: bold; font-size: 0.95rem; }
        input[type="text"], select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); background: #000; color: #fff; font-size: 0.95rem; outline: none; }

        .status-badge { display: inline-block; background: rgba(37, 244, 238, 0.15); color: var(--tiktok-cyan); border: 1px solid var(--tiktok-cyan); padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; margin-bottom: 15px; }
        .error { color: var(--tiktok-pink); background: rgba(254, 44, 85, 0.1); border: 1px solid var(--tiktok-pink); padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; }
        .success { color: #4ade80; background: rgba(74, 222, 128, 0.1); border: 1px solid #4ade80; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: relative; border-left: none; border-bottom: 1px solid var(--border-color); }
            .main-content { margin-right: 0; padding: 1.5rem; }
        }
    </style>
</head>
<body>

    <aside class="sidebar">
        <div>
            <div class="brand"><i class="fa-brands fa-tiktok"></i><span>لوحة التحكم</span></div>
            <ul class="nav-menu">
                <li class="nav-item active"><a href="/"><i class="fa-solid fa-house"></i> الرئيسية</a></li>
            </ul>
        </div>
        <ul class="nav-menu">
            <li class="nav-item">
                <a href="/login" class="auth-btn" id="authBtn"><i class="fa-solid fa-right-to-bracket"></i> تسجيل الدخول</a>
            </li>
        </ul>
    </aside>

    <main class="main-content">
        <div class="card">
            <h2>إدارة البوت</h2>
            <p class="desc">قم بتسجيل الدخول لاختيار السيرفر والتحكم بالإعدادات</p>

            <div id="content">
                <a href="/login" class="btn-tiktok"><i class="fa-brands fa-discord"></i> تسجيل الدخول عبر ديسكورد</a>
            </div>
        </div>
    </main>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (token) {
            const authBtn = document.getElementById('authBtn');
            authBtn.href = '/';
            authBtn.innerHTML = '<i class="fa-solid fa-right-from-bracket"></i> تسجيل الخروج';

            fetch('/api/guilds?token=' + token)
                .then(res => res.json())
                .then(data => {
                    if (data.guilds && data.guilds.length > 0) {
                        let html = `
                            <div class="form-group">
                                <label>اختر السيرفر اللي فيه رتبتك:</label>
                                <select id="guildSelect">`;
                        data.guilds.forEach(g => { html += `<option value="${g.id}">${g.name}</option>`; });
                        html += `</select></div>
                            <div style="text-align: center; margin: 10px 0;"><span class="status-badge"><i class="fa-solid fa-bolt"></i> حالة البوت: جاهز للبث🔥</span></div>
                            <div class="form-group"><label>يوزر التيك توك (TikTok Username):</label><input type="text" id="tiktokUser" placeholder="مثال: 2vce4"></div>
                            <div class="form-group"><label>رقم/آيدي روم التنبيهات (Channel ID):</label><input type="text" id="channelId" placeholder="مثال: 1538986763622813766"></div>
                            
                            <button onclick="saveSettings()" class="btn-tiktok"><i class="fa-solid fa-floppy-disk"></i> حفظ التنبيهات</button>
                            <button onclick="sendAlertNow()" class="btn-tiktok btn-send-now"><i class="fa-solid fa-paper-plane"></i> إرسال تنبيه الآن</button>

                            <div id="responseMsg"></div>`;
                        document.getElementById('content').innerHTML = html;
                    }
                });
        }

        function saveSettings() {
            const guildId = document.getElementById('guildSelect').value;
            const tiktokUser = document.getElementById('tiktokUser').value.trim();
            const channelId = document.getElementById('channelId').value.trim();
            const msgDiv = document.getElementById('responseMsg');

            if (!tiktokUser || !channelId) {
                msgDiv.innerHTML = '<div class="error">يرجى ملء يوزر التيك توك ورقم الروم أولاً.</div>';
                return;
            }

            fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ guild_id: guildId, tiktok_user: tiktokUser, channel_id: channelId })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    msgDiv.innerHTML = '<div class="success"><i class="fa-solid fa-circle-check"></i> تم حفظ الإعدادات بنجاح!</div>';
                }
            });
        }

        function sendAlertNow() {
            const tiktokUser = document.getElementById('tiktokUser').value.trim();
            const channelId = document.getElementById('channelId').value.trim();
            const msgDiv = document.getElementById('responseMsg');

            if (!tiktokUser || !channelId) {
                msgDiv.innerHTML = '<div class="error">يرجى ملء يوزر التيك توك ورقم الروم أولاً.</div>';
                return;
            }

            msgDiv.innerHTML = '<p style="color:var(--tiktok-cyan); text-align:center; margin-top:10px;"><i class="fa-solid fa-spinner fa-spin"></i> جاري إرسال التنبيه...</p>';

            fetch('/api/send-now', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tiktok_user: tiktokUser, channel_id: channelId })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    msgDiv.innerHTML = '<div class="success"><i class="fa-solid fa-paper-plane"></i> تم إرسال التنبيه إلى الروم بنجاح! 🔥</div>';
                } else {
                    msgDiv.innerHTML = `<div class="error">فشل الإرسال: ${data.error}</div>`;
                }
            });
        }
    </script>
</body>
</html>
"""

# --- Routes ---

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/login')
def login():
    redirect_uri = request.host_url.rstrip('/') + '/callback'
    discord_auth_url = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&scope=identify+guilds"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return redirect('/?err=nocode')
    
    redirect_uri = request.host_url.rstrip('/') + '/callback'
    data = {'client_id': DISCORD_CLIENT_ID, 'client_secret': DISCORD_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    res = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
    if res.status_code == 200:
        return redirect(f"/?token={res.json().get('access_token')}")
    return redirect('/?err=auth_failed')

@app.route('/api/guilds')
def get_guilds():
    user_token = request.args.get('token')
    guilds_list = []
    if user_token:
        res = requests.get('https://discord.com/api/v10/users/@me/guilds', headers={'Authorization': f'Bearer {user_token}'})
        if res.status_code == 200:
            for g in res.json():
                guilds_list.append({"id": str(g['id']), "name": g['name']})
    return jsonify({"guilds": guilds_list})

@app.route('/api/save', methods=['POST'])
def save_settings():
    data = request.json
    guild_id = data.get('guild_id')
    tiktok_user = data.get('tiktok_user', '').replace('@', '').strip()
    channel_id = data.get('channel_id', '').strip()

    all_configs = load_config()
    all_configs[guild_id] = {"tiktok_user": tiktok_user, "channel_id": channel_id}
    save_config(all_configs)

    if guild_id not in active_monitors:
        t = threading.Thread(target=run_listener_in_thread, args=(tiktok_user, channel_id), daemon=True)
        t.start()
        active_monitors[guild_id] = t

    return jsonify({"success": True})

@app.route('/api/send-now', methods=['POST'])
def send_now():
    data = request.json
    tiktok_user = data.get('tiktok_user', '').replace('@', '').strip()
    channel_id = data.get('channel_id', '').strip()

    success, msg = send_discord_alert(channel_id, tiktok_user)
    return jsonify({"success": success, "error": msg if not success else ""})

if __name__ == '__main__':
    restart_all_listeners()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
