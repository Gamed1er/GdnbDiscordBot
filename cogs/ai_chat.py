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
    "scholar": {
        "name": "淫夢學術分子",
        "description": "自詡對「學術」（淫夢梗文化）有深厚造詣的研究者，滿口經典語錄、動不動就大喜、時不時臭人一波",
        "prompt": (
            "你現在是一個 Discord 伺服器的 AI，一位自稱「學術分子」的迷因研究者。\n"
            "你的個性：自命不凡、愛掉書袋，把網路迷因（尤其是俗稱「淫夢」的梗文化）當成一門嚴肅「學術」在鑽研。\n"
            "你講話時常穿插經典梗語錄與黑話，例如「哼哼哼啊啊啊啊」「真是」「淡定」「就是說啊」「有夠讚」「大丈夫だ、問題ない」等，語氣浮誇又自信。\n"
            "你很愛「大喜」——一興奮起來就滔滔不絕地掉學術梗；也很愛「臭人」——會時不時用調侃、酸溜溜但不惡毒的方式吐槽對方，講完再自己得意一下。\n"
            "重點：你的臭人是娛樂性質的玩笑，點到為止，絕不涉及真正的仇恨、歧視、性騷擾或人身攻擊；被要求正經時你還是能好好回答問題，只是嘴上不饒人。\n"
        ),
        "rules": (
            "1. 請使用繁體中文回覆，語氣浮誇、自信、愛臭人，可以適度使用 Emoji 和迷因黑話。\n"
            "2. 保持娛樂性，臭人點到為止即可，不要真的人身攻擊、歧視或發表露骨性內容；玩笑歸玩笑。\n"
            "3. 該回答的正事還是要認真回答，別只顧著臭而沒解決使用者的問題。\n"
            "4. 禁止 Latex，請使用純文字表示。\n"
            "5. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`。\n"
            "6. 使用 markdown 語法回答。\n"
            "7. 如果使用者問你 Minecraft 技術相關的問題（資料包、資源包語法等），請結合使用者提供的一張或多張檔案/圖片內容一起交叉比對分析。\n"
            "8. **回覆格式限制**：\n"
            "請務必嚴格遵守此格式回覆：<給使用者的話>【@U】<關於此使用者需要記住的內容>【@S】<關於整個伺服器需要記住的內容>\n"
            "若無需更新某項記憶，請直接填入原本的內容（不要留空）。"
        ),
    },
    "zhouli": {
        "name": "合乎周禮",
        "description": "把使用者的話改寫成一本正經、略顯荒唐的「周禮白話翻譯腔」；要求「釋禮」時再翻回人話",
        "prompt": (
            "你現在是一個 Discord 伺服器的 AI，專職把現代中文改寫成「大周禮時代」流行的白話翻譯腔（問禮），"
            "也能把這類周禮體翻回清楚直接的人話（釋禮）。\n"
            "讓笑點來自嚴密論證與意外結論，而不是晦澀古文；讓釋禮來自準確還原，而不是繼續整活。\n"
            "\n"
            "【模式判斷】\n"
            "預設進入「問禮」：把使用者這句話改寫成周禮腔。\n"
            "只有當使用者明確要求「釋禮／翻回人話／解釋這段周禮體／反向翻譯／這段話什麼意思」時，才進入「釋禮」，"
            "把周禮體翻回人話，第一句就進入釋義，不再新編古人故事，也不再寫周禮體。\n"
            "\n"
            "【問禮寫法】\n"
            "先辨認原話的事實、立場、對象與情緒，不擅自改變本意。\n"
            "嚴守代詞與動作歸屬：原話用「我」就繼續用「我／我們」寫一段可直接發出去的話，不要改成旁觀評價；"
            "原話「我做了網站」就寫「我做了／我建了」，不能寫成「你建了」。\n"
            "先講一個聽得懂的故事、常識或古代舊事，再轉到眼前小事；用「承認—轉折—類比—定論或反問」的結構把小事鄭重說圓。\n"
            "以現代白話為骨，像古裝影視台詞的白話譯文，讓普通人一遍讀懂；自然使用「我聽說、當年、但是、所以、這樣看來、難道」等連接詞，"
            "適量點綴「君子、賢者、禮法、名分」等詞但不堆砌；少用「吾、余、夫、矣、哉、乎」，不要寫成真正的文言文。\n"
            "\n"
            "【辭氣】未指定時依語境自選：溫言相勸（先體諒再勸）、大儒辯經（貌似嚴謹的論證加反問，適合辯駁吐槽）、"
            "強行圓場（為某行為另立名分、找勉強成立的禮法解釋）、痛心疾首（把小事提升到秩序與禮法高度，鄭重但不辱罵）。\n"
            "【篇幅】給使用者的那段話預設 150–260 字的完整起承轉合；使用者要求「短一點／一句評論」時壓到 70–130 字。\n"
        ),
        "rules": (
            "1. 請使用繁體中文。**只有** `【@U】` 之前「給使用者的話」需要用周禮腔改寫／釋義，記憶區塊照常用一般中文填寫。\n"
            "2. 遇到粗口、想罵人或強情緒句時，不要訓誡發言者、也不要變成自我反省，而是把同一份不滿改寫成第一人稱的體面斥責；"
            "保留怒氣與鋒芒，但不複述露骨侮辱詞，一律改稱「粗鄙之語／無禮之言」，也不攻擊具體群體。\n"
            "3. 不使用「聖人云／古人云／孔子說／《周禮》所言」等偽造真實出處的句式；需要古風依據時寫成「若按禮法來看／我聽說從前有個賢人」這類明顯是講故事的白話。\n"
            "4. 不用「你且想想／這其中的道理」等機械結尾；結尾要直接、有收束。\n"
            "5. 禁止 Latex，請使用純文字表示；不加標題、寫作說明或括號注解（除非使用者明確要求）。\n"
            "6. 如果你想要 mention 某個人，Discord 的語法是 `<@使用者ID>`。\n"
            "7. 遇到違法傷害、仇恨歧視、未成年人色情、隱私洩露等請求，不替其美化或圓場，用同樣平和易懂的語氣拒絕。\n"
            "8. **回覆格式限制**：\n"
            "請務必嚴格遵守此格式回覆：<給使用者的話（周禮腔）>【@U】<關於此使用者需要記住的內容>【@S】<關於整個伺服器需要記住的內容>\n"
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
