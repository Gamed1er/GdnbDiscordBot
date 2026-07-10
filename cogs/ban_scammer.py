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
            banned_user = message.author
            try:
                # 執行 Ban
                reason = "觸發陷阱頻道：疑似詐騙或惡意廣告機器人。"
                await banned_user.ban(reason=reason, delete_message_days=1)

                # 發送日誌到後台 (可選)
                log_msg = f"🛡️ **安全警報**：已自動 Ban 掉用戶 `{banned_user}` (ID: {banned_user.id})\n**原因**：在陷阱頻道發言。"
                print(log_msg) # 同時顯示在樹莓派日誌

                # 在陷阱頻道彈出說明 embed，並顯示誰被封禁
                embed = discord.Embed(
                    title="🚫 請勿在這個頻道發訊息",
                    description=(
                        "這個頻道是用來**防止詐騙**的陷阱頻道。\n"
                        "任何在此頻道發送訊息的帳號都會被自動封禁，"
                        "以阻擋詐騙與惡意廣告機器人。\n\n"
                        "如果你是不小心誤入的正常成員，請不要在此發言。"
                    ),
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="已被封禁的帳號",
                    value=f"{banned_user.mention} (`{banned_user}` / ID: `{banned_user.id}`)",
                    inline=False
                )
                if banned_user.display_avatar:
                    embed.set_thumbnail(url=banned_user.display_avatar.url)
                await message.channel.send(embed=embed)

            except discord.Forbidden:
                print(f"❌ 權限不足，無法 Ban 掉 {message.author}。")
            except discord.HTTPException as e:
                print(f"❌ 發生錯誤：{e}")

async def setup(bot):
    await bot.add_cog(BanScammer(bot))