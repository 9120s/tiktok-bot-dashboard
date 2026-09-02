import os
import requests
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://tiktok-bot-2s2-dashboard.onrender.com/callback")

# رابط دعوة سيرفرك
SERVER_INVITE_URL = "https://discord.gg/YOUR_INVITE_CODE" 

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم البوت</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0f172a;
            --bg-sidebar: #1e293b;
            --bg-card: #1e293b;
            --accent: #5865F2;
            --accent-hover: #4752C4;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
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
            top: 0;
            bottom: 0;
            right: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--text-main);
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .brand i {
            color: var(--accent);
            font-size: 1.5rem;
        }

        .nav-menu {
            list-style: none;
            margin-top: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .nav-item a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: var(--text-muted);
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .nav-item a:hover, .nav-item.active a {
            background: rgba(88, 101, 242, 0.15);
            color: #fff;
        }

        .join-server-btn {
            background: linear-gradient(135deg, #5865F2, #eb459e);
            color: white !important;
            box-shadow: 0 4px 15px rgba(88, 101, 242, 0.3);
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
            max-width: 500px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            text-align: center;
        }

        .btn-discord {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: var(--accent);
            color: #fff;
            padding: 14px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1rem;
            transition: background 0.3s ease;
            width: 100%;
            border: none;
            cursor: pointer;
        }

        .btn-discord:hover {
            background: var(--accent-hover);
        }

        select {
            width: 100%;
            padding: 12px;
            margin-top: 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-main);
            color: #fff;
            font-size: 1rem;
            outline: none;
        }

        .error {
            color: #f87171;
            background: rgba(248, 113, 113, 0.1);
            padding: 10px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 0.88rem;
        }

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
                <i class="fa-solid fa-robot"></i>
                <span>لوحة التحكم</span>
            </div>
            <ul class="nav-menu">
                <li class="nav-item active">
                    <a href="/"><i class="fa-solid fa-house"></i> الرئيسية</a>
                </li>
            </ul>
        </div>

        <ul class="nav-menu">
            <li class="nav-item">
                <a href="{{ server_invite }}" target="_blank" class="join-server-btn">
                    <i class="fa-brands fa-discord"></i> انضم لسيرفرنا
                </a>
            </li>
        </ul>
    </aside>

    <main class="main-content">
        <div class="card">
            <h2>إدارة البوت</h2>
            <p style="color: var(--text-muted); margin-bottom: 2rem;">اختر السيرفر للبدء في ضبط الإعدادات</p>
            
            <div id="content">
                <a href="/login" class="btn-discord">
                    <i class="fa-brands fa-discord"></i> تسجيل الدخول عبر ديسكورد
                </a>
            </div>
        </div>
    </main>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const err = urlParams.get('err');

        if (err) {
            document.getElementById('content').innerHTML += `<div class="error">خطأ في عملية التسجيل: ${err}</div>`;
        }

        if (token) {
            document.getElementById('content').innerHTML = '<p><i class="fa-solid fa-spinner fa-spin"></i> جاري تحميل السيرفرات...</p>';
            fetch('/api/guilds?token=' + token)
                .then(res => res.json())
                .then(data => {
                    if (data.guilds && data.guilds.length > 0) {
                        let html = '<label style="display:block; text-align:right; margin-bottom:8px; font-weight:bold;">السيرفرات التي تمتلك فيها رتبة:</label><select id="guildSelect">';
                        data.guilds.forEach(g => {
                            html += `<option value="${g.id}">${g.name}</option>`;
                        });
                        html += '</select>';
                        document.getElementById('content').innerHTML = html;
                    } else {
                        document.getElementById('content').innerHTML = '<p>لم يتم العثور على سيرفرات تملك فيها رتبة بمصالحات إدارية أو تنظيمية.</p>';
                    }
                })
                .catch(err => {
                    document.getElementById('content').innerHTML = '<div class="error">حدث خطأ أثناء جلب السيرفرات.</div>';
                });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT, server_invite=SERVER_INVITE_URL)

@app.route('/login')
def login():
    discord_auth_url = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify+guilds"
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
        'redirect_uri': REDIRECT_URI
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
                    # يفحص الصلاحيات التالية: 
                    # Owner | Admin (0x8) | Manage Guild (0x20) | Manage Roles (0x10000000) | Manage Channels (0x10) | Kick Members (0x2) | Ban Members (0x4) | Mute Members (0x400000)
                    has_permission = (
                        g.get('owner') or 
                        (permissions & 0x8) != 0 or 
                        (permissions & 0x20) != 0 or 
                        (permissions & 0x10000000) != 0 or 
                        (permissions & 0x10) != 0 or 
                        (permissions & 0x2) != 0 or
                        (permissions & 0x4) != 0 or
                        (permissions & 0x400000) != 0
                    )
                    if has_permission:
                        guilds_list.append({"id": str(g['id']), "name": g['name']})
        except Exception as e:
            print("Fetch guilds error:", e)

    return jsonify({"guilds": guilds_list})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
