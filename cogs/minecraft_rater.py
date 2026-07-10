# DEPRECATED: 此 cog 已標記為棄用，不再自動載入。
# 若需恢復，請將 setup() 函數中的 return 移除。

import discord
from discord.ext import commands
from discord import app_commands
import re
from google.genai import types
from core.gemini_client import GeminiAI

class MinecraftRater(commands.Cog):
    def __init__(self, bot, ai_client):
        self.bot = bot
        self.ai = ai_client

    @commands.hybrid_command(name="rate_build", aliases=["rate", "score", "評分"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    @app_commands.describe(image="上傳你想要 AI 評分的 Minecraft 建築圖片 (選填，若未提供則會讀取回覆的圖片)")
    async def rate_build(self, ctx, image: discord.Attachment = None):
        """( 已棄用功能 )"""
        # 1. 取得圖片附件
        attachments = []
        
        # 優先使用參數傳入的圖片
        if image:
            attachments.append(image)
        # 檢查當前訊息是否有附件
        elif ctx.message and ctx.message.attachments:
            attachments = ctx.message.attachments
        # 檢查是否是回覆訊息，且被回覆的訊息是否有附件
        elif ctx.message and ctx.message.reference and ctx.message.reference.resolved:
            resolved_msg = ctx.message.reference.resolved
            if isinstance(resolved_msg, discord.Message):
                attachments = resolved_msg.attachments

        # 過濾出圖片附件 (支援 png, jpg, jpeg, webp 等格式)
        image_attachments = []
        image_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif")
        for att in attachments:
            is_image = False
            if att.content_type and att.content_type.startswith("image/"):
                is_image = True
            elif att.filename and att.filename.lower().endswith(image_extensions):
                is_image = True
            
            if is_image:
                image_attachments.append(att)

        if not image_attachments:
            await ctx.reply("⚠️ 請在上傳建築圖片的同時輸入此指令，或是回覆包含圖片的訊息！")
            # 重設冷卻時間，因為使用者沒成功使用
            ctx.command.reset_cooldown(ctx)
            return

        # 限制最多上傳 10 張圖片，避免 API 過載
        if len(image_attachments) > 10:
            await ctx.reply("⚠️ 一次最多只能評分 10 張圖片喔！")
            ctx.command.reset_cooldown(ctx)
            return

        # 2. 發送讀取/分析中的提示訊息
        thinking_msg = await ctx.reply("🔍 正在下載並分析您的建築圖片，請稍候...")

        try:
            async with ctx.typing():
                # 3. 讀取所有圖片的 bytes 並包裝成 API 格式
                contents = []
                for att in image_attachments:
                    img_bytes = await att.read()
                    
                    # 決定正確的 MIME 類型 (若 content_type 為空，則根據副檔名判定)
                    mime_type = att.content_type
                    if not mime_type and att.filename:
                        filename_lower = att.filename.lower()
                        if filename_lower.endswith((".jpg", ".jpeg")):
                            mime_type = "image/jpeg"
                        elif filename_lower.endswith(".png"):
                            mime_type = "image/png"
                        elif filename_lower.endswith(".webp"):
                            mime_type = "image/webp"
                        elif filename_lower.endswith(".gif"):
                            mime_type = "image/gif"
                    
                    # 如果仍無法判定，預設為 image/png
                    if not mime_type:
                        mime_type = "image/png"

                    part = types.Part.from_bytes(
                        data=img_bytes,
                        mime_type=mime_type
                    )
                    contents.append(part)

                # 4. 定義系統提示詞與評估標準
                SYSTEM_PROMPT = """
                你現在是一位專業的 Minecraft 建築評審與設計大師。
                請針對使用者上傳的 Minecraft 建築圖片進行詳細、客觀且具建設性的評估與評分。

                請以下列格式進行回覆，且使用繁體中文（台灣習慣用語）：

                ## 📊 評分：**[總分] / 100**

                ### 📐 細項評分
                * **外觀與造型 (Shape & Structure)**: [分數] / 25
                * **色調與方塊搭配 (Color & Texturing)**: [分數] / 25
                * **細節與細緻度 (Details)**: [分數] / 25
                * **創意與整體氛圍 (Creativity & Atmosphere)**: [分數] / 25

                ---

                ### 🌟 亮點與優點
                1. [優點一，並說明為什麼好]
                2. [優點二]

                ### 🛠 具體改進建議
                1. [建議一，例如可以增加什麼材質、修改什麼結構]
                2. [建議二]

                ---
                *評審總結：[用一句話總結對這個建築的印象]*

                【注意事項】
                1. 總分必須是四個細項分數的加總（總分 = 外觀與造型 + 色調與方塊搭配 + 細節與細緻度 + 創意與整體氛圍）。
                2. 請保持專業、友善且具鼓勵性的口吻。
                3. 總分請務必用 `**[總分] / 100**` 的格式，以便程式解析。
                """
                # 將提示詞插到最前面
                contents.insert(0, SYSTEM_PROMPT)

                # 5. 調用 Gemini API
                response_text = self.ai.get_response(contents)

                if not response_text:
                    await thinking_msg.edit(content="❌ AI 目前無法回應，請稍後再試。")
                    return

                # 檢查是否為 GeminiAI 類別回傳的錯誤提示
                if response_text.startswith("📢") or response_text.startswith("⚠️") or response_text.startswith("❌") or response_text.startswith("😵"):
                    await thinking_msg.edit(content=response_text)
                    return

                # 6. 解析分數以決定 Embed 顏色
                score = 60  # 預設分數
                match = re.search(r'\*\*(\d+)\s*/\s*100\*\*', response_text)
                if not match:
                    match = re.search(r'(\d+)\s*/\s*100', response_text)
                
                if match:
                    try:
                        score = int(match.group(1))
                    except ValueError:
                        pass

                # 根據分數決定視覺效果（Embed 顏色）
                if score >= 90:
                    embed_color = discord.Color.gold()       # 金色 (神作)
                elif score >= 75:
                    embed_color = discord.Color.green()      # 綠色 (優秀)
                elif score >= 60:
                    embed_color = discord.Color.blue()       # 藍色 (普通)
                else:
                    embed_color = discord.Color.orange()     # 橘色 (待加強)

                # 7. 建立結果 Embed
                embed = discord.Embed(
                    title="🏰 Minecraft 建築評分報告",
                    description=response_text,
                    color=embed_color,
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=ctx.author.display_avatar.url)
                embed.set_footer(
                    text=f"由 {ctx.author.display_name} 提交建築 | Powered by Gemini 2.5 Flash", 
                    icon_url=ctx.author.display_avatar.url
                )

                # 8. 發送 Embed 並刪除「正在分析...」訊息
                await ctx.reply(embed=embed)
                await thinking_msg.delete()

        except Exception as e:
            print(f"Error in rate_build: {e}")
            await thinking_msg.edit(content=f"❌ 評分過程中發生錯誤：{str(e)}")

    @rate_build.error
    async def rate_build_error(self, ctx, error):
        """處理指令錯誤（如冷卻時間限制）"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⌛ 此指令冷卻中，請等待 {error.retry_after:.1f} 秒後再試！", delete_after=5)
        else:
            await ctx.reply(f"❌ 執行指令時發生錯誤：{str(error)}")

async def setup(bot):
    # DEPRECATED: 已停用，不載入此 cog。若需恢復，請移除此 return。
    return
    import os
    ai_client = GeminiAI(os.getenv("GEMINI_API_KEY").split(","))
    await bot.add_cog(MinecraftRater(bot, ai_client))
