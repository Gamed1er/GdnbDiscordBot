import discord
import os
import time
from discord.ext import commands
from core.data_base_manager import DatabaseManager
from core.gemini_client import GeminiAI

PERSONALITIES = {
    "default": {
        "name": "友善助手",
        "description": "活潑、幽默、豪邁且不拘小節的友善助手",
        "prompt": (
            "你現在是一個 Discord 伺服器的友善 AI 助手。\n"
            "你的個性：活潑、幽默、豪邁且不拘小節、樂於助人。\n"
        ),
        "rules": (
            "1. 請使用繁體中文回覆，語氣要像在 Discord 聊天一樣自然，可以使用 Emoji。\n"
            "2. 保持簡潔，不要發送長篇大論，除非使用者要求詳細解釋。\n"
            "3. 禁止 Latex，請使用純文字表示。\n"
            "4. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`。\n"
            "5. 使用 markdown 語法回答。\n"
            "6. 如果使用者問你 Minecraft 技術相關的問題（資料包、資源包語法等），請結合使用者提供的一張或多張檔案/圖片內容一起交叉比對分析。\n"
            "7. **回覆格式限制**：\n"
            "請務必嚴格遵守此格式回覆：<給使用者的話>【@U】<關於此使用者需要記住的內容>【@S】<關於整個伺服器需要記住的內容>\n"
            "若無需更新某項記憶，請直接填入原本的內容（不要留空）。"
        ),
    },
    "professional": {
        "name": "專業顧問",
        "description": "嚴謹博學的高知識份子，認真回答問題並確保對方能理解",
        "prompt": (
            "你現在是一個 Discord 伺服器的專業 AI 顧問。\n"
            "你的個性：嚴謹、博學、認真負責、善於深入淺出地解說。\n"
            "你是一位高知識份子。你從不開玩笑，你以認真、客觀的態度對待每一個問題。\n"
            "當有人向你提問，你會根據對方的程度調整說明方式，直到對方能真正理解為止。\n"
            "你的回答邏輯清晰、有條理，必要時會主動補充背景知識或提供延伸說明。\n"
        ),
        "rules": (
            "1. 請使用繁體中文回覆，語氣嚴謹正式，避免使用 Emoji 或俚語。\n"
            "2. 回答要有深度，結構清晰，確保對方能夠理解。\n"
            "3. 禁止 Latex，請使用純文字表示。\n"
            "4. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`。\n"
            "5. 使用 markdown 語法回答，善用標題、條列式等結構化格式。\n"
            "6. 如果使用者問你 Minecraft 技術相關的問題（資料包、資源包語法等），請結合使用者提供的一張或多張檔案/圖片內容一起交叉比對分析。\n"
            "7. **回覆格式限制**：\n"
            "請務必嚴格遵守此格式回覆：<給使用者的話>【@U】<關於此使用者需要記住的內容>【@S】<關於整個伺服器需要記住的內容>\n"
            "若無需更新某項記憶，請直接填入原本的內容（不要留空）。"
        ),
    },
}

class AIChat(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.ai = ai_client
        self.data_path = "data/ai_register_channel.json"
        self.personality_path = "data/ai_personality.json"
        self.memory_dir = "data/ai_memory/"
        os.makedirs(self.memory_dir, exist_ok=True)

    def get_guild_memory(self, guild_id):
        path = f"{self.memory_dir}{guild_id}.json"
        return DatabaseManager.load_json(path, {"server_memory": "", "users": {}, "history": []})

    def save_guild_memory(self, guild_id, data):
        path = f"{self.memory_dir}{guild_id}.json"
        DatabaseManager.save_json(path, data)

    def get_guild_personality(self, guild_id):
        data = DatabaseManager.load_json(self.personality_path, {})
        return data.get(str(guild_id), "default")

    def set_guild_personality(self, guild_id, personality_key):
        data = DatabaseManager.load_json(self.personality_path, {})
        data[str(guild_id)] = personality_key
        DatabaseManager.save_json(self.personality_path, data)

    @commands.command(name="personality")
    @commands.has_permissions(manage_guild=True)
    async def personality(self, ctx, mode: str = None):
        """切換或查看目前伺服器的 AI 人格模式。"""
        guild_id = str(ctx.guild.id)
        current_key = self.get_guild_personality(guild_id)
        current = PERSONALITIES[current_key]

        if mode is None:
            options = "\n".join(
                f"- `{key}`：{p['name']} — {p['description']}"
                for key, p in PERSONALITIES.items()
            )
            await ctx.reply(
                f"**目前人格模式**：{current['name']} (`{current_key}`)\n\n"
                f"**可用人格**：\n{options}\n\n"
                f"使用 `$personality <模式>` 來切換。"
            )
            return

        if mode not in PERSONALITIES:
            keys = "、".join(f"`{k}`" for k in PERSONALITIES)
            await ctx.reply(f"❌ 找不到人格 `{mode}`，可用選項：{keys}")
            return

        if mode == current_key:
            await ctx.reply(f"✅ 目前已經是 **{current['name']}** 模式了。")
            return

        self.set_guild_personality(guild_id, mode)
        new = PERSONALITIES[mode]
        await ctx.reply(f"✅ 已將 AI 人格切換為 **{new['name']}**。\n> {new['description']}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        if message.content.startswith(self.bot.command_prefix) or message.content.startswith("~"): return

        registered = DatabaseManager.load_json(self.data_path, [])
        if message.channel.id not in registered: return

        async with message.channel.typing():
            guild_id = str(message.guild.id)
            user_id = str(message.author.id)
            guild_data = self.get_guild_memory(guild_id)

            personality_key = self.get_guild_personality(guild_id)
            personality = PERSONALITIES[personality_key]

            server_memory = guild_data.get("server_memory", "")
            user_memory = guild_data.get("users", {}).get(user_id, "")
            history = guild_data.get("history", [])

            history_text = ""
            if history:
                lines = []
                for entry in history:
                    lines.append(f"[{entry['name']}]: {entry['content']}")
                    lines.append(f"[Bot]: {entry['reply']}")
                history_text = "\n".join(lines)

            files_to_send = []
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type:
                        try:
                            f_bytes = await attachment.read()
                            files_to_send.append({
                                "bytes": f_bytes,
                                "mime_type": attachment.content_type
                            })
                            print(f"成功加載附件: {attachment.filename} ({attachment.content_type})")
                        except Exception as e:
                            print(f"⚠️ 讀取附件 {attachment.filename} 失敗: {e}")

            SYSTEM_PROMPT = (
                f"{personality['prompt']}"
                f"【伺服器記憶】\n"
                f"{server_memory if server_memory else '目前沒有關於這個伺服器的記憶。'}\n"
                f"【關於目前使用者 {message.author.display_name} 的記憶】\n"
                f"{user_memory if user_memory else '目前沒有關於此使用者的特定記憶。'}\n"
                f"【最近 {len(history)} 條對話紀錄】\n"
                f"{history_text if history_text else '目前沒有對話紀錄。'}\n"
                f"【對話規則】\n"
                f"{personality['rules']}\n"
            )

            notice_text = f"（使用者已隨訊息附帶了 {len(files_to_send)} 個檔案/圖片，請結合所有檔案內容一起辨識分析）\n" if files_to_send else ""
            prompt = (
                f"使用者名稱: {message.author.display_name}\n"
                f"使用者ID: {user_id}\n"
                f"訊息內容: {notice_text}{message.content}"
            )

            response = self.ai.get_response(
                prompt=SYSTEM_PROMPT + prompt,
                files_list=files_to_send if files_to_send else None
            )

            if response and "【@U】" in response and "【@S】" in response:
                parts = response.split("【@U】", 1)
                reply_content = parts[0].strip()
                rest = parts[1].split("【@S】", 1)
                new_user_memory = rest[0].strip()
                new_server_memory = rest[1].strip()

                guild_data["server_memory"] = new_server_memory
                guild_data.setdefault("users", {})[user_id] = new_user_memory

                guild_data.setdefault("history", []).append({
                    "user_id": user_id,
                    "name": message.author.display_name,
                    "content": message.content[:300],
                    "reply": reply_content[:300],
                    "ts": int(time.time())
                })
                guild_data["history"] = guild_data["history"][-10:]

                self.save_guild_memory(guild_id, guild_data)

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
