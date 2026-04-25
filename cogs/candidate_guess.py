import re
import time

import discord
from discord.ext import commands
from discord.ext import tasks
from core.data_base_manager import DatabaseManager
from core.gemini_client import GeminiAI
from core.level_manager import LevelManager

class CandidateGuess(commands.Cog):

    import discord
from discord.ext import commands
from core.data_base_manager import DatabaseManager
import random
import json
import datetime

class CandidateGuess(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.pool_path = "data/guess_candidate/candidate_pool.json"
        self.channel_path = "data/guess_candidate/candidate_channel.json"
        self.daily_quiz_path = "data/guess_candidate/daily_quiz.json"
        self.data_dir = "data/level_system/"
        # 假設你的 ai 工具在 self.bot.ai 或你傳入的方式，這裡參考你 ai_chat 的寫法
        # 如果 self.ai 是在別的地方定義的，請確保它能被呼叫
        self.ai = ai_client 
        
    @commands.command(name="candidate_channel_register")
    @commands.has_permissions(administrator=True)
    async def announcement_channel_register(self, ctx):
        guild_id_str = str(ctx.guild.id)
        path = self.channel_path
        # 讀取為 dict，預設空 dict
        data = DatabaseManager.load_json(path, {})

        if guild_id_str in data and data[guild_id_str] == ctx.channel.id:
            del data[guild_id_str]
            await ctx.reply("🔇 這個機器人**不會**在這個頻道玩猜人物遊戲")
        else:
            data[guild_id_str] = ctx.channel.id
            await ctx.reply(f"🔊 猜謎頻道設定成功：{ctx.channel.mention}")

        DatabaseManager.save_json(path, data)


    # --- 隨機選題與 API 調用邏輯 ---
    async def generate_daily_quiz(self):
        # 1. 讀取母庫
        pool_data = DatabaseManager.load_json(self.pool_path, {})
        if not pool_data:
            return None

        # 2. 隨機選取一個類別與角色
        category_key = random.choice(list(pool_data.keys()))
        category_info = pool_data[category_key]
        ans_name = random.choice(category_info['pool'])
        area_name = category_info['name']

        # 3. 準備給 Gemini 的 Prompt
        SYSTEM_PROMPT = """
        你現在是一個 Discord 伺服器的專業的 Discord 猜謎遊戲出題者。
        請針對指定的人物或對象生成 JSON 格式的題目資料。
        
        【出題規則】
        1. 產出 3 個提示 (hint)。
        2. 第 1 句提示必須說一些這個人做過的事情或事蹟，例如 希特勒 可以說 「他曾經參與二次世界大戰」
           第 2 個和第 3 個提示可以說該人物的個性，或著可以說該人物做的「特別的事」，例如 徐志摩 可以說 「他墜機了」
           提示可以具有「誤導性」：利用該人物與其他知名人物重疊的真實特質來誘導玩家往錯誤方向猜測。
           提示詞可以帶有一點幽默感
        3. 提示詞是陳述句，但是盡量簡短，不超過 20 字。例如 孔子 的提示詞可能有「他力氣非常大，可以徒手舉起城門」
        4. maybe_ans 應包含所有可能的正確稱呼（如別名、縮寫、正式名稱），如果是外國人，附上英文或其他慣用語言名稱的全名或縮寫 ( 例如 林納斯·托瓦茲 可以猜 linus torvalds 或 linux，竈門炭治郎 可以猜 かまどたんじろう )。
        
        【輸出格式限制】
        請務必嚴格遵守以下格式回覆，不要包含任何開場白、結尾或 Markdown 標記以及其他語句，回覆內容必須是純 Json 檔案，格式如下：
        {
          "area": "領域名稱",
          "hint": ["提示1", "提示2", "提示3"],
          "ans": "標準答案",
          "maybe_ans": ["別名1", "別名2"]
        }

        【今日的題目與類別】
        """
        
        user_prompt = f"請針對「{ans_name}」這個人物出題，領域類別為「{area_name}」。"

        # print(user_prompt)
        
        # 4. 呼叫 API
        raw_response = self.ai.get_response(SYSTEM_PROMPT + user_prompt)

        # print(raw_response)
        
        try:
            # 使用正規表達式抓取 ```json ... ``` 之間的內容，或直接抓取 { ... }
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                quiz_data = json.loads(clean_json)

                # 嘗試解析 JSON
                quiz_data = json.loads(raw_response)
                quiz_data["date"] = str(datetime.date.today())
                
                # 取得昨天的答案 (如果有)
                old_quiz = DatabaseManager.load_json(self.daily_quiz_path, {})
                quiz_data["yesterday_ans"] = old_quiz.get("ans", "無")
                
                # 儲存今日題目
                DatabaseManager.save_json(self.daily_quiz_path, quiz_data)
                return quiz_data
            
            else:
                print(f"找不到 JSON 結構，原始回覆: {raw_response}")

        except Exception as e:
            print(f"解析 AI 回覆失敗: {e}")
            return None
        
    def cog_load(self):
        self.daily_check.start()

    def cog_unload(self):
        self.daily_check.cancel()

    @tasks.loop(minutes=30) # 每 30 分鐘檢查一次
    async def daily_check(self):
        now = datetime.datetime.now()
        # 檢查是否為早上 6 點
        if now.hour == 6:
            quiz_data = DatabaseManager.load_json(self.daily_quiz_path, {})
            # 避免同一天重複發送
            if quiz_data.get("date") != str(now.date()):
                new_quiz = await self.generate_daily_quiz()
                if new_quiz:
                    await self.broadcast_quiz(new_quiz)

    async def broadcast_quiz(self, quiz):
        # 讀取所有註冊過的頻道
        channels_data = DatabaseManager.load_json(self.channel_path, {})
        
        embed = discord.Embed(
            title=f"🧩 每日猜謎：這是誰？",
            description=f"**範疇：{quiz['area']}**\n昨天答案是：`{quiz['yesterday_ans']}`",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="🔸 提示 1", value=quiz['hint'][0], inline=False)
        embed.add_field(name="🔸 提示 2", value=quiz['hint'][1], inline=False)
        embed.add_field(name="🔸 提示 3", value=quiz['hint'][2], inline=False)
        embed.set_footer(text="直接在頻道輸入答案即可！")

        # 對所有登記的頻道發送訊息
        for guild_id, channel_id in channels_data.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)


    @commands.command(name="test_quiz")
    @commands.has_permissions(administrator=True)
    async def test_quiz(self, ctx):  # 必須加上 ctx
        # 你可以在這裡呼叫你寫好的生成邏輯來測試
        quiz_data = await self.generate_daily_quiz()
        if quiz_data:
            await self.broadcast_quiz(quiz_data)
            await ctx.send("✅ 測試題目已發送！")
        else:
            await ctx.send("❌ 題目生成失敗，請檢查 Log。")

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 過濾掉機器人自己、以及沒有伺服器的私訊
        if message.author.bot or not message.guild:
            return

        # 2. 檢查該頻道是否為登記的「猜謎頻道」
        guild_id_str = str(message.guild.id)
        channels_data = DatabaseManager.load_json(self.channel_path, {})
        
        # 如果該伺服器沒登記頻道，或是發言頻道不對，直接結束
        if guild_id_str not in channels_data or channels_data[guild_id_str] != message.channel.id:
            return

        # 3. 讀取今日題目資料
        quiz_data = DatabaseManager.load_json(self.daily_quiz_path, {})
        if not quiz_data:
            return
            
        # 檢查題目是否為今天生成的 (防止舊題目干擾)
        if quiz_data.get("date") != str(datetime.date.today()):
            return

        # 4. 比對答案
        # 處理使用者輸入：去空白、轉小寫
        user_input = message.content.strip().lower()
        
        # 準備正確答案清單
        standard_ans = quiz_data["ans"].lower()
        possible_answers = [standard_ans] + [a.lower() for a in quiz_data.get("maybe_ans", [])]

        if user_input in possible_answers:
            # --- 答對了 ---
            # 1. 讀取並更新答對名單
            # 確保 quiz_data 裡有 winners 這個 key
            if "winners" not in quiz_data:
                quiz_data["winners"] = []
            
            user_id = message.author.id
            
            # 檢查這位使用者今天是否已經答對過 (避免重複刷榜)
            if user_id not in quiz_data["winners"]:
                quiz_data["winners"].append(user_id)
                # 存回 JSON 檔案
                DatabaseManager.save_json(self.daily_quiz_path, quiz_data)
            else:
                return
            
            # 獲取他是第幾個答對的
            rank = quiz_data["winners"].index(user_id) + 1

            # 2. 執行刪除與回覆
            try:
                await message.delete()
            except discord.Forbidden:
                pass 

            # 使用簡單的文字回覆搭配 Markdown 語法
            reply_text = (
                f"## 🎊 恭喜 {message.author.mention} 答對今天的人物猜謎！\n"
                f"你是第 `{rank}` 位猜對的人。"
            )

            await message.channel.send(reply_text)
            
            # 3. 給予經驗值
            level_data = DatabaseManager.load_json(self.data_dir + str(message.guild.id) + ".json")
            user_id = str(message.author.id)
            user = level_data.get(user_id, LevelManager.BLANK_LEVEL_DATA)
            xp_gain = 50
            current_time = time.time()

            d_level = LevelManager.check_level_up(user["xp"], xp_gain)
            if d_level > 0 and user["announcement"]:
                with open("data/announcement_register_channel.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                for channel_id in data[str(message.guild.id)]:
                    channel = self.bot.get_channel(channel_id)
                    if channel is None:
                        try:
                            channel = await self.fetch_channel(channel_id)
                        except:
                            continue
                    
                    if channel:
                        await channel.send(f"恭喜 {message.author.mention} 已提升至等級 {user['level'] + d_level}")

            user["xp"] = round(user["xp"] + xp_gain, 2)
            user["last_talk_time"] = current_time
            user["last_word"] = message.content[:25]
            user["level"] = LevelManager.xp_to_level(user["xp"])

                    # 8. 儲存
            level_data[user_id] = user
            DatabaseManager.save_json(f"{self.data_dir}{message.guild.id}.json", level_data)
                
        else:
            # --- 答錯了 ---
            # 為了避免一般聊天也被加 X，我們設定一個門檻：
            # 只有當字數小於 10 個字，且該頻道是「猜謎頻道」時才反應
            if len(message.content) <= 10:
                # 這裡不需要加 await，因為加反應失敗不應該影響主程式
                try:
                    await message.add_reaction("❌")
                except:
                    pass


# 這行是關鍵，main.py 載入時會執行它
async def setup(bot):
    import os
    ai_client = GeminiAI(os.getenv(f"GEMINI_API_KEY").split(","))
    await bot.add_cog(CandidateGuess(bot, ai_client))