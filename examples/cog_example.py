import discord
from discord.ext import commands

class Prefab(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 範例 A：新增一個斜線指令 / 一般指令
    @commands.command(name="helloWorld")
    async def hello_command(self, ctx):
        await ctx.send(f"Hello, {ctx.author.mention}！")

    # 範例 B：監聽 Discord 事件 (例如使用者傳送訊息)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if "特殊關鍵字" in message.content:
            await message.channel.send("偵測到關鍵字！")

async def setup(bot):
    await bot.add_cog(Prefab(bot))