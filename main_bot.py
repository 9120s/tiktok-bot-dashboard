import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-2s2')

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# إعدادات Discord OAuth2
CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', 'https://tiktok-bot-2s2-dashboard.onrender.com/callback')
API_BASE_URL = 'https://discord.com/api/v10'

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(100), nullable=False)
    channel_id = db.Column(db.String(100), nullable=False)
    tiktok_username = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# دالة لتصفية السيرفرات بناءً على صلاحيات الإدارة للمستخدم (Administrator: 0x8 أو Manage Server: 0x20)
def filter_manageable_guilds(guilds):
    manageable = []
    if not guilds or not isinstance(guilds, list):
        return manageable
    for g in guilds:
        perms = int(g.get('permissions', 0))
        if (perms & 0x8) == 0x8 or (perms & 0x20) == 0x20:
            manageable.append(g)
    return manageable

@app.route('/')
def index():
    user = session.get('user')
    guilds = session.get('user_guilds', [])
    filtered_guilds = filter_manageable_guilds(guilds)
    alerts = Alert.query.all()
    return render_template('index.html', user=user, guilds=filtered_guilds, alerts=alerts)

# مسار تسجيل الدخول عبر ديسكورد
@app.route('/login')
def login():
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_login_url)

# استقبال استجابة ديسكورد وجلب البيانات
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'identify guilds'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f'{API_BASE_URL}/oauth2/token', data=data, headers=headers)
    tokens = r.json()
    access_token = tokens.get('access_token')

    if access_token:
        headers_auth = {'Authorization': f'Bearer {access_token}'}
        user_req = requests.get(f'{API_BASE_URL}/users/@me', headers=headers_auth)
        guilds_req = requests.get(f'{API_BASE_URL}/users/@me/guilds', headers=headers_auth)
        
        session['user'] = user_req.json()
        session['user_guilds'] = guilds_req.json()

    return redirect(url_for('index'))

# مسار تسجيل الخروج الفعلي ومسح الجلسة والكوكيز
@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('session', '', expires=0)
    return resp

@app.route('/add_alert', methods=['POST'])
def add_alert():
    guild_id = request.form.get('guild_id')
    channel_id = request.form.get('channel_id')
    tiktok_username = request.form.get('tiktok_username')

    if guild_id and channel_id and tiktok_username:
        new_alert = Alert(guild_id=guild_id, channel_id=channel_id, tiktok_username=tiktok_username.strip())
        db.session.add(new_alert)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/delete_alert/<int:id>', methods=['POST'])
def delete_alert(id):
    alert = Alert.query.get(id)
    if alert:
        db.session.delete(alert)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
