import os
import requests
from flask import Flask, render_template, request, jsonify, redirect

# تحديد المسار النهائي للمجلد لتجنب مشكلة الشاشة البيضاء
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1544289467853045861")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "")

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h3>حدث خطأ في تحميل الصفحة:</h3><p>{str(e)}</p>", 500

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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
