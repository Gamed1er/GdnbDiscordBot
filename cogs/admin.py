from discord.ext import commands
import json, os
from core.data_base_manager import DatabaseManager

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ext")
    @commands.is_owner()
    async def extension_operation(self, ctx, operation: str, extension: str):
        """load/unload/reload a extension"""
        ext_path = f"cogs.{extension}"
        try:
            if operation == "load":
                await self.bot.load_extension(ext_path)
            elif operation == "reload":
                await self.bot.reload_extension(ext_path)
            elif operation == "unload":
                await self.bot.unload_extension(ext_path)
            else:
                await ctx.send(f"格式不正確 ! 應該為`$ext <load/unload/reload> <extension_name>`")
                return
            await ctx.send(f"✅ `{operation}`: `{extension}`")
        except Exception as e:
            await ctx.send(f"❌ {e}")

    @commands.command(name = "stop", description = "Close this Discord Bot")
    @commands.is_owner()
    async def stop(self, ctx):        
        # 這裡會觸發 main.py 裡面的 self.close()
        # 進而觸發你寫的廣播下線通知邏輯
        await self.bot.close()

    @commands.command(name = "ai_channel_register", description = "Let this channel can / cannot send Gemini messages.")
    @commands.has_permissions(administrator = True)
    async def ai_channel_register(self, ctx):
        target_channel_id = ctx.channel.id
        registered = DatabaseManager.load_json("data/ai_register_channel.json", [])

        if target_channel_id in registered:
            registered.remove(target_channel_id)
            await ctx.reply(":mute: 這個頻道不可以跟 AI 聊天 :upside_down:")

        else:
            registered.append(target_channel_id)
            await ctx.reply(":loud_sound: 這個頻道現在可以跟 AI 聊天了")

        DatabaseManager.save_json("data/ai_register_channel.json", registered)

    @commands.command(name="announcement_channel_register")
    @commands.has_permissions(administrator=True)
    async def announcement_channel_register(self, ctx):
        target_channel_id = ctx.channel.id
        path = "data/announcement_register_channel.json"
        data = DatabaseManager.load_json(path)

        # 1. 統一將 Guild ID 轉換為字串
        guild_id_str = str(ctx.guild.id)

        # 2. 檢查該伺服器是否在資料中，若無則初始化空清單
        if guild_id_str not in data:
            data[guild_id_str] = []

        # 3. 執行邏輯切換 (Toggle)
        if target_channel_id in data[guild_id_str]:
            data[guild_id_str].remove(target_channel_id)
            await ctx.reply("🔇 這個機器人**不會**在這個頻道發布公告")
        else:
            data[guild_id_str].append(target_channel_id)
            await ctx.reply("🔊 這個機器人**會**在這個頻道發布公告")

        # 4. 儲存回檔案
        DatabaseManager.save_json(path, data)

async def setup(bot):
    await bot.add_cog(Admin(bot))