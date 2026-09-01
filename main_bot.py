import os
import requests
from flask import Flask, redirect, url_for, session, request, render_template_string

app = Flask(__name__)

# إعدادات المفاتيح المتغيرة
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-12345")
CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")

API_BASE_URL = "https://discord.com/api/v10"

# قالب الصفحة الرئيسية وتصميم إعدادات التفاعل في البث
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة تحكم البوت</title>
    <style>
        body { font-family: sans-serif; background-color: #1e1e2e; color: #cdd6f4; text-align: center; padding: 40px; }
        .card { background: #313244; padding: 25px; border-radius: 12px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .btn { background-color: #5865F2; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 15px; }
        .btn:hover { background-color: #4752C4; }
        .form-group { margin-bottom: 15px; text-align: right; }
        label { display: block; margin-bottom: 5px; font-size: 14px; color: #a6adc8; }
        input[type="text"], select { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #45475a; background: #1e1e2e; color: #cdd6f4; box-sizing: border-box; }
        .user-badge { margin-bottom: 20px; }
        .user-badge img { border-radius: 50%; width: 80px; height: 80px; }
    </style>
</head>
<body>
    <div class="card">
        {% if user %}
            <div class="user-badge">
                <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
                <h2>أهلاً بك، {{ user.username }}</h2>
            </div>
            
            <form action="/save-settings" method="POST">
                <h3>إعدادات إشعار أفضل 3 متفاعلين</h3>
                <div class="form-group">
                    <label>اختر السيرفر:</label>
                    <select name="guild_id">
                        {% for guild in guilds %}
                            <option value="{{ guild.id }}">{{ guild.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>عنوان الإشعار (مثال: 🏆 أفضل 3 متفاعلين في البث):</label>
                    <input type="text" name="top_title" value="🏆 أفضل 3 متفاعلين في البث" required>
                </div>
                
                <div class="form-group">
                    <label>معرّف قناة الإشعارات (Channel ID):</label>
                    <input type="text" name="channel_id" placeholder="أدخل ID القناة" required>
                </div>
                
                <button type="submit" class="btn">حفظ الإعدادات</button>
            </form>
            <br>
            <a href="/logout" style="color: #f38ba8; text-decoration: none; font-size: 14px;">تسجيل الخروج</a>
        {% else %}
            <h2>لوحة تحكم بوت تيك توك</h2>
            <p>يرجى تسجيل الدخول للتحكم بإعدادات الإشعارات والتفاعل</p>
            <a href="/login" class="btn">تسجيل الدخول بالديسكورد</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    user = session.get('user')
    guilds = session.get('guilds', [])
    return render_template_string(INDEX_HTML, user=user, guilds=guilds)

@app.route('/login')
def login():
    scope = "identify guilds"
    discord_auth_url = (
        f"{API_BASE_URL}/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope}"
    )
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')

    # 1. تبادل Code بـ Access Token
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_res = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    token_json = token_res.json()
    access_token = token_json.get('access_token')

    if not access_token:
        return redirect('/')

    # 2. جلب بيانات المستخدم
    user_headers = {'Authorization': f"Bearer {access_token}"}
    user_res = requests.get(f"{API_BASE_URL}/users/@me", headers=user_headers)
    user_data = user_res.json()

    # 3. جلب السيرفرات وتصفيتها لحل مشكلة حجم الـ Session (Cookie Size Limit)
    guilds_res = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers=user_headers)
    all_guilds = guilds_res.json()

    filtered_guilds = []
    if isinstance(all_guilds, list):
        for g in all_guilds:
            permissions = int(g.get('permissions', 0))
            # الحفظ فقط للسيرفرات التي يملك فيها صلاحية Administrator (0x8) أو المالك
            if (permissions & 0x8) == 0x8 or g.get('owner', False):
                filtered_guilds.append({
                    'id': g['id'],
                    'name': g['name'],
                    'icon': g.get('icon')
                })

    # حفظ البيانات المصغرة في Session
    session['user'] = {
        'id': user_data.get('id'),
        'username': user_data.get('username'),
        'avatar': user_data.get('avatar')
    }
    session['guilds'] = filtered_guilds

    return redirect('/')

@app.route('/save-settings', methods=['POST'])
def save_settings():
    if 'user' not in session:
        return redirect('/login')

    guild_id = request.form.get('guild_id')
    top_title = request.form.get('top_title')
    channel_id = request.form.get('channel_id')

    # هنا يتم حفظ الإعدادات أو إرسالها للبوت الخاص بك
    print(f"[حفظ الإعدادات] السيرفر: {guild_id} | القناة: {channel_id} | عنوان التفاعل: {top_title}")

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
