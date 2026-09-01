import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-2s2')

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# نموذج التنبيهات
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(100), nullable=False)
    channel_id = db.Column(db.String(100), nullable=False)
    tiktok_username = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# تصفية السيرفرات بناءً على صلاحيات الإدارة للمستخدم (Administrator / Manage Server)
def filter_manageable_guilds(guilds):
    manageable = []
    for g in guilds:
        perms = int(g.get('permissions', 0))
        # 0x8 تعني Administrator و 0x20 تعني Manage Server
        if (perms & 0x8) == 0x8 or (perms & 0x20) == 0x20:
            manageable.append(g)
    return manageable

@app.route('/')
def index():
    user = session.get('user')
    guilds = session.get('user_guilds', [])
    
    # تصفية قائمة السيرفرات المتاحة للمستخدم حسب صلاحياته فقط
    filtered_guilds = filter_manageable_guilds(guilds) if guilds else []
    
    alerts = Alert.query.all()
    return render_template('index.html', user=user, guilds=filtered_guilds, alerts=alerts)

# مسار تسجيل الخروج الصحيح
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# إضافة تنبيه جديد
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

# حذف تنبيه
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
