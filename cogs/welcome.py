import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from core.data_base_manager import DatabaseManager

WELCOME_DATA_PATH = "data/welcome_register_channel.json"
TZ_TAIPEI = timezone(timedelta(hours=8))


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_channel_id(self, guild_id: int):
        data = DatabaseManager.load_json(WELCOME_DATA_PATH, {})
        return data.get(str(guild_id))

    def _format_time(self) -> str:
        now = datetime.now(TZ_TAIPEI)
        return f"{now.strftime('%Y-%m-%d')} {now.hour}:{now.strftime('%M')}"

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = self._get_channel_id(member.guild.id)
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if channel is None:
            return

        guild = member.guild
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            name=f"歡迎來到 {guild.name}",
            icon_url=guild.icon.url if guild.icon else None
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.description = (
            f"歡迎 **{member.display_name}** 來到 **{guild.name}**\n"
            f"你是第 **{guild.member_count}** 個進入伺服器的人"
        )
        embed.set_footer(text=self._format_time())

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel_id = self._get_channel_id(member.guild.id)
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if channel is None:
            return

        guild = member.guild
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(
            name=f"{member.display_name} 離開了 {guild.name}",
            icon_url=guild.icon.url if guild.icon else None
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.description = "一路走好~"
        embed.set_footer(text=self._format_time())

        await channel.send(embed=embed)

    @commands.hybrid_command(name="welcome_channel_register", description="設定或取消這個頻道為歡迎/離開通知頻道")
    @commands.has_permissions(administrator=True)
    async def welcome_channel_register(self, ctx):
        data = DatabaseManager.load_json(WELCOME_DATA_PATH, {})
        guild_id_str = str(ctx.guild.id)
        channel_id = ctx.channel.id

        if data.get(guild_id_str) == channel_id:
            del data[guild_id_str]
            await ctx.reply("🔇 已取消這個頻道的歡迎/離開通知")
        else:
            data[guild_id_str] = channel_id
            await ctx.reply("🔊 這個頻道現在會顯示成員加入/離開通知")

        DatabaseManager.save_json(WELCOME_DATA_PATH, data)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
