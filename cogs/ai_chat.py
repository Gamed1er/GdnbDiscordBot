import discord
import os
from discord.ext import commands
from core.gemini_client import GeminiAI
from core.data_base_manager import DatabaseManager

class AIChat(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.ai = ai_client
        self.data_path = "data/ai_register_channel.json"
        self.memory_dir = "data/ai_memory/"
        os.makedirs(self.memory_dir, exist_ok=True) # 確保記憶資料夾存在

    def get_user_memory(self, user_id):
        """取得特定使用者的記憶內容"""
        path = f"{self.memory_dir}{user_id}.json"
        # 如果檔案不存在，回傳空字串
        data = DatabaseManager.load_json(path, {"memory": ""})
        return data.get("memory", "")

    def save_user_memory(self, user_id, memory_text):
        """儲存使用者的記憶內容"""
        path = f"{self.memory_dir}{user_id}.json"
        DatabaseManager.save_json(path, {"memory": memory_text})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        if message.content.startswith(self.bot.command_prefix) or message.content.startswith("~"): return

        # 檢查頻道是否登記 (這裡假設 ai_register_channel.json 存的是一個 list)
        registered = DatabaseManager.load_json(self.data_path, [])
        if message.channel.id not in registered: return
        
        async with message.channel.typing():
            # 1. 讀取該使用者的舊記憶
            user_id = str(message.author.id)
            old_memory = self.get_user_memory(user_id)
            
            # 2. 注入記憶到 Prompt

            SYSTEM_PROMPT = f"""
            你現在是一個 Discord 伺服器的友善 AI 助手。
            你的個性：活潑、幽默、豪邁且不拘小節、樂於助人。
            【目前的記憶】
            關於這位使用者 {message.author.display_name}，你目前的記憶如下：
            {old_memory if old_memory else "目前沒有關於這位使用者的特定記憶。"}
            對話規則：
            1. 請使用繁體中文回覆，除非使用者有要求用其他語言，語氣要像在 Discord 聊天一樣自然，可以使用 Emoji。
            2. 保持簡潔，不要發送長篇大論，除非使用者要求詳細解釋。
            3. 避免在每句話都重複自我介紹。
            4. 禁止 Latex，因為那個字體在 Discord 無法顯示，請使用純文字表示。
            5. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`，例如：如果使用者ID是 12345，你想打招呼，請寫 '你好啊 <@12345>！'
            6. 使用 markdown 語法回答，Discord 支援 markdown 語法
            7. 如果使用者有問你 Minecraft 技術相關的問題，例如資料包、資源包等，請去查詢當前 Minecraft 最新版本的語法再來通知
            8. **回覆格式限制**：
               請務必嚴格遵守此格式回覆：<給使用者的話>【@】<需要記住的內容>。
               - 前段會直接回覆給使用者。
               - 後段是你要留給未來的自己看的筆記（不超過 300 字），請簡述這次對話中值得記住的重點（如對方的喜好、剛聊過的話題），也可以在原有的記憶上做延伸。
            """

            prompt = (
                f"使用者名稱: {message.author.display_name}\n"
                f"使用者ID: {user_id}\n"
                f"訊息內容: {message.content}"
            )
            
            response = self.ai.get_response(SYSTEM_PROMPT + prompt)
            
            if response and "【@】" in response:
                # 3. 解析回覆：拆分「對話」與「記憶」
                parts = response.split("【@】", 1)
                reply_content = parts[0].strip()
                new_memory = parts[1].strip()

                # 4. 儲存新記憶
                self.save_user_memory(user_id, new_memory)

                # 5. 發送回覆（處理長度限制）
                if len(reply_content) > 2000:
                    reply_content = reply_content[:1900] + "..." # 修正截斷邏輯
                await message.reply(reply_content)
                
            elif response:
                # 如果 AI 沒按格式回覆，直接整段發出以免漏掉訊息
                await message.reply(response[:2000])
            else:
                await message.reply("⚠️ AI 目前無法回應。")

async def setup(bot):
    import os
    ai_client = GeminiAI(os.getenv(f"GEMINI_API_KEY").split(","))
    await bot.add_cog(AIChat(bot, ai_client))