import os
import asyncio

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv, find_dotenv
from core.handlers.commands import set_admin_commands
from core.handlers.lessons import set_lessons

from core.handlers.start import set_start
from core.handlers.testing import set_options

load_dotenv(find_dotenv())
TOKEN = os.environ.get("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await set_start(dp)
    await set_admin_commands(dp)
    await set_options(dp)
    await set_lessons(dp)

    print("Bot started!")
    
    try:
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")