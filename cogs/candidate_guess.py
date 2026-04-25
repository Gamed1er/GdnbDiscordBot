import discord
from discord.ext import commands
from discord.ext import tasks
from core.data_base_manager import DatabaseManager
from core.gemini_client import GeminiAI

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
    @commands.command(name="test_quiz")
    @commands.has_permissions(administrator=True)
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
        SYSTEM_PROMPT = f"""
        你是一個專業的 Discord 猜謎遊戲出題者。
        請針對指定的人物或對象生成 JSON 格式的題目資料。
        
        【出題規則】
        1. 產出 3 個提示 (hint)。
        2. 第 2 個和第 3 個提示可以具有「誤導性」：利用該人物與其他知名人物重疊的真實特質來誘導玩家往錯誤方向猜測。
        3. 提示必須簡短，每句不超過 15 個字。
        4. maybe_ans 應包含所有可能的正確稱呼（如別名、縮寫、正式名稱）。
        5. 如果該人物有別名 ( 例如 孔子 的別名是 孔丘 或 孔仲尼 )，請寫在 maybe_ans 中，否則 maybe_ans 保持空陣列 []
        
        【輸出格式限制】
        請務必僅回覆純 JSON 代碼塊，不要包含任何開場白、結尾或 Markdown 標記，格式如下：
        {{
          "area": "領域名稱",
          "hint": ["提示1", "提示2", "提示3"],
          "ans": "標準答案",
          "maybe_ans": ["別名1", "別名2"]
        }}
        """
        
        user_prompt = f"請針對「{ans_name}」這個角色出題，領域類別為「{area_name}」。"
        
        # 4. 呼叫 API
        raw_response = self.ai.get_response(SYSTEM_PROMPT + user_prompt)
        
        try:
            # 嘗試解析 JSON
            quiz_data = json.loads(raw_response)
            quiz_data["date"] = str(datetime.date.today())
            
            # 取得昨天的答案 (如果有)
            old_quiz = DatabaseManager.load_json(self.daily_quiz_path, {})
            quiz_data["yesterday_ans"] = old_quiz.get("ans", "無")
            
            # 儲存今日題目
            DatabaseManager.save_json(self.daily_quiz_path, quiz_data)
            return quiz_data
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


# 這行是關鍵，main.py 載入時會執行它
async def setup(bot):
    import os
    ai_client = GeminiAI(os.getenv(f"GEMINI_API_KEY").split(","))
    await bot.add_cog(CandidateGuess(bot, ai_client))