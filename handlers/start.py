from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db.crud import get_active_courses, upsert_lead
from keyboards.inline import get_courses_keyboard

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """
    /start bosilganda bot salomlashadi, kurslarni inline tugmalarda ko'rsatadi
    va AI suhbatni boshlaydi.
    Bir xil foydalanuvchi qayta yozilsa yangi lid yaratilmaydi, mavjudi yangilanadi (dublikatsiz).
    """
    await state.clear()
    await state.update_data(history=[])

    user = message.from_user
    user_name = user.first_name if user else "do'stim"
    
    # Bazaga foydalanuvchini upsert qilish va faol kurslarni olish
    async with AsyncSessionLocal() as session:
        if user:
            await upsert_lead(
                session=session,
                telegram_id=user.id,
                username=user.username,
                full_name=user.full_name,
                status="collecting"
            )
        courses = await get_active_courses(session)

    welcome_text = (
        f"Assalomu alaykum, {user_name}! 👋\n\n"
        "O'quv markazimizning rasmiy aqlli botiga xush kelibsiz!\n"
        "Men sizga barcha kurslarimiz haqida batafsil ma'lumot beraman va ro'yxatdan o'tishingizga yordamlashaman.\n\n"
        "📋 <b>Mavjud kurslarimiz bilan tanishing:</b>\n"
        "(Quyidagi tugmalardan birini tanlashingiz yoki suhbatda bemalol o'zingiz xohlagan savolni yozishingiz mumkin)"
    )
    
    keyboard = get_courses_keyboard(courses) if courses else None
    await message.answer(welcome_text, reply_markup=keyboard)
