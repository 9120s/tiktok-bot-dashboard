import os
import requests

JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_BIN_ID = os.getenv("JSONBIN_BIN_ID")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

def get_all_configs():
    """جلب جميع البيانات من JSONBin"""
    headers = {"X-Master-Key": JSONBIN_KEY}
    try:
        res = requests.get(BASE_URL, headers=headers)
        if res.status_code == 200:
            return res.json().get("record", {})
        return {}
    except Exception as e:
        print(f"Error reading JSONBin: {e}")
        return {}

def save_guild_config(guild_id, tiktok_username, channel_id, message_title):
    """حفظ أو تحديث إعدادات سيرفر معين"""
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_KEY
    }
    
    current_data = get_all_configs()
    
    current_data[str(guild_id)] = {
        "tiktok_username": tiktok_username.replace("@", "").strip(),
        "channel_id": str(channel_id).strip(),
        "message_title": message_title.strip()
    }
    
    try:
        res = requests.put(BASE_URL, json=current_data, headers=headers)
        return res.status_code == 200
    except Exception as e:
        print(f"Error writing to JSONBin: {e}")
        return False
