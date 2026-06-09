import asyncio
import re
import time

import discord
from discord.ext import commands

from core.music_manager import MusicManager, FFMPEG_OPTIONS

emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class Music(commands.Cog):
    """YouTube 點歌機器人"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = MusicManager()

    # ------------------------------------------------------------------ #
    #  內部工具
    # ------------------------------------------------------------------ #

    async def _play_next(self, ctx: commands.Context) -> None:
        """載入並播放清單中的下一首歌"""
        state = self.manager.get_state(ctx.channel.id)

        if not state["songs"]:
            state["is_playing"] = False
            return

        song = state["songs"].pop(0)

        try:
            await ctx.send(f"⏳ 正在載入: **{song.get('title', '未知')}**...")
            song = await self.manager.fetch_audio_url(song)
        except Exception as e:
            await ctx.send(f"❌ 載入失敗，跳過此曲: {e}")
            await self._play_next(ctx)
            return

        await ctx.send(f"🎶 正在播放: **{song['title']}**")

        def after_play(error):
            if error:
                print(f"[Music] 播放錯誤: {error}")
            if state["is_skip"]:
                state["is_skip"] = False
                return
            self.bot.loop.create_task(self._play_next(ctx))

        source = discord.FFmpegPCMAudio(song["url"], **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=after_play)

    # ------------------------------------------------------------------ #
    #  指令
    # ------------------------------------------------------------------ #

    @commands.command()
    async def search(self, ctx: commands.Context, *args):
        """搜尋 YouTube 並選擇歌曲加入清單
        用法: !search <關鍵字> [數量(1~10)]
        """
        if not args:
            await ctx.send("請輸入搜尋關鍵字！")
            return

        await ctx.send("🔍 請耐心等候...")
        state = self.manager.get_state(ctx.channel.id)

        if args[-1].isdigit():
            num = int(args[-1])
            keyword = " ".join(args[:-1])
        else:
            num = 5
            keyword = " ".join(args)

        if not 1 <= num <= 10:
            await ctx.send("❌ 數量範圍為 1 ~ 10！")
            return

        start = time.time()
        results = await self.manager.search_yt(keyword, num)
        elapsed = int(time.time() - start)

        if not results:
            await ctx.send("❌ 找不到相關的影片！")
            return

        embed = discord.Embed(
            title=f"🔍 搜尋結果: {keyword} (花費 {elapsed} 秒)",
            color=discord.Color.blue(),
        )
        video_dict = {}

        for i, video in enumerate(results):
            emoji = emoji_list[i]
            embed.add_field(
                name=f"{emoji} {video.get('title', '未知標題')}",
                value=f"[觀看影片]({video.get('url', '')})",
                inline=False,
            )
            video_dict[emoji] = video

        embed.set_footer(text="請點選對應的表情符號來選擇歌曲！")
        message = await ctx.send(embed=embed)

        for i in range(len(results)):
            await message.add_reaction(emoji_list[i])

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in video_dict

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            selected = video_dict[str(reaction.emoji)]
            state["songs"].append(selected)
            await ctx.send(f"🎵 你選擇了: **{selected['title']}**，已加入播放清單")
        except asyncio.TimeoutError:
            await ctx.send("⏰ 選擇超時，請重新搜尋！")

    @commands.command()
    async def add(self, ctx: commands.Context, url: str):
        """直接輸入 YouTube 網址加入清單
        用法: !add <YouTube 網址>
        """
        await ctx.send("🔍 正在解析網址...")
        state = self.manager.get_state(ctx.channel.id)

        clean_url = re.sub(r'&list=[^&]*', '', url)
        clean_url = re.sub(r'&index=[^&]*', '', clean_url)
        clean_url = re.sub(r'\?list=[^&]*&?', '?', clean_url).rstrip('?')

        try:
            info = await self.manager.fetch_single(clean_url)
            state["songs"].append(info)
            await ctx.send(f"✅ 已把 **{info['title']}** 加入播放清單")
        except Exception as e:
            await ctx.send(f"❌ 讀取失敗: {e}")

    @commands.command()
    async def play(self, ctx: commands.Context):
        state = self.manager.get_state(ctx.channel.id)

        if not state["songs"]:
            await ctx.send("❌ 你的播放清單是空的！")
            return

        if not ctx.author.voice:
            await ctx.send("❌ 你需要先加入語音頻道！")
            return

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect(timeout=60, reconnect=True, self_deaf=True)

        if ctx.voice_client.is_playing():
            await ctx.send("🎵 目前有歌曲正在播放，已幫你排隊。")
            return

        state["is_playing"] = True
        await self._play_next(ctx)

    @commands.command()
    async def skip(self, ctx: commands.Context):
        state = self.manager.get_state(ctx.channel.id)

        if not (ctx.voice_client and ctx.voice_client.is_playing()):
            await ctx.send("❌ 目前沒有正在播放的歌曲！")
            return

        state["is_skip"] = True
        ctx.voice_client.stop()
        await ctx.send("⏭️ 已跳過當前歌曲！")

        await asyncio.sleep(1)
        if state["songs"]:
            await self._play_next(ctx)
        else:
            await ctx.send("📭 播放清單已空，機器人下線。")
            await ctx.voice_client.disconnect()
            state["is_playing"] = False

    @commands.command()
    async def stop(self, ctx: commands.Context):
        state = self.manager.get_state(ctx.channel.id)

        if not ctx.voice_client:
            await ctx.send("❌ 我不在任何語音頻道中！")
            return

        state["is_playing"] = False
        state["is_skip"] = False
        state["songs"].clear()
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        self.manager.clear_state(ctx.channel.id)
        await ctx.send("👋 已離開語音頻道並清空歌單")

    @commands.command(name="list")
    async def list_songs(self, ctx: commands.Context, *args):
        state = self.manager.get_state(ctx.channel.id)

        if args and args[0] == 'delete':
            try:
                num = int(args[1])
                removed = state["songs"].pop(num - 1)
                await ctx.send(f"🗑️ 已刪除: {removed['title']}")
            except Exception:
                await ctx.send("❌ 發生錯誤！請確定輸入的號碼有效")
            return

        if not state["songs"]:
            await ctx.send("📭 播放清單為空！")
            return

        embed = discord.Embed(
            title="📋 你的播放清單（不包含目前播放）:",
            color=0x58C5E9,
        )
        for i, song in enumerate(state["songs"]):
            embed.add_field(name=f"{i+1} : {song['title']}", value="—", inline=False)
        embed.set_footer(text="使用 !list delete (數字) 來刪除指定歌曲")
        await ctx.send(embed=embed)

    @commands.command()
    async def jump(self, ctx: commands.Context, index: int):
        state = self.manager.get_state(ctx.channel.id)

        if not (ctx.voice_client and ctx.voice_client.is_playing()):
            await ctx.send("❌ 目前沒有正在播放歌曲！")
            return

        num = index - 1
        if not 0 <= num < len(state["songs"]):
            await ctx.send("❌ 超出範圍！輸入的數字不在清單內")
            return

        state["is_skip"] = True
        ctx.voice_client.stop()
        del state["songs"][:num]

        await ctx.send(f"🚀 跳轉至第 {index} 首歌曲")
        await asyncio.sleep(1)
        await self._play_next(ctx)

    @commands.command()
    async def clear(self, ctx: commands.Context):
        state = self.manager.get_state(ctx.channel.id)
        state["songs"].clear()
        await ctx.send("🧹 已清除播放清單")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))