import discord, os
from discord.ext import commands
from core.data_base_manager import DatabaseManager
from core.map_view import MapView


class MapSystem(commands.Cog):
    @commands.command(name="create_map_embed")
    @commands.is_owner()
    async def create_map_embed(self, ctx, map_name: str, map_lore: str, fit_version: str, map_path_name: str, url: str):
        # 1. 修正 Embed 建立與 URL (這裡的 url 會讓標題變成可點擊連結)
        embed = discord.Embed(
            title=map_name, 
            description=f"建議 Minecraft 版本: `{fit_version}`", 
            url=url,
            color=discord.Color.blue()
        )

        # 2. 處理本地圖片 (必須轉成 discord.File)
        thumb_path = f"data/projects/{map_path_name}/thumbnail.png"
        file = None
        if os.path.exists(thumb_path):
            file = discord.File(thumb_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png") # 這裡要這樣寫才能對應 file

        # 3. 讀取統計 (確保傳入 BLANK_STATISTIC)
        if not os.path.exists("data/projects/{map_path_name}/statistics.json"):
            blank = MapView.BLANK_STATISTIC
            map_data = blank
            DatabaseManager.save_json(f"data/projects/{map_path_name}/statistics.json", blank)

        # 4. 處理敘述欄位
        map_lores = map_lore.split("\\n") # 建議用 \\n 讓指令輸入時能換行
        for l in map_lores:
            if l.strip(): # 避免空行
                embed.add_field(name="📌 地圖介紹", value=l, inline=False)

        # 5. 顯示統計
        avg_rating = "尚未評分"
        if map_data['rating_count'] > 0:
            avg_rating = round(map_data['total_rating_sum'] / map_data['rating_count'], 1)

        embed.add_field(name="📊 統計資訊", value=f"📥 下載次數：`{map_data['downloads']}`\n⭐ 平均評分：`{avg_rating}`", inline=False)

        # 6. 傳送時記得帶上 file 和傳入 map_path_name 給 View
        view = MapView(map_path_name) 
        await ctx.send(file=file, embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(MapSystem(bot))