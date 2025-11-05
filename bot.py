import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.video_meting import start_call_manager
from app.handlers import router
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаем PyTgCalls в фоне
    await start_call_manager()

    # Запускаем aiogram
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())