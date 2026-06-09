import discord
import os
from discord.ext import commands
from core.data_base_manager import DatabaseManager
from core.gemini_client import GeminiAI

class AIChat(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.ai = ai_client
        self.data_path = "data/ai_register_channel.json"
        self.memory_dir = "data/ai_memory/"
        os.makedirs(self.memory_dir, exist_ok=True)

    def get_user_memory(self, user_id):
        path = f"{self.memory_dir}{user_id}.json"
        data = DatabaseManager.load_json(path, {"memory": ""})
        return data.get("memory", "")

    def save_user_memory(self, user_id, memory_text):
        path = f"{self.memory_dir}{user_id}.json"
        DatabaseManager.save_json(path, {"memory": memory_text})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        if message.content.startswith(self.bot.command_prefix) or message.content.startswith("~"): return

        # 檢查頻道是否登記
        registered = DatabaseManager.load_json(self.data_path, [])
        if message.channel.id not in registered: return
        
        async with message.channel.typing():
            user_id = str(message.author.id)
            old_memory = self.get_user_memory(user_id)
            
            # 建立一個清單來儲存所有要發送給 Gemini 的檔案資訊
            files_to_send = []
            
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type:
                        try:
                            # 異步讀取每一個檔案的二進位資料
                            f_bytes = await attachment.read()
                            files_to_send.append({
                                "bytes": f_bytes,
                                "mime_type": attachment.content_type
                            })
                            print(f"成功加載附件: {attachment.filename} ({attachment.content_type})")
                        except Exception as e:
                            print(f"⚠️ 讀取附件 {attachment.filename} 失敗: {e}")

            # 3. 注入記憶到 Prompt
            SYSTEM_PROMPT = f"""
                你現在是一個 Discord 伺服器的友善 AI 助手。
                你的個性：活潑、幽默、豪邁且不拘小節、樂於助人。
                【目前的記憶】
                關於這位使用者 {message.author.display_name}，你目前的記憶如下：
                {old_memory if old_memory else "目前沒有關於核心使用者的特定記憶。"}
                【對話規則】
                1. 請使用繁體中文回覆，語氣要像在 Discord 聊天一樣自然，可以使用 Emoji。
                2. 保持簡潔，不要發送長篇大論，除非使用者要求詳細解釋。
                3. 禁止 Latex，請使用純文字表示。
                4. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`。
                5. 使用 markdown 語法回答。
                6. 如果使用者問你 Minecraft 技術相關的問題（資料包、資源包語法等），請結合使用者提供的一張或多張檔案/圖片內容一起交叉比對分析。
                7. **回覆格式限制**：
                請務必嚴格遵守此格式回覆：<給使用者的話>【@】<需要記住的內容>。
            """

            # 提示文字更新
            notice_text = f"（使用者已隨訊息附帶了 {len(files_to_send)} 個檔案/圖片，請結合所有檔案內容一起辨識分析）\n" if files_to_send else ""
            prompt = (
                f"使用者名稱: {message.author.display_name}\n"
                f"使用者ID: {user_id}\n"
                f"訊息內容: {notice_text}{message.content}"
            )
            
            # 呼叫 Gemini（傳入包含多檔案的清單）
            response = self.ai.get_response(
                prompt=SYSTEM_PROMPT + prompt, 
                files_list=files_to_send if files_to_send else None
            )
            
            if response and "【@】" in response:
                parts = response.split("【@】", 1)
                reply_content = parts[0].strip()
                new_memory = parts[1].strip()

                self.save_user_memory(user_id, new_memory)

                if len(reply_content) > 2000:
                    reply_content = reply_content[:1900] + "..."
                await message.reply(reply_content)
                
            elif response:
                await message.reply(response[:2000])
            else:
                await message.reply("⚠️ AI 目前無法回應。")

async def setup(bot):
    import os
    keys_str = os.getenv("GEMINI_API_KEY")
    api_keys = keys_str.split(",") if keys_str else []
    ai_client = GeminiAI(api_keys)
    await bot.add_cog(AIChat(bot, ai_client))