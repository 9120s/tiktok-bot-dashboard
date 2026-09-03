import os
import time
import json
import asyncio
import threading
import requests
import discord
from discord.ext import commands
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("CLIENT_ID", os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")).strip()
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET", os.getenv("DISCORD_CLIENT_SECRET", "")).strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SERVER_INVITE_URL = os.getenv("SERVER_INVITE_URL", "https://discord.gg/TQUFzyxM7").strip()

CONFIG_FILE = "configs.json"

# --- دمج وإدارة الحفظ التلقائي في ملف JSON ---
def load_configs():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config file: {e}")
    return {}

def save_configs(configs):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Error saving config file: {e}")

SAVED_CONFIGS = load_configs()
LAST_LIVE_STATUS = {}

# --- تشغيل بوت ديسكورد ---
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

# --- دالة إرسال التنبيهات للديسكورد ---
def send_discord_alert(channel_id, tiktok_user, is_test=False):
    if not BOT_TOKEN:
        print("❌ [ALERT ERROR] BOT_TOKEN غير مضاف!")
        return False, "BOT_TOKEN_MISSING"
    
    clean_channel_id = str(channel_id).strip()
    url = f"https://discord.com/api/v10/channels/{clean_channel_id}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    if is_test:
        content = ""
        title = f"⚙️ تم الربط بنجاح! - {tiktok_user}"
        desc = f"حساب **@{tiktok_user}** متصل الآن وسيرسل إشعار فور بدء البث."
        color = 4898432  # أخضر
    else:
        content = "@everyone 🔴 معاً بدأ بث جديد حياكم!"
        title = f"TikTok Live - {tiktok_user}"
        desc = f"معاً الآن في بث مباشر على TikTok! 🔴\n\n[اضغط هنا للإنضمام للبث](https://www.tiktok.com/@{tiktok_user}/live)"
        color = 16657493  # وردي

    payload = {
        "content": content,
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color,
            "footer": {"text": "TikTok Live Notification"}
        }]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📡 [DISCORD RESP] Channel: {clean_channel_id} | Code: {res.status_code} | Body: {res.text}")
        if res.status_code in [200, 201]:
            return True, "OK"
        else:
            return False, f"HTTP_{res.status_code}: {res.text}"
    except Exception as e:
        print(f"❌ [DISCORD SEND EXCEPTION] {e}")
        return False, str(e)

# --- فحص حالة البث ---
def check_tiktok_live_status(tiktok_user):
    url = f"https://www.tiktok.com/@{tiktok_user}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200 and ('"status":2' in res.text or 'live-room' in res.url or 'LIVE' in res.text):
            return True
    except Exception:
        pass
    return False

# --- محرك المراقبة الشامل لجميع السيرفرات ---
def background_checker():
    while True:
        try:
            current_configs = load_configs()
            for guild_id, data in current_configs.items():
                tiktok_user = data.get("tiktok_user")
                channel_id = data.get("channel_id")
                
                if tiktok_user and channel_id:
                    is_live = check_tiktok_live_status(tiktok_user)
                    was_live = LAST_LIVE_STATUS.get(guild_id, False)

                    if is_live and not was_live:
                        print(f"🔴 [LIVE DETECTED] @{tiktok_user} فتح بث! جاري الإرسال للسيرفر {guild_id} الروم {channel_id}...")
                        send_discord_alert(channel_id, tiktok_user, is_test=False)
                        LAST_LIVE_STATUS[guild_id] = True
                    elif not is_live and was_live:
                        LAST_LIVE_STATUS[guild_id] = False

        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
        
        time.sleep(30)

threading.Thread(target=background_checker, daemon=True).start()

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
            width: 280px; background: var(--bg-sidebar); border-left: 1px solid var(--border-color);
            display: flex; flex-direction: column; justify-content: space-between; padding: 1.5rem 1rem;
            position: fixed; top: 0; bottom: 0; right: 0; z-index: 100; overflow-y: auto;
        }

        .brand {
            display: flex; align-items: center; gap: 12px; font-size: 1.3rem; font-weight: 800;
            color: var(--text-main); padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);
            text-shadow: 2px 2px var(--tiktok-pink), -2px -2px var(--tiktok-cyan);
        }

        .section-title { font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin: 1.2rem 0 0.5rem 0; font-weight: bold; }

        .nav-menu { list-style: none; display: flex; flex-direction: column; gap: 6px; }
        .nav-item a {
            display: flex; align-items: center; gap: 12px; padding: 10px 14px;
            color: var(--text-muted); text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 0.95rem;
        }
        .nav-item a:hover, .nav-item.active a { background: #27272a; color: var(--tiktok-cyan); }

        .saved-servers-list { list-style: none; display: flex; flex-direction: column; gap: 6px; max-height: 150px; overflow-y: auto; }
        .saved-server-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #18181b; border-radius: 6px; font-size: 0.85rem; border: 1px solid var(--border-color); }

        .top3-sidebar-list { list-style: none; display: flex; flex-direction: column; gap: 6px; }
        .top3-sidebar-item {
            background: #18181b; border: 1px solid var(--border-color); border-radius: 8px;
            padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem;
        }
        .top3-sidebar-item .user { font-weight: bold; color: var(--tiktok-cyan); }
        .top3-sidebar-item .server-id { font-size: 0.75rem; color: var(--text-muted); }

        .join-server-btn {
            background: linear-gradient(45deg, var(--tiktok-pink), var(--tiktok-cyan));
            color: #000 !important; font-weight: 800 !important; text-align: center; justify-content: center;
        }

        .auth-btn { background: rgba(254, 44, 85, 0.15); color: var(--tiktok-pink) !important; border: 1px solid var(--tiktok-pink); margin-bottom: 8px; text-align: center; justify-content: center; }

        .main-content { margin-right: 280px; flex: 1; padding: 2.5rem; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; padding: 2.5rem; width: 100%; max-width: 550px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8); text-align: right; }
        .card h2 { text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; }
        .card p.desc { text-align: center; color: var(--text-muted); margin-bottom: 1.5rem; }

        .btn-tiktok {
            display: inline-flex; align-items: center; justify-content: center; gap: 10px;
            background: var(--tiktok-pink); color: #fff; padding: 14px 28px; border-radius: 10px;
            font-weight: bold; font-size: 1rem; width: 100%; border: none; cursor: pointer; margin-top: 10px; text-decoration: none;
        }

        .form-group { margin-bottom: 1.2rem; }
        .form-group label { display: block; margin-bottom: 6px; font-weight: bold; font-size: 0.95rem; }
        input[type="text"], select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); background: #000; color: #fff; font-size: 0.95rem; outline: none; }

        .status-badge { display: inline-block; background: rgba(37, 244, 238, 0.15); color: var(--tiktok-cyan); border: 1px solid var(--tiktok-cyan); padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; margin-bottom: 15px; }
        .error { color: var(--tiktok-pink); background: rgba(254, 44, 85, 0.1); border: 1px solid var(--tiktok-pink); padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; }
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
            <div class="brand"><i class="fa-brands fa-tiktok"></i><span>لوحة التحكم</span></div>
            
            <ul class="nav-menu" style="margin-top: 1rem;">
                <li class="nav-item active"><a href="/"><i class="fa-solid fa-house"></i> الرئيسية</a></li>
            </ul>

            <div class="section-title"><i class="fa-solid fa-server"></i> السيرفرات المحفوظة</div>
            <ul class="saved-servers-list" id="savedServersMenu">
                <li style="color:var(--text-muted); font-size:0.8rem; text-align:center;">جاري التحميل...</li>
            </ul>

            <div class="section-title"><i class="fa-solid fa-crown"></i> أفضل ثوالث</div>
            <ul class="top3-sidebar-list" id="top3SidebarMenu">
                <li style="color:var(--text-muted); font-size:0.8rem; text-align:center;">لا توجد بيانات</li>
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
            <p class="desc">قم بإعداد حساب التيك توك وروم الديسكورد للتنبيه المباشر</p>

            <div id="content">
                <a href="/login" class="btn-tiktok"><i class="fa-brands fa-discord"></i> تسجيل الدخول عبر ديسكورد</a>
            </div>
        </div>
    </main>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        function reloadSidebar() {
            fetch('/api/saved-configs')
                .then(res => res.json())
                .then(data => {
                    const menu = document.getElementById('savedServersMenu');
                    const top3Menu = document.getElementById('top3SidebarMenu');

                    if (data.configs && data.configs.length > 0) {
                        menu.innerHTML = '';
                        top3Menu.innerHTML = '';

                        data.configs.forEach((item, index) => {
                            menu.innerHTML += `
                                <li class="saved-server-item">
                                    <span><i class="fa-solid fa-hashtag"></i> ${item.guild_id}</span>
                                    <strong style="color:var(--tiktok-cyan)">@${item.tiktok_user}</strong>
                                </li>`;

                            if (index < 3) {
                                top3Menu.innerHTML += `
                                    <li class="top3-sidebar-item">
                                        <span class="user">@${item.tiktok_user}</span>
                                        <span class="server-id">${item.guild_id}</span>
                                    </li>`;
                            }
                        });
                    } else {
                        menu.innerHTML = '<li style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:5px;">لا توجد سيرفرات محفوظة</li>';
                        top3Menu.innerHTML = '<li style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:5px;">لا توجد ثوالث حالياً</li>';
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
                            <div style="text-align: center; margin: 10px 0;"><span class="status-badge"><i class="fa-solid fa-bolt"></i> المراقبة التلقائية تعمل في الخلفية 🔥</span></div>
                            <div class="form-group"><label>يوزر التيك توك (TikTok Username):</label><input type="text" id="tiktokUser" placeholder="مثال: 2vce4"></div>
                            <div class="form-group"><label>رقم/آيدي روم التنبيهات (Channel ID):</label><input type="text" id="channelId" placeholder="مثال: 1538986763622813766"></div>
                            
                            <button onclick="saveSettings()" class="btn-tiktok"><i class="fa-solid fa-floppy-disk"></i> حفظ وتفعيل التنبيه الآلي</button>

                            <div id="responseMsg"></div>`;
                        document.getElementById('content').innerHTML = html;
                    } else {
                        document.getElementById('content').innerHTML = '<div class="error">لم يتم العثور على سيرفرات لديك فيها صلاحيات إدارة!</div>';
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

            msgDiv.innerHTML = '<div style="color:var(--text-muted); text-align:center; margin-top:10px;">جاري التفعيل والحفظ...</div>';

            fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ guild_id: guildId, tiktok_user: tiktokUser, channel_id: channelId })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success && data.sent) {
                    msgDiv.innerHTML = '<div class="success"><i class="fa-solid fa-circle-check"></i> تم الربط بنجاح! تم إرسال الرسالة التجريبية لـ ديسكورد.</div>';
                    reloadSidebar();
                } else {
                    msgDiv.innerHTML = '<div class="error"><i class="fa-solid fa-triangle-exclamation"></i> فشل إرسال الرسالة في السيرفر! سبب الخطأ: ' + data.details + '</div>';
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

# --- Routes ---

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
            "tiktok_user": data.get("tiktok_user", ""),
            "channel_id": data.get("channel_id", "")
        })
    return jsonify({"configs": result})

@app.route('/api/save', methods=['POST'])
def save_settings():
    data = request.json
    guild_id = str(data.get('guild_id')).strip()
    tiktok_user = data.get('tiktok_user', '').replace('@', '').strip()
    channel_id = str(data.get('channel_id', '')).strip()

    # حفظ وإضافة السيرفر مع السيرفرات السابقة دون مسحها
    configs = load_configs()
    configs[guild_id] = {"tiktok_user": tiktok_user, "channel_id": channel_id}
    save_configs(configs)

    # إرسال الرسالة التجريبية لتأكيد الربط
    sent, details = send_discord_alert(channel_id, tiktok_user, is_test=True)

    return jsonify({"success": sent, "sent": sent, "details": details})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
