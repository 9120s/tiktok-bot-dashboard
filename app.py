import os
import requests
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

# تعديل أسماء المتغيرات لتطابق الموجود في Render تماماً
DISCORD_CLIENT_ID = os.getenv("CLIENT_ID", os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")).strip()
DISCORD_CLIENT_SECRET = os.getenv("CLIENT_SECRET", os.getenv("DISCORD_CLIENT_SECRET", "")).strip()

SERVER_INVITE_URL = "https://discord.gg/YOUR_INVITE_CODE"

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم | TikTok Style</title>
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

        /* Sidebar */
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

        .join-server-btn:hover {
            opacity: 0.9;
            transform: scale(1.02);
        }

        /* Main Content */
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
            text-align: center;
        }

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
        }

        select {
            width: 100%;
            padding: 12px;
            margin-top: 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: #000;
            color: var(--tiktok-cyan);
            font-size: 1rem;
            outline: none;
            font-weight: 600;
        }

        .error {
            color: var(--tiktok-pink);
            background: rgba(254, 44, 85, 0.1);
            border: 1px solid var(--tiktok-pink);
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: relative; border-left: none; border-bottom: 1px solid var(--border-color); }
            .main-content { margin-right: 0; padding: 1.5rem; }
        }
    </style>
</head>
<body>

    <!-- القائمة الجانبية -->
    <aside class="sidebar">
        <div>
            <div class="brand">
                <i class="fa-brands fa-tiktok"></i>
                <span>لوحة التحكم</span>
            </div>
            <ul class="nav-menu">
                <li class="nav-item active">
                    <a href="/"><i class="fa-solid fa-house"></i> الرئيسية</a>
                </li>
                <li class="nav-item">
                    <a href="#"><i class="fa-solid fa-trophy"></i> أفضل ثالث للبثوث</a>
                </li>
                <li class="nav-item">
                    <a href="#"><i class="fa-solid fa-bookmark"></i> السيرفرات المحفوظة</a>
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

    <!-- المحتوى الرئيسي -->
    <main class="main-content">
        <div class="card">
            <h2>إدارة البوت</h2>
            <p style="color: var(--text-muted); margin-bottom: 2rem;">قم بتسجيل الدخول لاختيار السيرفر والتحكم بالإعدادات</p>
            
            <div id="content">
                <a href="/login" class="btn-tiktok">
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
            document.getElementById('content').innerHTML += `<div class="error">خطأ في التسجيل (${err}): يرجى التأكد من الـ Client Secret في Render.</div>`;
        }

        if (token) {
            document.getElementById('content').innerHTML = '<p style="color:var(--tiktok-cyan);"><i class="fa-solid fa-spinner fa-spin"></i> جاري تحميل جميع السيرفرات...</p>';
            fetch('/api/guilds?token=' + token)
                .then(res => res.json())
                .then(data => {
                    if (data.guilds && data.guilds.length > 0) {
                        let html = '<label style="display:block; text-align:right; margin-bottom:8px; font-weight:bold;">اختر السيرفر:</label><select id="guildSelect">';
                        data.guilds.forEach(g => {
                            html += `<option value="${g.id}">${g.name}</option>`;
                        });
                        html += '</select>';
                        document.getElementById('content').innerHTML = html;
                    } else {
                        document.getElementById('content').innerHTML = '<p>لم يتم العثور على سيرفرات.</p>';
                    }
                })
                .catch(err => {
                    document.getElementById('content').innerHTML = '<div class="error">حدث خطأ أثناء جلب البيانات.</div>';
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
                    guilds_list.append({"id": str(g['id']), "name": g['name']})
        except Exception as e:
            print("Fetch guilds error:", e)

    return jsonify({"guilds": guilds_list})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
