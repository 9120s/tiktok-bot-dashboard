import os
import requests
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "")

# واجهة HTML مدمجة ومباشرة لمنع الشاشة البيضاء نهائياً
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم البوت</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 90%; max-width: 450px; text-align: center; }
        h2 { margin-bottom: 1.5rem; color: #38bdf8; }
        .btn { display: inline-block; background: #5865F2; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; transition: 0.2s; border: none; cursor: pointer; width: 100%; box-sizing: border-box; }
        .btn:hover { background: #4752C4; }
        select { width: 100%; padding: 10px; margin-top: 15px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 1rem; }
    </style>
</head>
<body>
    <div class="card">
        <h2>لوحة تحكم البوت</h2>
        <div id="content">
            <a href="/login" class="btn">تسجيل الدخول عبر ديسكورد</a>
        </div>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (token) {
            document.getElementById('content').innerHTML = '<p>جاري تحميل السيرفرات...</p>';
            fetch('/api/guilds?token=' + token)
                .then(res => res.json())
                .then(data => {
                    if (data.guilds && data.guilds.length > 0) {
                        let html = '<label>اختر السيرفر:</label><select id="guildSelect">';
                        data.guilds.forEach(g => {
                            html += `<option value="${g.id}">${g.name}</option>`;
                        });
                        html += '</select>';
                        document.getElementById('content').innerHTML = html;
                    } else {
                        document.getElementById('content').innerHTML = '<p>لم يتم العثور على سيرفرات تمتلك فيها صلاحيات إدارية.</p>';
                    }
                })
                .catch(err => {
                    document.getElementById('content').innerHTML = '<p>حدث خطأ أثناء جلب السيرفرات.</p>';
                });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/login')
def login():
    redirect_url = REDIRECT_URI if REDIRECT_URI else f"{request.host_url.rstrip('/')}/callback"
    discord_auth_url = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&response_type=code&redirect_uri={redirect_url}&scope=identify+guilds"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')
    
    redirect_url = REDIRECT_URI if REDIRECT_URI else f"{request.host_url.rstrip('/')}/callback"
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
        if r.status_code == 200:
            token = r.json().get('access_token')
            return redirect(f'/?token={token}')
    except Exception as e:
        print("Callback Error:", e)
        
    return redirect('/')

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
                    has_permission = (
                        g.get('owner') or 
                        (permissions & 0x8) != 0 or 
                        (permissions & 0x20) != 0 or 
                        (permissions & 0x10000000) != 0 or 
                        (permissions & 0x10) != 0 or 
                        (permissions & 0x20000000) != 0 or
                        (permissions & 0x2000) != 0
                    )
                    if has_permission:
                        guilds_list.append({"id": str(g['id']), "name": g['name']})
        except Exception as e:
            print("Fetch guilds error:", e)

    return jsonify({"guilds": guilds_list})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
