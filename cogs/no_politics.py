import discord
import datetime
from discord.ext import commands
from core.data_base_manager import DatabaseManager

IMMUNE_DATA_PATH = "data/politics_immune_channels.json"


class NoPolitics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ban_words = DatabaseManager.load_json("data/banned_politics_words.json", [])

    def _is_immune(self, guild_id: int, channel_id: int) -> bool:
        data = DatabaseManager.load_json(IMMUNE_DATA_PATH, {})
        return channel_id in data.get(str(guild_id), [])

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 基本檢查：忽略機器人自己、忽略私訊
        if message.author.bot or not message.guild:
            return

        # 2. 免疫頻道直接跳過
        if self._is_immune(message.guild.id, message.channel.id):
            return

        # 3. 檢查訊息是否違規
        content = message.content.lower()
        triggered_words = [word for word in self.ban_words if word in content]

        if triggered_words:
            try:
                # 4. 執行禁言 (Timeout) - 10 秒
                # 這裡使用 timedelta 定義時長
                duration = datetime.timedelta(seconds=10)
                await message.author.timeout(duration, reason="政治言論攔截：{message.author} (已禁言10s) 內容: '{message.content}'")

                # 5. 給予警告（標註使用者）
                # 注意：message.channel.send 不支援 ephemeral
                warning_msg = f"⚠️ {message.author.mention} 這裡不是政治台，請不要聊政治，謝謝。"
                await message.channel.send(warning_msg, delete_after=10) # 10秒後自動刪除警告，保持頻道整潔
                
                # 6. 紀錄到後台 Log
                print(f"政治言論攔截：{message.author} (已禁言10s) 內容: '{message.content}'")

                # 3. 刪除訊息
                await message.delete()

            except discord.Forbidden:
                print("❌ 錯誤：機器人權限不足（需要『管理訊息』與『管理成員』權限）。")
            except Exception as e:
                print(f"❌ 發生錯誤: {e}")

    @commands.hybrid_command(name="politics_immune", description="設定或取消這個頻道免受政治言論審查")
    @commands.has_permissions(administrator=True)
    async def politics_immune(self, ctx):
        data = DatabaseManager.load_json(IMMUNE_DATA_PATH, {})
        guild_id_str = str(ctx.guild.id)
        channel_id = ctx.channel.id

        if guild_id_str not in data:
            data[guild_id_str] = []

        if channel_id in data[guild_id_str]:
            data[guild_id_str].remove(channel_id)
            await ctx.reply("🔒 這個頻道已**取消**政治言論免疫，政治審查恢復運作")
        else:
            data[guild_id_str].append(channel_id)
            await ctx.reply("🔓 這個頻道已設為**免疫頻道**，政治言論不會受到審查")

        DatabaseManager.save_json(IMMUNE_DATA_PATH, data)


async def setup(bot):
    await bot.add_cog(NoPolitics(bot))