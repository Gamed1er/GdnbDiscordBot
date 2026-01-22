import discord
import json
import os
from discord.ext import commands
from core.gemini_client import GeminiAI
from core.data_base_manager import DatabaseManager

class AIChat(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.ai = ai_client
        self.data_path = "data/ai_register_channel.json"

    @commands.Cog.listener()
    async def on_message(self, message):

        # 不要回應自己發的訊息
        if message.author == self.bot.user: return
        
        # 忽略指令
        if message.content.startswith(self.bot.command_prefix): return
        if message.content.startswith("~"): return

        # 忽略未登記的頻道
        registered = DatabaseManager.load_json(self.data_path, [])
        if message.channel.id not in registered: return
        
        async with message.channel.typing():
            SYSTEM_PROMPT = """
            你現在是一個 Discord 伺服器的友善 AI 助手。
            你的個性：活潑、幽默、豪邁且不拘小節、樂於助人。
            你可能需要知道的人 (除非被問到或需要提到，否則不用主動提及) :
            1. 遊戲亡，@gdnb，Discord ID 是 683177859300196383，維護和編寫 Discord Bot 的人。他是一個 Minecraft 地圖開發者，正在深入研究關於資工方面的東西。中央大學資工系
            2. 收音機，一個 Youtuber，專門教學 Minecraft 指令，你可以透過 Youtube 查詢到他的頻道。中央大學數學系
            3. 村村，一個 Youtuber，也是教學 Minecraft 指令，收音機是他的師父。目前就讀高中
            對話規則：
            1. 請使用繁體中文回覆，除非使用者有要求用其他語言，語氣要像在 Discord 聊天一樣自然，可以使用 Emoji。
            2. 保持簡潔，不要發送長篇大論，除非使用者要求詳細解釋。
            3. 避免在每句話都重複自我介紹。
            4. 禁止 Latex，因為那個字體在 Discord 無法顯示，請使用純文字表示。
            5. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`，例如：如果使用者ID是 12345，你想打招呼，請寫 '你好啊 <@12345>！'
            6. 使用 markdown 語法回答，Discord 支援 markdown 語法
            7. 如果使用者有問你 Minecraft 技術相關的問題，例如資料包、資源包等，請去查詢當前 Minecraft 最新版本的語法再來通知
            """

            # 在發送請求時
            prompt = (
                f"使用者名稱: {message.author.display_name}\n"
                f"使用者ID: {message.author.id}\n"
                f"訊息內容: {message.content}"
            )
            response = self.ai.get_response(SYSTEM_PROMPT + prompt)
            
            if response and response.strip():
                if len(response) > 2000:
                    response = response[::1900] + "(內容長度已超過 Discord 訊息長度限制，已省略)"
                await message.reply(response)
            else:
                await message.reply("( 錯誤 : 機器人未給予回覆，可能是 Gemini 那邊的問題，請在嘗試一次 )")


# 這個函數是讓 main.py 載入這個模組的關鍵
async def setup(bot):
    # 這裡可以從環境變數讀取 API Key 傳進去
    import os
    ai_client = GeminiAI(os.getenv("GEMINI_API_KEY"))
    await bot.add_cog(AIChat(bot, ai_client))