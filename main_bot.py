import os
import discord
from discord.ext import tasks, commands
from TikTokLive import TikTokLiveClient
from database import get_all_configs

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# قائمة لمتابعة الحسابات المسجلة للبث حالياً لمنع تكرار الإشعار
live_streamers = set()

@tasks.loop(seconds=60)
async def check_tiktok_lives():
    configs = get_all_configs()
    
    for guild_id, data in configs.items():
        username = data.get("tiktok_username")
        channel_id = data.get("channel_id")
        title = data.get("message_title", "بدأ بث مباشر!")
        
        if not username or not channel_id:
            continue
            
        try:
            client = TikTokLiveClient(unique_id=username)
            is_live = await client.is_live()
            
            stream_key = f"{guild_id}_{username}"
            
            # إذا كان الحساب أونلاين ولم يتم إرسال تنبيه له بعد
            if is_live and stream_key not in live_streamers:
                live_streamers.add(stream_key)
                channel = bot.get_channel(int(channel_id))
                if channel:
                    embed = discord.Embed(
                        title=f"🔴 {title}",
                        description=f"الحساب **@{username}** بدأ بث مباشر الآن على تيك توك!\n\n[اضغط هنا للمشاهدة](https://www.tiktok.com/@{username}/live)",
                        color=0xFF0050
                    )
                    await channel.send(content="@everyone", embed=embed)
                    
            # إذا انتهى البث، يتم إزالة الحساب من القائمة ليكون جاهزاً للبث القادم
            elif not is_live and stream_key in live_streamers:
                live_streamers.remove(stream_key)
                
        except Exception as e:
            print(f"Error checking {username}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    if not check_tiktok_lives.is_running():
        check_tiktok_lives.start()

bot.run(os.getenv("BOT_TOKEN"))
