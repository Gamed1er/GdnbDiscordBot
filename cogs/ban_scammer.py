import discord
from discord.ext import commands

class BanScammer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 這裡填入你建立的「陷阱頻道」ID
        self.trap_channel_id = 1463485955767009302  

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 基本檢查：忽略機器人自己、忽略私訊
        if message.author == self.bot.user or not message.guild:
            return

        # 2. 檢查訊息是否發送在陷阱頻道
        if message.channel.id == self.trap_channel_id:
            try:
                # 執行 Ban
                reason = "觸發陷阱頻道：疑似詐騙或惡意廣告機器人。"
                await message.author.ban(reason=reason, delete_message_days=1)
                
                # 發送日誌到後台 (可選)
                log_msg = f"🛡️ **安全警報**：已自動 Ban 掉用戶 `{message.author}` (ID: {message.author.id})\n**原因**：在陷阱頻道發言。"
                print(log_msg) # 同時顯示在樹莓派日誌
                
                # 如果你想通知其他管理員，可以在這裡指定一個管理頻道發送
                # admin_channel = self.bot.get_channel(管理頻道ID)
                # await admin_channel.send(log_msg)

            except discord.Forbidden:
                print(f"❌ 權限不足，無法 Ban 掉 {message.author}。")
            except discord.HTTPException as e:
                print(f"❌ 發生錯誤：{e}")

async def setup(bot):
    await bot.add_cog(BanScammer(bot))