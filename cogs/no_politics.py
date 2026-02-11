import discord
import json, os, datetime  # 修改：需要 datetime 來設定禁言時間
from discord.ext import commands

import logging
logger = logging.getLogger(__name__)

class NoPolitics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 使用 encoding="utf-8" 避免樹莓派讀取中文 json 出現亂碼
        with open("data/banned_politics_word.json", "r", encoding="utf-8") as json_file:
            self.ban_words = json.load(json_file)

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 基本檢查：忽略機器人自己、忽略私訊
        if message.author.bot or not message.guild:
            return

        # 2. 檢查訊息是否違規
        content = message.content.lower()
        triggered_words = [word for word in self.ban_words if word in content]

        if triggered_words:
            try:
                # 3. 刪除訊息
                await message.delete()
                
                # 4. 執行禁言 (Timeout) - 10 秒
                # 這裡使用 timedelta 定義時長
                duration = datetime.timedelta(seconds=10)
                await message.author.timeout(duration, reason="政治言論攔截：{message.author} (已禁言10s) 內容: '{message.content}'")

                # 5. 給予警告（標註使用者）
                # 注意：message.channel.send 不支援 ephemeral
                warning_msg = f"⚠️ {message.author.mention} 這裡不是政治台，請不要聊政治，謝謝。"
                await message.channel.send(warning_msg, delete_after=10) # 10秒後自動刪除警告，保持頻道整潔
                
                # 6. 紀錄到後台 Log
                logger.info(f"政治言論攔截：{message.author} (已禁言10s) 內容: '{message.content}'")

            except discord.Forbidden:
                logger.error("❌ 錯誤：機器人權限不足（需要『管理訊息』與『管理成員』權限）。")
            except Exception as e:
                logger.error(f"❌ 發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(NoPolitics(bot))