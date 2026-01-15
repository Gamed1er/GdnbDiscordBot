from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ext")
    @commands.is_owner()
    async def extension_operation(self, ctx, operation: str, extension: str):
        ext_path = f"cogs.{extension}"
        try:
            if operation == "load":
                await self.bot.load_extension(ext_path)
            elif operation == "reload":
                await self.bot.reload_extension(ext_path)
            elif operation == "unload":
                await self.bot.unload_extension(ext_path)
            await ctx.send(f"✅ `{operation}`: `{extension}`")
        except Exception as e:
            await ctx.send(f"❌ {e}")

async def setup(bot):
    await bot.add_cog(Admin(bot))