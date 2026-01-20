import discord
import os
from core.data_base_manager import DatabaseManager

class MapView(discord.ui.View):
    def __init__(self, map_name):
        super().__init__(timeout=None) # 永久有效的按鈕
        self.map_name = map_name
        self.stats_path = f"data/projects/{map_name}/statistics.json"

    BLANK_STATISTIC = {"map_version": 1,"downloads": 0,"total_rating_sum": 0,"rating_count": 0, "users":[]}
    BLANK_USER = {"id" : -1, "download_version" : -1, "rate_points" : -1}

    @discord.ui.button(label="📥 下載地圖", style=discord.ButtonStyle.green)
    async def download_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. 讀取統計資料
        data = DatabaseManager.load_json(self.stats_path)
        current_map_version = data.get("map_version", 1)
        user_id = interaction.user.id
        
        # 2. 尋找該用戶是否在紀錄中
        user_record = next((u for u in data["users"] if u["id"] == user_id), None)

        # 3. 檢查下載資格
        if user_record:
            # 如果用戶下載過，且版本等於當前版本
            if user_record["download_version"] >= current_map_version:
                await interaction.response.send_message(
                    f"❌ 您已經下載過版本 {current_map_version} 了！請檢查您的私訊紀錄。", 
                    ephemeral=True
                )
                return
        else:
            # 如果是全新用戶，建立新紀錄
            user_record = {"id": user_id, "download_version": -1, "rate_points": -1}
            data["users"].append(user_record)

        # 4. 通過檢查，執行下載流程
        # 更新用戶下載版本與總下載量
        user_record["download_version"] = current_map_version
        data["downloads"] += 1
        DatabaseManager.save_json(self.stats_path, data)

        # 5. 發送連結或檔案
        url = data.get("download_url", "未設定連結")
        await interaction.response.send_message(
            f"✅ 認證成功！地圖檔案已發送到私訊\n", 
            ephemeral=True
        )
        files = []
        folder = f"data/projects/{self.map_name}"
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                if filename.endswith(".zip"):
                    files.append(discord.File(os.path.join(folder, filename)))
        await interaction.user.send(f"這是地圖 **{self.map_name}** 的下載檔案：", files=files)

    @discord.ui.button(label="⭐ 評分地圖", style=discord.ButtonStyle.blurple)
    async def rate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 呼叫 Modal 並傳入 self (View 本身)
        await interaction.response.send_modal(RatingModal(self))

class RatingModal(discord.ui.Modal, title='地圖評分系統'):
    # 定義輸入框
    rating_input = discord.ui.TextInput(
        label='請給予這張地圖評分 (1-5)',
        placeholder='請輸入 1 到 5 的整數...',
        min_length=1,
        max_length=1,
        required=True
    )

    def __init__(self, map_view):
        super().__init__()
        self.map_view = map_view # 存取原本的 View 以便更新 Embed

    async def on_submit(self, interaction: discord.Interaction):
        # 1. 驗證輸入內容
        try:
            score = int(self.rating_input.value)
            if not (1 <= score <= 5):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ 評分失敗：請輸入 1 到 5 之間的數字。", ephemeral=True)
            return

        # 2. 讀取與更新資料 (使用 DatabaseManager)
        from core.data_base_manager import DatabaseManager
        data = DatabaseManager.load_json(self.map_view.stats_path)
        user_id = interaction.user.id

        # 3. 尋找用戶紀錄 (確保已下載過才能評分，或依你的需求調整)
        user_record = next((u for u in data["users"] if u["id"] == user_id), None)
        
        if not user_record:
            await interaction.response.send_message("⚠️ 您必須先點擊「下載」後才能進行評分喔！", ephemeral=True)
            return

        # 4. 更新數據
        user_record["rate_points"] = score
        data["total_rating_sum"] += score
        data["rating_count"] += 1
        DatabaseManager.save_json(self.map_view.stats_path, data)

        # 5. 更新原本的 Embed
        # 計算新平均分
        avg_score = round(data["total_rating_sum"] / data["rating_count"], 1)
        
        # 取得原本的 Embed 並修改特定欄位 (假設評分欄位是最後一個)
        embed = interaction.message.embeds[0]
        # 重新設定統計資訊欄位 (根據你之前的格式)
        # 假設你的統計欄位是在最後一個 field
        embed.set_field_at(
            index=len(embed.fields) - 1, 
            name="📊 統計資訊", 
            value=f"📥 下載次數：`{data['downloads']}`\n⭐ 平均評分：`{avg_score}` ({data['rating_count']} 人評價)",
            inline=False
        )

        # 更新原始訊息的 Embed
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"✅ 感謝您的評價！您給予了 {score} 顆星。", ephemeral=True)