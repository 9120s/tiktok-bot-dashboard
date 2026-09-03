import os
import json
import asyncio
import threading
import requests
import discord
from discord.ext import commands
from flask import Flask, request, jsonify, redirect, render_template_string
from TikTokLive import TikTokLiveClient
from supabase import create_client, Client

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("CLIENT_ID", os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")).strip()
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET", os.getenv("DISCORD_CLIENT_SECRET", "")).strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SERVER_INVITE_URL = os.getenv("SERVER_INVITE_URL", "https://discord.gg/TQUFzyxM7").strip()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ggevrddcmxlxvkjhsywy.supabase.co").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ [SUPABASE] تم الاتصال بقاعدة البيانات بنجاح!")
    except Exception as e:
        print(f"❌ [SUPABASE ERROR] {e}")

CONFIG_FILE = "configs.json"

def load_configs():
    if supabase:
        try:
            res = supabase.table("bot_configs").select("*").execute()
            configs = {}
            for row in res.data:
                configs[row["guild_id"]] = {
                    "platform": row.get("platform", "tiktok"),
                    "streamer_user": row.get("tiktok_user", ""),
                    "channel_id": row.get("channel_id", "")
                }
            return configs
        except Exception as e:
            print(f"⚠️ Error reading from Supabase: {e}")

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading local config file: {e}")
    return {}

def save_configs_db(guild_id, streamer_user, channel_id, platform="tiktok"):
    if supabase:
        try:
            data = {
                "guild_id": str(guild_id),
                "tiktok_user": str(streamer_user),
                "channel_id": str(channel_id),
                "platform": str(platform)
            }
            supabase.table("bot_configs").upsert(data).execute()
            print(f"💾 [SUPABASE] تم حفظ البيانات للسيرفر: {guild_id}")
            return
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")

    configs = load_configs()
    configs[str(guild_id)] = {"platform": platform, "tiktok_user": streamer_user, "channel_id": channel_id}
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Error saving config file: {e}")

ACTIVE_CLIENTS = {}

intents = discord.Intents.default()
discord_client = commands.Bot(command_prefix="!", intents=intents)

@discord_client.event
async def on_ready():
    print(f'✅ [DISCORD] البوت متصل باسم: {discord_client.user}')

def run_discord_bot():
    if BOT_TOKEN:
        try:
            discord_client.run(BOT_TOKEN)
        except Exception as e:
            print(f"❌ [DISCORD ERROR] {e}")

threading.Thread(target=run_discord_bot, daemon=True).start()

def send_discord_alert(channel_id, streamer_user, platform="tiktok", is_test=False):
    if not BOT_TOKEN:
        return False, "BOT_TOKEN_MISSING"
    
    clean_channel_id = str(channel_id).strip()
    url = f"https://discord.com/api/v10/channels/{clean_channel_id}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    if platform == "twitch":
        stream_url = f"https://www.twitch.tv/{streamer_user}"
        platform_name = "Twitch"
        color = 9127187
    elif platform == "kick":
        stream_url = f"https://kick.com/{streamer_user}"
        platform_name = "Kick"
        color = 5570614
    else:
        stream_url = f"https://www.tiktok.com/@{streamer_user}/live"
        platform_name = "TikTok"
        color = 16657493

    if is_test:
        content = ""
        title = f"⚙️ تم الربط بنجاح! - {platform_name}"
        desc = f"حساب **@{streamer_user}** على منصة **{platform_name}** متصل الآن وسيرسل إشعار فور بدء البث."
        color = 4898432
    else:
        content = f"@everyone 🔴 بدأ بث جديد على {platform_name}!"
        title = f"{platform_name} Live - {streamer_user}"
        desc = f"الآن في بث مباشر! 🔴\n\n[اضغط هنا للإنضمام للبث مباشرة]({stream_url})"

    payload = {
        "content": content,
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color,
            "footer": {"text": f"{platform_name} Live Notification"}
        }]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return True, "OK"
        else:
            return False, f"HTTP_{res.status_code}: {res.text}"
    except Exception as e:
        return False, str(e)

async def start_tiktok_listener(streamer_user, channel_id, platform="tiktok"):
    if platform == "tiktok":
        client = TikTokLiveClient(unique_id=streamer_user)
        @client.on("connect")
        async def on_connect(event):
            send_discord_alert(channel_id, streamer_user, platform, is_test=False)
        try:
            await client.start()
        except Exception as e:
            print(f"⚠️ [LIVE CLOSED] @{streamer_user}: {e}")

def monitor_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def main_loop():
        while True:
            configs = load_configs()
            for guild_id, data in configs.items():
                streamer_user = data.get("streamer_user") or data.get("tiktok_user")
                channel_id = data.get("channel_id")
                platform = data.get("platform", "tiktok")
                
                if streamer_user and channel_id and platform == "tiktok":
                    key = f"{guild_id}_{streamer_user}"
                    if key not in ACTIVE_CLIENTS or not ACTIVE_CLIENTS[key].is_alive():
                        t = threading.Thread(target=lambda: asyncio.run(start_tiktok_listener(streamer_user, channel_id, platform)), daemon=True)
                        t.start()
                        ACTIVE_CLIENTS[key] = t
                        
            await asyncio.sleep(60)

    loop.run_until_complete(main_loop())

threading.Thread(target=monitor_thread, daemon=True).start()

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم | Multi-Platform Live</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-main: #121212;
            --bg-sidebar: #000000;
            --bg-card: #1e1e1e;
            --primary: #fe2c55;
            --text-main: #ffffff;
            --text-muted: #a1a1aa;
            --border-color: #27272a;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-main); color: var(--text-main); display: flex; min-height: 100vh; }

        .sidebar {
            width: 280px; background: var(--bg-sidebar); border-left: 1px solid var(--border-color);
            display: flex; flex-direction: column; justify-content: space-between; padding: 1.5rem 1rem;
            position: fixed; top: 0; bottom: 0; right: 0; z-index: 100; overflow-y: auto;
        }

        .brand {
            display: flex; align-items: center; gap: 12px; font-size: 1.3rem; font-weight: 800;
            color: var(--text-main); padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);
        }

        .section-title { font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin: 1.2rem 0 0.5rem 0; font-weight: bold; }

        .nav-menu { list-style: none; display: flex; flex-direction: column; gap: 6px; }
        .nav-item a {
            display: flex; align-items: center; gap: 12px; padding: 10px 14px;
            color: var(--text-muted); text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 0.95rem;
        }
        .nav-item a:hover, .nav-item.active a { background: #27272a; color: #25f4ee; }

        .saved-servers-list { list-style: none; display: flex; flex-direction: column; gap: 6px; max-height: 150px; overflow-y: auto; }
        .saved-server-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #18181b; border-radius: 6px; font-size: 0.85rem; border: 1px solid var(--border-color); }

        .join-server-btn {
            background: linear-gradient(45deg, #fe2c55, #25f4ee);
            color: #000 !important; font-weight: 800 !important; text-align: center; justify-content: center;
        }

        .auth-btn { background: rgba(254, 44, 85, 0.15); color: #fe2c55 !important; border: 1px solid #fe2c55; margin-bottom: 8px; text-align: center; justify-content: center; }

        .main-content { margin-right: 280px; flex: 1; padding: 2.5rem; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; padding: 2.5rem; width: 100%; max-width: 550px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8); text-align: right; }
        .card h2 { text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; }
        .card p.desc { text-align: center; color: var(--text-muted); margin-bottom: 1.5rem; }

        .btn-submit {
            display: inline-flex; align-items: center; justify-content: center; gap: 10px;
            background: #fe2c55; color: #fff; padding: 14px 28px; border-radius: 10px;
            font-weight: bold; font-size: 1rem; width: 100%; border: none; cursor: pointer; margin-top: 10px; text-decoration: none;
        }

        .form-group { margin-bottom: 1.2rem; }
        .form-group label { display: block; margin-bottom: 6px; font-weight: bold; font-size: 0.95rem; }
        input[type="text"], select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); background: #000; color: #fff; font-size: 0.95rem; outline: none; }

        .platform-tabs { display: flex; gap: 10px; margin-bottom: 1.2rem; }
        .platform-btn {
            flex: 1; padding: 10px; border-radius: 8px; border: 1px solid var(--border-color); background: #18181b; color: #fff;
            cursor: pointer; text-align: center; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 8px;
        }
        .platform-btn.active[data-platform="tiktok"] { background: #fe2c55; border-color: #fe2c55; }
        .platform-btn.active[data-platform="twitch"] { background: #9146ff; border-color: #9146ff; }
        .platform-btn.active[data-platform="kick"] { background: #53fc18; color: #000; border-color: #53fc18; }

        .status-badge { display: inline-block; background: rgba(37, 244, 238, 0.15); color: #25f4ee; border: 1px solid #25f4ee; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; margin-bottom: 15px; }
        .error { color: #fe2c55; background: rgba(254, 44, 85, 0.1); border: 1px solid #fe2c55; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; }
        .success { color: #4ade80; background: rgba(74, 222, 128, 0.1); border: 1px solid #4ade80; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: relative; border-left: none; }
            .main-content { margin-right: 0; padding: 1.5rem; }
        }
    </style>
</head>
<body>

    <aside class="sidebar">
        <div>
            <div class="brand"><i class="fa-solid fa-tower-broadcast"></i><span>لوحة التحكم</span></div>
            
            <ul class="nav-menu" style="margin-top: 1rem;">
                <li class="nav-item active"><a href="/"><i class="fa-solid fa-house"></i> الرئيسية</a></li>
            </ul>

            <div class="section-title"><i class="fa-solid fa-server"></i> السيرفرات المحفوظة</div>
            <ul class="saved-servers-list" id="savedServersMenu">
                <li style="color:var(--text-muted); font-size:0.8rem; text-align:center;">جاري التحميل...</li>
            </ul>
        </div>

        <ul class="nav-menu" style="margin-top: 1.5rem;">
            <li class="nav-item">
                <a href="/login" class="auth-btn" id="authBtn"><i class="fa-solid fa-right-to-bracket"></i> تسجيل الدخول</a>
            </li>
            <li class="nav-item">
                <a href="{{ server_invite }}" target="_blank" class="join-server-btn">
                    <i class="fa-brands fa-discord"></i> انضم لسيرفرنا
                </a>
            </li>
        </ul>
    </aside>

    <main class="main-content">
        <div class="card">
            <h2>إدارة التنبيهات التلقائية</h2>
            <p class="desc">قم بضبط منصة البث المباشر وروم الديسكورد للتنبيهات</p>

            <div id="content">
                <a href="/login" class="btn-submit"><i class="fa-brands fa-discord"></i> تسجيل الدخول عبر ديسكورد</a>
            </div>
        </div>
    </main>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        let selectedPlatform = 'tiktok';

        function reloadSidebar() {
            fetch('/api/saved-configs')
                .then(res => res.json())
                .then(data => {
                    const menu = document.getElementById('savedServersMenu');
                    if (data.configs && data.configs.length > 0) {
                        menu.innerHTML = '';
                        data.configs.forEach((item) => {
                            menu.innerHTML += `
                                <li class="saved-server-item">
                                    <span><i class="fa-solid fa-hashtag"></i> ${item.guild_id}</span>
                                    <strong style="color:#25f4ee">@${item.tiktok_user}</strong>
                                </li>`;
                        });
                    } else {
                        menu.innerHTML = '<li style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:5px;">لا توجد سيرفرات محفوظة</li>';
                    }
                });
        }

        reloadSidebar();

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
                                <label>اختر السيرفر الإداري:</label>
                                <select id="guildSelect">`;
                        data.guilds.forEach(g => { html += `<option value="${g.id}">${g.name}</option>`; });
                        html += `</select></div>

                            <div class="form-group">
                                <label>اختر المنصة:</label>
                                <div class="platform-tabs">
                                    <div class="platform-btn active" data-platform="tiktok" onclick="setPlatform('tiktok')"><i class="fa-brands fa-tiktok"></i> TikTok</div>
                                    <div class="platform-btn" data-platform="twitch" onclick="setPlatform('twitch')"><i class="fa-brands fa-twitch"></i> Twitch</div>
                                    <div class="platform-btn" data-platform="kick" onclick="setPlatform('kick')"><i class="fa-solid fa-bolt"></i> Kick</div>
                                </div>
                            </div>

                            <div class="form-group"><label id="userLabel">يوزر حساب TikTok:</label><input type="text" id="streamerUser" placeholder="مثال: os_in7"></div>
                            <div class="form-group"><label>رقم/آيدي روم التنبيهات (Channel ID):</label><input type="text" id="channelId" placeholder="مثال: 1538986763622813766"></div>
                            
                            <button onclick="saveSettings()" class="btn-submit"><i class="fa-solid fa-floppy-disk"></i> حفظ وتفعيل التنبيه الآلي</button>

                            <div id="responseMsg"></div>`;
                        document.getElementById('content').innerHTML = html;
                    } else {
                        document.getElementById('content').innerHTML = '<div class="error">لم يتم العثور على سيرفرات لديك فيها صلاحيات إدارة!</div>';
                    }
                });
        }

        function setPlatform(platform) {
            selectedPlatform = platform;
            document.querySelectorAll('.platform-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`.platform-btn[data-platform="${platform}"]`).classList.add('active');
            
            const label = document.getElementById('userLabel');
            if (platform === 'twitch') {
                label.innerText = 'يوزر حساب Twitch:';
            } else if (platform === 'kick') {
                label.innerText = 'يوزر حساب Kick:';
            } else {
                label.innerText = 'يوزر حساب TikTok:';
            }
        }

        function saveSettings() {
            const guildId = document.getElementById('guildSelect').value;
            const streamerUser = document.getElementById('streamerUser').value.trim();
            const channelId = document.getElementById('channelId').value.trim();
            const msgDiv = document.getElementById('responseMsg');

            if (!streamerUser || !channelId) {
                msgDiv.innerHTML = '<div class="error">يرجى ملء كافة البيانات أولاً.</div>';
                return;
            }

            msgDiv.innerHTML = '<div style="color:var(--text-muted); text-align:center; margin-top:10px;">جاري التفعيل والحفظ...</div>';

            fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ guild_id: guildId, streamer_user: streamerUser, channel_id: channelId, platform: selectedPlatform })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    msgDiv.innerHTML = '<div class="success"><i class="fa-solid fa-circle-check"></i> تم الربط وبدء المراقبة بنجاح!</div>';
                    reloadSidebar();
                } else {
                    msgDiv.innerHTML = '<div class="error"><i class="fa-solid fa-triangle-exclamation"></i> فشل إرسال الرسالة! السبب: ' + data.details + '</div>';
                    reloadSidebar();
                }
            });
        }
    </script>
</body>
</html>
"""

def get_redirect_uri():
    redirect_env = os.getenv("REDIRECT_URI", "").strip()
    if redirect_env:
        return redirect_env
    base_url = request.host_url.rstrip('/')
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://", 1)
    return f"{base_url}/callback"

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT, server_invite=SERVER_INVITE_URL)

@app.route('/login')
def login():
    redirect_uri = get_redirect_uri()
    discord_auth_url = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&scope=identify+guilds"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return redirect('/?err=nocode')
    
    redirect_uri = get_redirect_uri()
    data = {'client_id': DISCORD_CLIENT_ID, 'client_secret': DISCORD_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    res = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
    if res.status_code == 200:
        return redirect(f"/?token={res.json().get('access_token')}")
    return redirect(f'/?err=auth_failed_{res.status_code}')

@app.route('/api/guilds')
def get_guilds():
    user_token = request.args.get('token')
    guilds_list = []
    if user_token:
        after_id = 0
        while True:
            url = 'https://discord.com/api/v10/users/@me/guilds?limit=200'
            if after_id:
                url += f'&after={after_id}'
                
            res = requests.get(url, headers={'Authorization': f'Bearer {user_token}'})
            if res.status_code == 200:
                data = res.json()
                if not data:
                    break
                for g in data:
                    permissions = int(g.get('permissions', 0))
                    is_owner = g.get('owner', False)
                    is_admin = (permissions & 0x8) == 0x8
                    can_manage = (permissions & 0x20) == 0x20

                    if is_owner or is_admin or can_manage:
                        guilds_list.append({"id": str(g['id']), "name": g['name']})

                after_id = data[-1]['id']
            else:
                break
                
    guilds_list.sort(key=lambda x: x['name'].lower())
    return jsonify({"guilds": guilds_list})

@app.route('/api/saved-configs')
def get_saved_configs():
    configs = load_configs()
    result = []
    for g_id, data in configs.items():
        result.append({
            "guild_id": g_id,
            "tiktok_user": data.get("streamer_user") or data.get("tiktok_user", ""),
            "channel_id": data.get("channel_id", "")
        })
    return jsonify({"configs": result})

@app.route('/api/save', methods=['POST'])
def save_settings():
    data = request.json
    guild_id = str(data.get('guild_id')).strip()
    streamer_user = data.get('streamer_user', '').replace('@', '').strip()
    channel_id = str(data.get('channel_id', '')).strip()
    platform = data.get('platform', 'tiktok').strip()

    save_configs_db(guild_id, streamer_user, channel_id, platform)

    sent, details = send_discord_alert(channel_id, streamer_user, platform=platform, is_test=True)

    return jsonify({"success": sent, "details": details})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
