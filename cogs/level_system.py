import discord
import json, os, math, time
from discord.ext import commands

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/level_system"
        os.makedirs(self.data_dir, exist_ok=True)
        # 建議進階做法：這裡可以用一個字典緩存資料，不要每次都讀寫檔案

    def get_path(self, guild_id):
        return f"{self.data_dir}/{guild_id}.json"

    def get_level_data(self, guild_id):
        path = self.get_path(guild_id)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_level_data(self, guild_id, data):
        with open(self.get_path(guild_id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def level_to_xp(x):
        return 18 * x * x - 21 * x + 4  # 18x^2 - 21x + 4
    
    def xp_to_level(y):
        if y <= 0: return 0
        return int((21 + math.sqrt(153 + 72 * y)) / 36)


    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 基本過濾
        if message.author.bot or not message.guild or message.content.startswith("$"):
            return

        level_data = self.get_level_data(message.guild.id)
        user_id = str(message.author.id)

        # 2. 取得舊資料或初始化
        user = level_data.get(user_id, {"xp": 0, "last_talk_time": 0, "last_word": ""})
        current_time = time.time()

        # 3. 檢查重複與冷卻
        if current_time - user["last_talk_time"] < 3:
            return
        if message.content == user["last_word"] and message.content != "":
            return

        # 4. 計算 XP 邏輯
        # 你的需求：sqrt(len/4)，上限 20
        # 實作：先算 sqrt(字數/4)，用 min 限制它不能超過 20
        content_xp = math.sqrt(len(message.content) / 4)
        xp_gain = min(content_xp, 20) 

        # 5. 檢查附加檔案 (圖片、影片等)
        if message.attachments:
            xp_gain += 8

        # 6. 更新資料
        user["xp"] = round(user["xp"] + xp_gain, 2)
        user["last_talk_time"] = current_time
        user["last_word"] = message.content

        # 7. 檢查等級 (可選：要在這裡檢查是否該給予身分組)
        # self.check_level_up(message, user["xp"])

        # 8. 儲存
        level_data[user_id] = user
        self.save_level_data(message.guild.id, level_data)

    @commands.command(name="xp")
    async def asking_xp(self, ctx, target: discord.Member = None):
        target = target or ctx.author # 如果沒指定 target，就是自己
        
        level_data = self.get_level_data(ctx.guild.id)
        user_data = level_data.get(str(target.id), {"xp": 0})

        await ctx.send(f"📊 **{target.display_name}** 的經驗值為：`{int(user_data['xp'])}` XP")

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))