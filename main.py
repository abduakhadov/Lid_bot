import asyncio
import logging
import sys
import warnings

# AFC va deprecated paket ogohlantirishlarini o'chirish
warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from db.base import init_db, AsyncSessionLocal
from db.crud import seed_initial_courses
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.courses import router as courses_router
from handlers.contact import router as contact_router
from handlers.chat import router as chat_router
from middlewares.throttle import ThrottlingMiddleware


async def main() -> None:
    # Logging sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Bot ishga tushirilmoqda...")

    # Ma'lumotlar bazasini initsializatsiya qilish
    try:
        await init_db()
        async with AsyncSessionLocal() as session:
            await seed_initial_courses(session)
        logger.info("Ma'lumotlar bazasi va jadvallar muvaffaqiyatli tekshirildi.")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasiga ulanishda xatolik: {e}")

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Spamdan himoya (Rate limit middleware - Bonus vazifa)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=settings.RATE_LIMIT))

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(courses_router)
    dp.include_router(contact_router)
    dp.include_router(chat_router)

    # Telegram menyu komandalarini o'rnatish
    from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

    # Oddiy foydalanuvchilar uchun menyu (admin buyruqlari ko'rinmaydi)
    user_commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="courses", description="Barcha kurslar ro'yxati"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Faqat adminlar uchun maxsus menyu (stats va add_course bilan)
    admin_commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="courses", description="Barcha kurslar ro'yxati"),
        BotCommand(command="stats", description="Lidlar statistikasi (Admin)"),
        BotCommand(command="add_course", description="Yangi kurs qo'shish (Admin)"),
    ]
    for admin_id in settings.admin_id_list:
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            logger.warning(f"Admin ({admin_id}) uchun menyu komandalari o'rnatishda xatolik: {e}")


    # Eski xabarlarni tozalash va pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot tayyor va xabarlarni qabul qilmoqda!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
