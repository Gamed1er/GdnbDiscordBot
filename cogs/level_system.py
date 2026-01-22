import discord
import json, os, math, time
from discord.ext import commands
from core.level_manager import LevelManager
from core.data_base_manager import DatabaseManager

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/level_system/"
        os.makedirs(self.data_dir, exist_ok=True)
        # 建議進階做法：這裡可以用一個字典緩存資料，不要每次都讀寫檔案

    def get_path(self, guild_id):
        return f"{self.data_dir}/{guild_id}.json"

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 基本過濾
        if message.author.bot or not message.guild or message.content.startswith("$"):
            return

        level_data = DatabaseManager.load_json(self.data_dir + str(message.guild.id) + ".json")
        user_id = str(message.author.id)

        # 2. 取得舊資料或初始化
        user = level_data.get(user_id, LevelManager.BLANK_LEVEL_DATA)
        current_time = time.time()

        # 3. 檢查重複與冷卻
        if current_time - user["last_talk_time"] < 3:
            return
        if message.content[:25] == user["last_word"] and message.content != "":
            return

        # 4. 計算 XP 邏輯
        # 你的需求：sqrt(len/4)，上限 20
        # 實作：先算 sqrt(字數/4)，用 min 限制它不能超過 20
        content_xp = math.sqrt(len(message.content) / 4)
        xp_gain = min(content_xp, 20) 

        # 5. 檢查附加檔案 (圖片、影片等)
        if message.attachments:
            xp_gain += 8

        # 6. 檢查等級 (可選：要在這裡檢查是否該給予身分組)
        d_level = LevelManager.check_level_up(user["xp"], xp_gain)
        if d_level > 0:
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

        # 7. 更新資料
        user["xp"] = round(user["xp"] + xp_gain, 2)
        user["last_talk_time"] = current_time
        user["last_word"] = message.content[:25]
        user["level"] = LevelManager.xp_to_level(user["xp"])
        
        # 8. 儲存
        level_data[user_id] = user
        DatabaseManager.save_json(f"{self.data_dir}{message.guild.id}.json", level_data)

    @commands.command(name="xp")
    async def asking_xp(self, ctx, target: discord.Member = None):
        target = target or ctx.author 
        
        level_data = DatabaseManager.load_json(self.data_dir + str(ctx.guild.id) + ".json")
        user_data = level_data.get(str(target.id), LevelManager.BLANK_LEVEL_DATA)

        # 這裡外層用雙引號，裡面 user_data['level'] 用單引號
        embed = discord.Embed(
            title = f"{target.display_name} 的等級：Lv.{user_data['level']}", 
            color = discord.Color.from_rgb(80, 255, 80)
        )

        # 設定縮圖為使用者的頭貼 URL
        embed.set_thumbnail(url=target.display_avatar.url)

        # 計算下一級所需的總 XP
        next_level_xp = LevelManager.level_to_xp(user_data['level'] + 1)
        current_xp = int(user_data['xp'])

        embed.add_field(
            value=LevelManager.get_progress_bar(current_xp, next_level_xp), 
            name=f"{current_xp} / {next_level_xp} XP", 
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LevelSystem(bot))