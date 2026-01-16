import discord
import json
import os
from discord.ext import commands
from core.gemini_client import GeminiAI

class AIChat(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.ai = ai_client
        self.data_path = "data/ai_register_channel.json"

        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.data_path):
            with open(self.data_path, "w") as f:
                json.dump([], f) # 初始化為空列表

    def get_registered_channels(self):
        with open(self.data_path, "r") as f:
            return json.load(f)

    def save_channels(self, channels):
        with open(self.data_path, "w") as f:
            json.dump(channels, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):

        # 不要回應自己發的訊息
        if message.author == self.bot.user: return
        
        # 忽略指令
        if message.content.startswith(self.bot.command_prefix): return
        if message.content.startswith("~"): return

        # 忽略未登記的頻道
        registered = self.get_registered_channels()
        if message.channel.id not in registered: return
        
        async with message.channel.typing():
            response = self.ai.get_response(f"你現在在一個 Discord 裡面，這個伺服器的開發者 @gdnb 將你使用 API 套用進這個 Discord 機器人上。接下來有一位使用者說話，請給予回覆 : 使用者 {message.author} 說 {message.content}")
            
            if response and response.strip():
                if len(response) > 2000:
                    response = response[1900::] + "(內容長度已超過 Discord 訊息長度限制，已省略)"
                await message.reply(response)
            else:
                await message.reply("( 錯誤 : 機器人未給予回覆，可能是 Gemini 那邊的問題，請在嘗試一次 )")

    


# 這個函數是讓 main.py 載入這個模組的關鍵
async def setup(bot):
    # 這裡可以從環境變數讀取 API Key 傳進去
    import os
    ai_client = GeminiAI(os.getenv("GEMINI_API_KEY"))
    await bot.add_cog(AIChat(bot, ai_client))