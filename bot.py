import asyncio
import discord
from discord.ext import commands
from TikTokLive import TikTokLiveClient
import database

# Token البوت الخاص بك
BOT_TOKEN = 'MTU0NDI4OTQ2Nzg1MzA0NTg2MQ.Gy9z8P.79IVHdLyiitKCKLpCRkea6EoRWt_ftp_iM_dw8'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# قاموس لمتابعة البثوث النشطة لمنع تكرار التنبيه
active_streams = {}

async def check_tiktok_lives():
    await bot.wait_until_ready()
    print("بدأ موجه فحص بثوث التيك توك...")
    
    while not bot.is_closed():
        try:
            subscriptions = database.get_all_subscriptions()
            for sub in subscriptions:
                guild_id, channel_id, tiktok_username = sub[0], int(sub[1]), sub[2]

                client = TikTokLiveClient(unique_id=tiktok_username)

                try:
                    is_live = await client.is_live()
                except Exception as e:
                    is_live = False

                # إذا الحساب فتح بث ولم يرسل تنبيه سابقاً
                if is_live and not active_streams.get(tiktok_username, False):
                    active_streams[tiktok_username] = True
                    channel = bot.get_channel(channel_id)
                    if channel:
                        embed = discord.Embed(
                            title=f"🔴 {tiktok_username} بدأ بث مباشر الآن على TikTok!",
                            url=f"https://www.tiktok.com/@{tiktok_username}/live",
                            color=discord.Color.red()
                        )
                        embed.add_field(name="رابط البث", value=f"[اضغط هنا للانضمام للبث](https://www.tiktok.com/@{tiktok_username}/live)", inline=False)
                        embed.set_footer(text="TikTok Live Notification")
                        
                        await channel.send(content="@everyone معاذ بدأ بث حياكم!", embed=embed)
                        print(f"تم إرسال تنبيه البث للحساب: {tiktok_username}")

                # إذا انتهى البث
                elif not is_live and active_streams.get(tiktok_username, False):
                    active_streams[tiktok_username] = False

        except Exception as e:
            print(f"خطأ أثناء فحص البث: {e}")

        # الفحص كل 30 ثانية
        await asyncio.sleep(30)

@bot.event
async def on_ready():
    print(f'✅ تم تشغيل البوت بنجاح باسم: {bot.user}')
    bot.loop.create_task(check_tiktok_lives())

if __name__ == '__main__':
    bot.run(BOT_TOKEN)