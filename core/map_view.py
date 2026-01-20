import discord
import os
from core.data_base_manager import DatabaseManager

class MapView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 永久有效的按鈕

    BLANK_STATISTIC = {"map_version": 1,"downloads": 0,"total_rating_sum": 0,"rating_count": 0, "users":[]}
    BLANK_USER = {"id" : -1, "download_version" : -1, "rate_points" : -1}

    @discord.ui.button(label="📥 下載地圖", style=discord.ButtonStyle.green, custom_id="map_download")
    async def download_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        map_name = self.get_map_name(interaction)
        stats_path = self.get_stats_path(interaction)

        # 1. 讀取統計資料
        data = DatabaseManager.load_json(stats_path, MapView.BLANK_STATISTIC)
        current_map_version = data.get("map_version", 1)
        user_id = interaction.user.id
        
        # 2. 尋找該用戶是否在紀錄中
        if "users" not in data:
            data["users"] = []
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
        DatabaseManager.save_json(stats_path, data)

        # 5. 發送連結或檔案
        url = data.get("download_url", "未設定連結")
        await interaction.response.send_message(
            f"✅ 認證成功！地圖檔案已發送到私訊\n", 
            ephemeral=True
        )
        files = []
        folder = f"data/projects/{map_name}"
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                if filename.endswith(".zip"):
                    files.append(discord.File(os.path.join(folder, filename)))
        await interaction.user.send(f"這是地圖 **{map_name}** 的下載檔案：", files=files)
        await interaction.message.edit(embed = self.renew_embed(interaction, data))

    @discord.ui.button(label="⭐ 評分地圖", style=discord.ButtonStyle.blurple, custom_id="map_rate")
    async def rate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        map_name = self.get_map_name(interaction)
        stats_path = self.get_stats_path(interaction)
        # 呼叫 Modal 並傳入 self (View 本身)
        await interaction.response.send_modal(RatingModal(self))

    def get_map_name(self, interaction : discord.Interaction):
        footer = interaction.message.embeds[0].footer.text
        if not footer.startswith("map_id:"):
            raise ValueError("Embed 缺少 map_id")
        return footer.replace("map_id:", "")
    
    def get_stats_path(self, interaction: discord.Interaction):
        return f"data/projects/{self.get_map_name(interaction)}/statistics.json"
    
    def renew_embed(self, interaction : discord.Interaction, data : dict):
        # 1. 取得舊的 Embed
        old_embed = interaction.message.embeds[0]
        # 2. 複製它，這樣可以保留圖片、顏色、標題等所有設定
        new_embed = old_embed.copy()
        
        # 3. 計算評分
        # 防呆：如果有人評分但 rating_count 為 0 (雖然理論上不會)，避免除以 0
        count = data.get("rating_count", 0)
        total = data.get("total_rating_sum", 0)
        avg_score = round(total / count, 1) if count > 0 else 0

        # 4. 更新特定欄位
        # 我們不再用 len(embed.fields)-1，改用循環尋找，這樣更安全
        for i, field in enumerate(new_embed.fields):
            if "統計資訊" in field.name:
                new_embed.set_field_at(
                    index=i, 
                    name="📊 統計資訊", 
                    value=f"📥 下載次數：`{data['downloads']}`\n⭐ 平均評分：`{avg_score}` ({count} 人評價)",
                    inline=False
                )
                break

        # 關鍵：.copy() 已經幫你保留了 thumbnail 的 url="attachment://thumbnail.png"
        # 且不需要再重新發送 file，Discord 會自動關聯原本訊息中的附件。
        return new_embed

class RatingModal(discord.ui.Modal, title='地圖評分與評價'):
    # 分數輸入框 (短)
    rating_input = discord.ui.TextInput(
        label='請給予這張地圖評分 (1-5)',
        placeholder='請輸入 1 到 5...',
        min_length=1,
        max_length=1,
        required=True
    )
    
    # 評價內容輸入框 (長)
    comment_input = discord.ui.TextInput(
        label='給作者的建議或心得 (選填, 只有遊戲亡本人會看到)',
        style=discord.TextStyle.long, # 設定為多行輸入
        placeholder='這張地圖很有趣！希望下次可以增加...',
        required=False, # 設定為非必填
        max_length=500 # 限制字數防止 JSON 過大
    )

    def __init__(self, map_view: MapView):
        super().__init__()
        self.map_view = map_view

    async def on_submit(self, interaction: discord.Interaction):
        # 1. 驗證分數內容
        try:
            score = int(self.rating_input.value)
            if not (1 <= score <= 5):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ 評分失敗：請輸入 1 到 5 之間的數字。", ephemeral=True)
            return

        # 2. 獲取評價內容
        user_comment = self.comment_input.value if self.comment_input.value else ""

        # 3. 讀取與更新資料
        stats_path = self.map_view.get_stats_path(interaction)
        data = DatabaseManager.load_json(stats_path)
        user_id = interaction.user.id

        # 尋找用戶紀錄
        user_record = next((u for u in data["users"] if u["id"] == user_id), None)
        
        if not user_record:
            await interaction.response.send_message("⚠️ 您必須先點擊「下載」後才能進行評分喔！", ephemeral=True)
            return

        # 4. 更新數據 (處理分數與評論)
        if user_record.get("rate_points", -1) != -1:
            # 扣除舊的分數
            data["total_rating_sum"] -= user_record["rate_points"]
        else:
            # 第一次評分才增加人數
            data["rating_count"] += 1
            
        # 更新該用戶的紀錄 (如果之前有評論，新的會直接覆蓋舊的)
        user_record["rate_points"] = score
        user_record["comment"] = user_comment # 新增欄位儲存評價
        user_record["last_rated_at"] = str(discord.utils.utcnow()) # 紀錄評價時間

        data["total_rating_sum"] += score
        DatabaseManager.save_json(stats_path, data)

        # 5. 更新原本的 Embed (這部分代碼與之前相同)
        await interaction.message.edit(embed = self.map_view.renew_embed(interaction, data))
        
        msg = f"✅ 感謝您的評價！您給予了 {score} 顆星。"
        if user_comment:
            msg += f"\n您的評價內容：{user_comment}"
            
        await interaction.response.send_message(msg, ephemeral=True)