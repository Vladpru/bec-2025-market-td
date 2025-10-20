import asyncio
from dotenv import load_dotenv
load_dotenv()
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.admin import admin_start
from config import load_config
from bot.middleware.check_user import AuthMiddleware
from bot.handlers import captain, captain_help, captain_shop, helpdesk, helpdesk_add, organizer, organizer_analytics, organizer_limits, organizer_phase, organizer_shop, start
from bot.utils.database import get_database

config = load_config()

if not config.bot_token:
    raise ValueError("BOT_TOKEN не знайдено! Перевірте ваш .env файл.")

bot = Bot(token=config.bot_token) 
dp = Dispatcher(storage=MemoryStorage())


async def main():
    bot.session.default_parse_mode = "HTML"
    db = await get_database()
    
    dp.message.middleware(AuthMiddleware(db))
    
    dp.include_routers(
        start.router,
        captain.router,
        captain_shop.router,
        captain_help.router,
        helpdesk.router,
        helpdesk_add.router,
        organizer.router,
        organizer_shop.router,
        organizer_limits.router,
        organizer_phase.router,
        organizer_analytics.router,
        admin_start.router,
    )
    
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Помилка сталася: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())