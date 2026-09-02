import os
import requests
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("CLIENT_ID", os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")).strip()
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET", os.getenv("DISCORD_CLIENT_SECRET", "")).strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

SERVER_INVITE_URL = "https://discord.gg/YOUR_INVITE_CODE"

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

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 260px;
            background: var(--bg-sidebar);
            border-left: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 1.5rem 1rem;
            position: fixed;
            top: 0; bottom: 0; right: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.3rem;
            font-weight: 800;
            color: var(--text-main);
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            text-shadow: 2px 2px var(--tiktok-pink), -2px -2px var(--tiktok-cyan);
        }

        .nav-menu {
            list-style: none;
            margin-top: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .nav-item a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: var(--text-muted);
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .nav-item a:hover, .nav-item.active a {
            background: #27272a;
            color: var(--tiktok-cyan);
        }

        .join-server-btn {
            background: linear-gradient(45deg, var(--tiktok-pink), var(--tiktok-cyan));
            color: #000 !important;
            font-weight: 800 !important;
            box-shadow: 0 4px 15px rgba(254, 44, 85, 0.4);
        }

        .auth-btn {
            background: rgba(254, 44, 85, 0.15);
            color: var(--tiktok-pink) !important;
            border: 1px solid var(--tiktok-pink);
            margin-bottom: 8px;
        }

        .auth-btn:hover {
            background: var(--tiktok-pink) !important;
            color: #fff !important;
        }

        .main-content {
            margin-right: 260px;
            flex: 1;
            padding: 2.5rem;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2.5rem;
            width: 100%;
            max-width: 520px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
            text-align: right;
        }

        .card h2 { text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; }
        .card p.desc { text-align: center; color: var(--text-muted); margin-bottom: 2rem; }

        .btn-tiktok {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: var(--tiktok-pink);
            color: #fff;
            padding: 14px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 100%;
            border: none;
            cursor: pointer;
            box-shadow: 0 0 15px rgba(254, 44, 85, 0.5);
            margin-top: 15px;
        }

        .btn-tiktok:hover { background: #e02649; }

        .form-group { margin-bottom: 1.2rem; }
        .form-group label { display: block; margin-bottom: 6px; font-weight: bold; font-size: 0.95rem; }

        input[type="text"], select {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: #000;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
        }

        .status-badge {
            display: inline-block;
            background: rgba(37, 244, 238, 0.15);
            color: var(--tiktok-cyan);
            border: 1px solid var(--tiktok-cyan);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-bottom: 15px;
        }

        .error {
            color: var(--tiktok-pink);
            background: rgba(254, 44, 85, 0.1);
            border: 1px solid var(--tiktok-pink);
            padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center;
        }

        .success {
            color: #4ade80;
            background: rgba(74, 222, 128, 0.1);
            border: 1px solid #4ade80;
            padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center;
        }

        .page-section { display: none; }
        .page-section.active { display: block; }

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
            <div class="brand">
                <i class="fa-brands fa-tiktok"></i>
                <span>لوحة التحكم</span>
            </div>
            <ul class="nav-menu">
                <li class="nav-item active" id="nav-home">
                    <a onclick="switchTab('home')"><i class="fa-solid fa-house"></i> الرئيسية</a>
                </li>
                <li class="nav-item" id="nav-top">
                    <a onclick="switchTab('top')"><i class="fa-solid fa-trophy"></i> أفضل ثوالث للبثوث</a>
                </li>
                <li class="nav-item" id="nav-saved">
                    <a onclick="switchTab('saved')"><i class="fa-solid fa-bookmark"></i> السيرفرات المحفوظة</a>
                </li>
            </ul>
        </div>

        <ul class="nav-menu">
            <li class="nav-item" id="authNavItem">
                <a href="/login" class="auth-btn" id="authBtn">
                    <i class="fa-solid fa-right-to-bracket"></i> تسجيل الدخول
                </a>
            </li>
            <li class="nav-item">
                <a href="{{ server_invite }}" target="_blank" class="join-server-btn">
                    <i class="fa-brands fa-discord"></i> انضم لسيرفرنا
                </a>
            </li>
        </ul>
    </aside>

    <main class="main-content">
        <div id="section-home" class="card page-section active">
            <h2>إدارة البوت</h2>
            <p class="desc">قم بتسجيل الدخول لاختيار السيرفر والتحكم بالإعدادات</p>
            
            <div id="content">
                <a href="/login" class="btn-tiktok">
                    <i class="fa-brands fa-discord"></i> تسجيل الدخول عبر ديسكورد
                </a>
            </div>
        </div>

        <div id="section-top" class="card page-section">
            <h2>🏆 أفضل ثوالث للبثوث</h2>
            <p class="desc">قائمة بـ أفضل البثوث النشطة حالياً</p>
            <div style="text-align: center; color: var(--text-muted); padding: 20px 0;">
                <i class="fa-solid fa-fire fa-2x" style="color: var(--tiktok-pink); margin-bottom: 10px;"></i>
                <p>قريباً سيتم عرض ترتيب البثوث المباشرة هنا!</p>
            </div>
        </div>

        <div id="section-saved" class="card page-section">
            <h2>🔖 السيرفرات المحفوظة</h2>
            <p class="desc">إدارة السيرفرات التي تم ضبط إعداداتها سابقاً</p>
            <div id="savedGuildsList" style="text-align: center; color: var(--text-muted); padding: 20px 0;">
                <i class="fa-solid fa-server fa-2x" style="color: var(--tiktok-cyan); margin-bottom: 10px;"></i>
                <p>لم يتم حفظ أي سيرفرات بعد.</p>
            </div>
        </div>
    </main>

    <script>
        function switchTab(tab) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active'));

            if (tab === 'home') {
                document.getElementById('nav-home').classList.add('active');
                document.getElementById('section-home').classList.add('active');
            } else if (tab === 'top') {
                document.getElementById('nav-top').classList.add('active');
                document.getElementById('section-top').classList.add('active');
            } else if (tab === 'saved') {
                document.getElementById('nav-saved').classList.add('active');
                document.getElementById('section-saved').classList.add('active');
            }
        }

        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const err = urlParams.get('err');

        if (err) {
            document.getElementById('content').innerHTML += `<div class="error">خطأ في التسجيل (${err})</div>`;
        }

        if (token) {
            const authBtn = document.getElementById('authBtn');
            authBtn.href = '/';
            authBtn.innerHTML = '<i class="fa-solid fa-right-from-bracket"></i> تسجيل الخروج';

            document.getElementById('content').innerHTML = '<p style="color:var(--tiktok-cyan); text-align:center;"><i class="fa-solid fa-spinner fa-spin"></i> جاري جلب السيرفرات...</p>';
            fetch('/api/guilds?token=' + token)
                .then(res => res.json())
                .then(data => {
                    if (data.guilds && data.guilds.length > 0) {
                        let html = `
                            <div class="form-group">
                                <label>اختر السيرفر اللي فيه رتبتك:</label>
                                <select id="guildSelect">
                        `;
                        data.guilds.forEach(g => {
                            html += `<option value="${g.id}">${g.name}</option>`;
                        });
                        html += `
                                </select>
                            </div>

                            <div style="text-align: center; margin: 10px 0;">
                                <span class="status-badge"><i class="fa-solid fa-bolt"></i> حالة البوت: جاهز للبث🔥</span>
                            </div>

                            <div class="form-group">
                                <label><i class="fa-brands fa-tiktok"></i> يوزر التيك توك (TikTok Username):</label>
                                <input type="text" id="tiktokUser" placeholder="مثال: 2vce4">
                            </div>

                            <div class="form-group">
                                <label><i class="fa-solid fa-hashtag"></i> رقم/آيدي روم التنبيهات (Channel ID):</label>
                                <input type="text" id="channelId" placeholder="مثال: 1538986763622813766">
                            </div>

                            <button onclick="saveSettings()" class="btn-tiktok">
                                <i class="fa-solid fa-floppy-disk"></i> حفظ التنبيهات
                            </button>

                            <div id="responseMsg"></div>
                        `;
                        document.getElementById('content').innerHTML = html;
                    } else {
                        document.getElementById('content').innerHTML = '<p style="text-align:center;">لم يتم العثور على سيرفرات تملك فيها رتبة.</p>';
                    }
                })
                .catch(err => {
                    document.getElementById('content').innerHTML = '<div class="error">حدث خطأ أثناء جلب البيانات.</div>';
                });
        }

        function saveSettings() {
            const guildSelect = document.getElementById('guildSelect');
            const guildId = guildSelect.value;
            const guildName = guildSelect.options[guildSelect.selectedIndex].text;
            const tiktokUser = document.getElementById('tiktokUser').value.trim();
            const channelId = document.getElementById('channelId').value.trim();
            const msgDiv = document.getElementById('responseMsg');

            if (!tiktokUser || !channelId) {
                msgDiv.innerHTML = '<div class="error">يرجى ملء يوزر التيك توك ورقم الروم أولاً.</div>';
                return;
            }

            msgDiv.innerHTML = '<p style="color:var(--tiktok-cyan); text-align:center; margin-top:10px;"><i class="fa-solid fa-spinner fa-spin"></i> جاري حفظ التنبيهات...</p>';

            fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    guild_id: guildId,
                    tiktok_user: tiktokUser,
                    channel_id: channelId
                })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    msgDiv.innerHTML = '<div class="success"><i class="fa-solid fa-circle-check"></i> تم حفظ إعدادات التنبيهات بنجاح! جاهز للبث🔥</div>';
                    document.getElementById('savedGuildsList').innerHTML = `
                        <div style="background:#000; padding:15px; border-radius:8px; border:1px solid var(--tiktok-cyan); text-align:right;">
                            <p style="color:var(--tiktok-cyan); font-weight:bold;"><i class="fa-solid fa-server"></i> ${guildName}</p>
                            <p style="font-size:0.85rem; color:var(--text-muted); margin-top:5px;">التيك توك: @${tiktokUser} | الروم: ${channelId}</p>
                        </div>
                    `;
                } else {
                    msgDiv.innerHTML = `<div class="error">حدث خطأ أثناء الحفظ: ${data.error || 'تأكد من البيانات'}</div>`;
                }
            })
            .catch(e => {
                msgDiv.innerHTML = '<div class="error">خطأ في الاتصال بالسيرفر.</div>';
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
    return request.host_url.rstrip('/') + '/callback'

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
    if not code:
        return redirect('/?err=nocode')
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': get_redirect_uri()
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
        if r.status_code == 200:
            token = r.json().get('access_token')
            return redirect(f'/?token={token}')
        else:
            return redirect(f'/?err=auth_failed_{r.status_code}')
    except Exception as e:
        return redirect(f'/?err={str(e)}')

@app.route('/api/guilds', methods=['GET'])
def get_guilds():
    user_token = request.args.get('token')
    guilds_list = []

    if user_token and user_token not in ['demo', 'null', 'undefined', '']:
        try:
            headers = {'Authorization': f'Bearer {user_token}'}
            res = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers)
            if res.status_code == 200:
                for g in res.json():
                    permissions = int(g.get('permissions', 0))
                    has_role_permission = (
                        g.get('owner') or 
                        (permissions & 0x8) != 0 or 
                        (permissions & 0x20) != 0 or 
                        (permissions & 0x10000000) != 0 or 
                        (permissions & 0x10) != 0 or 
                        (permissions & 0x2) != 0 or 
                        (permissions & 0x4) != 0 or 
                        (permissions & 0x400000) != 0 or 
                        (permissions & 0x2000) != 0
                    )
                    if has_role_permission:
                        guilds_list.append({"id": str(g['id']), "name": g['name']})
        except Exception as e:
            print("Fetch guilds error:", e)

    return jsonify({"guilds": guilds_list})

@app.route('/api/save', methods=['POST'])
def save_settings():
    data = request.json
    guild_id = data.get('guild_id')
    tiktok_user = data.get('tiktok_user')
    channel_id = data.get('channel_id')

    print(f"Saved Config: Guild={guild_id}, TikTok={tiktok_user}, Channel={channel_id}")
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
