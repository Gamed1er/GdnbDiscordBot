import discord
from discord.ext import commands
from discord import app_commands
from core.map_view import MapView
from core.data_base_manager import DatabaseManager
import os

class MapSetupModal(discord.ui.Modal, title='發布新地圖 Embed'):
    # 定義表單內容
    map_name = discord.ui.TextInput(label='地圖顯示名稱', placeholder='例如：超極限生存島嶼')
    fit_version = discord.ui.TextInput(label='適用版本', placeholder='例如：1.20.1', default='1.20.1')
    map_path = discord.ui.TextInput(label='資料夾路徑名稱', placeholder='需與 data/projects/ 下的名稱一致')
    map_url = discord.ui.TextInput(label='官網/參考連結 (選填)', required=False)
    map_lore = discord.ui.TextInput(
        label='地圖詳細介紹', 
        style=discord.TextStyle.long, 
        placeholder='請輸入地圖的特色描述...',
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        path_name = self.map_path.value.strip()
        project_dir = f"data/projects/{path_name}"
        stats_path = f"{project_dir}/statistics.json"
        thumb_path = f"{project_dir}/thumbnail.png"

        # 1. 自動檢查資料夾是否存在，不存在就幫你建！
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        # 2. 處理統計資料 (不重複覆蓋)
        if not os.path.exists(stats_path):
            map_data = MapView.BLANK_STATISTIC.copy()
            DatabaseManager.save_json(stats_path, map_data)
        else:
            map_data = DatabaseManager.load_json(stats_path)

        # 3. 建立視覺化 Embed
        embed = discord.Embed(
            title=self.map_name.value,
            description=f"✅ **建議版本**: `{self.fit_version.value}`",
            url=self.map_url.value if self.map_url.value else None,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"map_id:{path_name}")

        # 處理圖片
        file = None
        if os.path.exists(thumb_path):
            file = discord.File(thumb_path, filename="thumbnail.png")
            embed.set_thumbnail(url="attachment://thumbnail.png")
        else:
            embed.set_footer(text=f"map_id:{path_name} (⚠ 缺少縮圖)")

        # 處理統計資訊顯示
        avg_rating = "尚未評分"
        if map_data['rating_count'] > 0:
            avg_rating = round(map_data['total_rating_sum'] / map_data['rating_count'], 1)

        embed.add_field(name="📌 地圖介紹", value=self.map_lore.value, inline=False)
        embed.add_field(
            name="📊 統計資訊", 
            value=f"📥 下載次數：`{map_data['downloads']}`\n⭐ 平均評分：`{avg_rating}`", 
            inline=False
        )

        # 4. 發送結果
        view = MapView() # 持久化 View
        await interaction.channel.send(file=file, embed=embed, view=view)
        await interaction.response.send_message(f"✅ 地圖 `{self.map_name.value}` 已成功發布！", ephemeral=True)

class MapSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setup_map", description="Launch the interactive wizard to publish a new map.")
    @commands.is_owner()
    async def setup_map(self, ctx):
        """啟動發布地圖的視覺化精靈"""
        await ctx.send("請點擊下方按鈕開始設定地圖資訊：", view=MapSetupLauncher())

class MapSetupLauncher(discord.ui.View):
    @discord.ui.button(label="開啟發布表單", style=discord.ButtonStyle.primary, emoji="🛠")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MapSetupModal())

async def setup(bot):
    await bot.add_cog(MapSystem(bot))