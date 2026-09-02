import os
import json
import threading
import requests
from flask import Flask, redirect, session, request, render_template_string
import discord
from discord.ext import commands
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

# --------------------------------------------------
# 1. الإعدادات وإدارة الحفظ
# --------------------------------------------------

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey12345")
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

CLIENT_ID = os.environ.get("CLIENT_ID") or os.environ.get("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET") or os.environ.get("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("REDIRECT_URI") or os.environ.get("DISCORD_REDIRECT_URI", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN", "")

API_BASE_URL = "https://discord.com/api/v10"
CONFIG_FILE = "guilds_config.json"

def load_configs():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_configs():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(GUILDS_CONFIG, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[Config Save Error] {e}")

GUILDS_CONFIG = load_configs()

# --------------------------------------------------
# 2. إعدادات بوت ديسكورد (Discord Bot)
# --------------------------------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

def run_bot():
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("Error: BOT_TOKEN is missing!")

# --------------------------------------------------
# 3. لوحة التحكم بتصميم القائمة الجانبية المتقدم
# --------------------------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Bot Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f1015;
            --card-bg: #181920;
            --accent-color: #ff0050;
            --sidebar-bg: #121319;
            --text-color: #ffffff;
            --text-muted: #a0a5b5;
            --border-color: #262833;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-color); min-height: 100vh; overflow-x: hidden; }

        /* Navbar Header */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 25px;
            background-color: var(--sidebar-bg);
            border-bottom: 1px solid var(--border-color);
        }

        .menu-btn {
            background: none;
            border: none;
            color: var(--text-color);
            font-size: 24px;
            cursor: pointer;
            transition: color 0.3s;
        }

        .menu-btn:hover { color: var(--accent-color); }

        .brand { font-size: 20px; font-weight: bold; display: flex; align-items: center; gap: 10px; }
        .brand i { color: var(--accent-color); }

        /* Sidebar Navigation */
        .sidebar {
            position: fixed;
            top: 0;
            right: -280px;
            width: 280px;
            height: 100%;
            background-color: var(--sidebar-bg);
            box-shadow: -5px 0 15px rgba(0,0,0,0.5);
            transition: right 0.3s ease;
            z-index: 1000;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }

        .sidebar.active { right: 0; }

        .sidebar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 20px;
        }

        .close-btn { background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; }
        .close-btn:hover { color: var(--text-color); }

        .nav-links { list-style: none; display: flex; flex-direction: column; gap: 10px; }
        .nav-links li a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 15px;
            color: var(--text-muted);
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
        }

        .nav-links li a:hover, .nav-links li a.active {
            background-color: rgba(255, 0, 80, 0.1);
            color: var(--accent-color);
        }

        .overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6);
            display: none;
            z-index: 999;
        }
        .overlay.active { display: block; }

        /* Main Content Grid */
        .container { max-width: 900px; margin: 40px auto; padding: 0 20px; }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }

        .form-group { margin-bottom: 20px; text-align: right; }
        .form-group label { display: block; margin-bottom: 8px; color: var(--text-muted); font-size: 14px; }
        .form-control {
            width: 100%;
            padding: 12px 15px;
            background-color: #101117;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-color);
            font-size: 14px;
            outline: none;
        }
        .form-control:focus { border-color: var(--accent-color); }

        .btn-submit {
            width: 100%;
            padding: 12px;
            background-color: var(--accent-color);
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn-submit:hover { opacity: 0.9; }

        .btn-login {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background-color: #5865F2;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>

    <!-- Header Navbar -->
    <div class="navbar">
        <button class="menu-btn" onclick="toggleMenu()"><i class="fa-solid fa-bars"></i></button>
        <div class="brand"><i class="fa-brands fa-tiktok"></i> TikTok Bot Dashboard</div>
        <div>
            {% if logged_in %}
                <span style="color: var(--text-muted); font-size: 14px;">{{ user['username'] }}</span>
            {% endif %}
        </div>
    </div>

    <!-- Overlay -->
    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>

    <!-- Sidebar Navigation -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h3>القائمة الرئيسية</h3>
            <button class="close-btn" onclick="toggleMenu()"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <ul class="nav-links">
            <li><a href="#" class="active" onclick="switchTab('settings')"><i class="fa-solid fa-gear"></i> الإعدادات العامة</a></li>
            <li><a href="#" onclick="switchTab('top3')"><i class="fa-solid fa-trophy"></i> أفضل ثوالث (Top Streamers)</a></li>
            {% if logged_in %}
                <li style="margin-top: auto;"><a href="/logout" style="color: #ff4757;"><i class="fa-solid fa-right-from-bracket"></i> تسجيل الخروج</a></li>
            {% endif %}
        </ul>
    </div>

    <!-- Main Body Container -->
    <div class="container">
        {% if not logged_in %}
            <div class="card" style="text-align: center; padding: 50px;">
                <h2 style="margin-bottom: 15px;">مرحباً بك في لوحة التحكم</h2>
                <p style="color: var(--text-muted); margin-bottom: 25px;">يرجى تسجيل الدخول عبر ديسكورد للتحكم بإعدادات البوت</p>
                <a class="btn-login" href="/login"><i class="fa-brands fa-discord"></i> دخول بحساب Discord</a>
            </div>
        {% else %}
            <!-- Tab 1: Settings -->
            <div id="settings" class="tab-content active">
                <div class="card">
                    <h2 style="margin-bottom: 20px;"><i class="fa-solid fa-sliders"></i> إعدادات التنبيهات</h2>
                    <form action="/save-settings" method="POST">
                        <div class="form-group">
                            <label>السيرفر المستهدف:</label>
                            <select name="guild_id" class="form-control">
                                {% for guild in guilds %}
                                    <option value="{{ guild['id'] }}">{{ guild['name'] }}</option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="form-group">
                            <label>رقم روم التنبيهات (Channel ID):</label>
                            <input type="text" name="channel_id" class="form-control" placeholder="أدخل ID القناة هنا" required>
                        </div>

                        <div class="form-group">
                            <label>عنوان التنبيه:</label>
                            <input type="text" name="top_title" class="form-control" placeholder="مثال: البث مباشر الآن!">
                        </div>

                        <button type="submit" class="btn-submit">حفظ الإعدادات</button>
                    </form>
                </div>
            </div>

            <!-- Tab 2: Top 3 Streamers -->
            <div id="top3" class="tab-content">
                <div class="card">
                    <h2 style="margin-bottom: 20px;"><i class="fa-solid fa-trophy" style="color: gold;"></i> قائمة أفضل ثوالث</h2>
                    <p style="color: var(--text-muted); margin-bottom: 15px;">عرض إحصائيات ومعلومات الداعمين وأفضل المجموعات.</p>
                    <div style="padding: 20px; background: #101117; border-radius: 8px; text-align: center; color: var(--text-muted);">
                        قريباً: سيتم مزامنة أفضل ثوالث وتحديثها تلقائياً مع بث التيك توك.
                    </div>
                </div>
            </div>
        {% endif %}
    </div>

    <script>
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            toggleMenu();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    logged_in = 'user' in session
    user = session.get('user', None)
    guilds = session.get('guilds', [])
    return render_template_string(DASHBOARD_HTML, logged_in=logged_in, user=user, guilds=guilds)

@app.route('/login')
def login():
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "لم يتم استلام كود التوثيق من ديسكورد", 400

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        token_res = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
        token_data = token_res.json()
        access_token = token_data.get('access_token')

        if not access_token:
            return f"<h3>فشل الحصول على التوكين</h3><p>رد ديسكورد: {token_data}</p>", 400

        user_headers = {'Authorization': f"Bearer {access_token}"}
        user_data = requests.get(f"{API_BASE_URL}/users/@me", headers=user_headers).json()
        all_guilds = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers=user_headers).json()

        filtered_guilds = []
        if isinstance(all_guilds, list):
            for g in all_guilds:
                permissions = int(g.get('permissions', 0))
                if (permissions & 0x8) == 0x8 or g.get('owner', False):
                    filtered_guilds.append({'id': str(g['id']), 'name': g['name'], 'icon': g.get('icon')})

        session['user'] = {'id': user_data.get('id'), 'username': user_data.get('username'), 'avatar': user_data.get('avatar')}
        session['guilds'] = filtered_guilds
        return redirect('/')

    except Exception as e:
        return f"<h3>حدث خطأ في السيرفر:</h3><p>{e}</p>", 500

@app.route('/save-settings', methods=['POST'])
def save_settings():
    if 'user' not in session:
        return redirect('/login')

    guild_id = request.form.get('guild_id')
    if not guild_id and session.get('guilds'):
        guild_id = session['guilds'][0]['id']

    if guild_id:
        GUILDS_CONFIG[str(guild_id)] = {
            "channel_id": request.form.get('channel_id'),
            "top_title": request.form.get('top_title')
        }
        save_configs()
        return redirect(f'/?guild_id={guild_id}')

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --------------------------------------------------
# 4. تشغيل البوت واللوحة معاً
# --------------------------------------------------

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port)
