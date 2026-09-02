import os
import asyncio
import threading
import requests
from flask import Flask
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent

app = Flask(__name__)

# ==================== الإعدادات ====================
# يمكنك تعيين القيم هنا مباشرة أو استخدام متغيرات البيئة (Environment Variables)
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "2vce4")  # يوزر التيك توك
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "ضع_رابط_الويب_هوك_هنا")  # رابط الـ Webhook الخاص بروم الديسكورد
# ===================================================

def send_discord_webhook(username):
    """إرسال تنبيه إلى ديسكورد عبر Webhook فور فتح البث"""
    payload = {
        "content": f"🚨 **تنبيه بث جديد!**\nقام الحساب **@{username}** ببدء بث مباشر الآن على تيك توك!\nhttps://www.tiktok.com/@{username}/live"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            print(f"[+] تم إرسال التنبيه بنجاح للحساب @{username}")
        else:
            print(f"[-] فشل إرسال التنبيه: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[-] حدث خطأ أثناء إرسال التنبيه: {e}")

async def tiktok_monitor():
    """مراقبة البث المباشر في الخلفية بشكل مستمر"""
    while True:
        try:
            print(f"[*] بدء مراقبة حساب التيك توك: @{TIKTOK_USERNAME}")
            client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)

            @client.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                print(f"[!] تم اكتشاف فتح البث للحساب @{TIKTOK_USERNAME}!")
                send_discord_webhook(TIKTOK_USERNAME)

            # الاتصال بالبث والانتظار
            await client.start()

        except Exception as e:
            # في حال عدم وجود بث أو انقطاع الاتصال، ينتظر 30 ثانية ثم يعيد المحاولة تلقائياً
            await asyncio.sleep(30)

def start_background_loop():
    """تشغيل المراقبة التلقائية في السلسلة الخلفية (Background Thread)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tiktok_monitor())

# تشغيل المراقبة التلقائية فور بدء السكربت
threading.Thread(target=start_background_loop, daemon=True).start()

@app.route('/')
def home():
    """مسار بسيط للتأكد من أن السكربت يعمل ولربطه بـ UptimeRobot"""
    return f"Bot is running 24/7! Monitoring TikTok user: @{TIKTOK_USERNAME}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
