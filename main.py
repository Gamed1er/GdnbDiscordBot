import discord
import os
import json
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from core.map_view import MapView
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import logging
load_dotenv() # 載入 .env 檔案中的變數

# 設定全域 Logging
def setup_logging():
    # 1. 建立 .log 資料夾
    log_dir = "/log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 2. 定義基礎 Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 3. 設定 TimedRotatingFileHandler
    # filename: 初始檔案路徑
    # when='midnight': 每天午夜自動切割
    # interval=1: 每 1 天執行一次
    # backupCount=30: 保留最近 30 天的 log，舊的自動刪除
    log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%y%m%d')}.log")
    
    handler = TimedRotatingFileHandler(
        filename=log_filename,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )

    # 4. 自定義滾動檔案的檔名格式 (讓它符合 260221.log 這種格式)
    # 預設行為會把日期加在副檔名後面，我們透過以下函數修正它
    handler.suffix = "%y%m%d.log" 
    
    # 5. 設定格式與輸出
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    
    # 同時在螢幕上顯示
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

# 執行初始化
setup_logging()
logger = logging.getLogger(__name__)
logger.info("日誌系統啟動成功，每天將自動建立新檔案。")

class GdnbBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="$", intents=intents)

    async def setup_hook(self):
        self.add_view(MapView())

        # 自動載入 cogs 資料夾下的所有 .py 檔
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != "prefab.py":
                await self.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'已載入模組: {filename}')

    async def on_ready(self):
        # 原有的同步邏輯
        self.tree.clear_commands(guild=None)
        await self.tree.sync() 
        logger.info(f'已同步斜線指令。機器人 {self.user} 已上線！')

        # 修正 JSON 讀取
        try:
            with open("data/announcement_register_channel.json", "r", encoding="utf-8") as f:
                registered = json.load(f)
            
            for guild in registered.values():
                for channel_id in guild:
                    channel = self.get_channel(channel_id)
                    # 如果 get_channel 拿不到 (快取還沒好)，就用 fetch_channel 硬抓
                    if channel is None:
                        try:
                            channel = await self.fetch_channel(channel_id)
                        except:
                            continue
                    
                    if channel:
                        await channel.send(":green_circle: 【我不是遊戲亡】已上線")
        except Exception as e:
            logger.error(f"上線通知發送失敗: {e}")

    async def close(self):
        logger.info("機器人正在關閉，發送下線通知...")
        try:
            # 修正 JSON 讀取
            with open("data/announcement_register_channel.json", "r", encoding="utf-8") as f:
                registered = json.load(f)
            
            for guild in registered.values():
                for channel_id in guild:
                    channel = self.get_channel(channel_id)
                    if channel:
                        await channel.send(":red_circle: 【我不是遊戲亡】已下線")
        except Exception as e:
            logger.info(f"下線通知發送失敗: {e}")
            
        await super().close()

    async def on_command_error(self, ctx, error):
        # 1. 捕捉「缺少參數」錯誤 (你剛遇到的 MissingRequiredArgument)
        if isinstance(error, commands.MissingRequiredArgument):
            message = f":negative_squared_cross_mark: 缺少參數：請確保輸入了正確的指令格式。"
        
        # 2. 捕捉「找不到指令」錯誤 (你剛遇到的 CommandNotFound)
        elif isinstance(error, commands.CommandNotFound):
            message = f":negative_squared_cross_mark: 找不到指令：`{ctx.invoked_with}`。請輸入正確的指令。"
        
        # 3. 捕捉「權限不足」錯誤 (你設置的 is_owner)
        elif isinstance(error, commands.NotOwner):
            message = f":negative_squared_cross_mark: 權限不足：只有機器人擁有者可以執行此指令。"

        # 4. 捕捉「權限不足」錯誤 (你設置的 is_owner)
        elif isinstance(error, commands.NotOwner):
            message = f":negative_squared_cross_mark: 權限不足：只有擁有 Administer 權限的才可以執行此指令。"
            
        # 5. 其他未知錯誤
        else:
            message = f":fire: 發生未知錯誤：{str(error)}，請通知管理員"

        # 將錯誤訊息發送到頻道中，並設置 10 秒後自動刪除 (保持頻道整潔)
        await ctx.reply(message)


bot = GdnbBot()
bot.run(os.getenv("DISCORD_TOKEN"))
