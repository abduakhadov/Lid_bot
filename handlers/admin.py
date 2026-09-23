import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import settings
from db.base import AsyncSessionLocal
from db.crud import get_lead_statistics, create_course

logger = logging.getLogger(__name__)
router = Router(name="admin_router")


class AddCourseStates(StatesGroup):
    name = State()
    description = State()
    price = State()
    duration = State()
    age_limits = State()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    admins = settings.admin_id_list
    # Agar ADMIN_IDS berilmagan bo'lsa, test uchun barcha foydalanuvchilar ishlata oladi
    if not admins:
        return True
    return user_id in admins


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """
    Statistika buyrug'i:
    Bugungi lidlar soni, jami lidlar va eng ko'p tanlangan kurs.
    """
    if not is_admin(message.from_user.id):
        await message.answer("Kechirasiz, ushbu buyruq faqat bot adminlari uchun.")
        return

    async with AsyncSessionLocal() as session:
        stats = await get_lead_statistics(session)

    stats_text = (
        "📊 <b>BOT VA LIDLAR STATISTIKASI</b>\n\n"
        f"📅 <b>Bugungi yangi lidlar:</b> {stats['today_leads']} ta\n"
        f"👥 <b>Jami lidlar soni:</b> {stats['total_leads']} ta\n"
        f"🔥 <b>Aniq lidlar (Hot/Accepted):</b> {stats['hot_leads']} ta\n"
        f"⚠️ <b>Operator yordami so'raganlar:</b> {stats['needs_operator_leads']} ta\n\n"
        f"🏆 <b>Eng ko'p tanlangan kurs:</b>\n"
        f"👉 <b>{stats['top_course_name']}</b> ({stats['top_course_count']} marta tanlangan)"
    )

    await message.answer(stats_text)


@router.message(Command("add_course"))
async def cmd_add_course(message: Message, state: FSMContext) -> None:
    """Yangi kurs qo'shish jarayonini boshlash"""
    if not is_admin(message.from_user.id):
        await message.answer("Kechirasiz, ushbu buyruq faqat bot adminlari uchun.")
        return

    await state.set_state(AddCourseStates.name)
    await message.answer(
        "➕ <b>Yangi kurs qo'shish</b>\n\n"
        "Kurs nomini kiriting (Masalan: <i>Node.js Backend</i>):\n\n"
        "<i>(Bekor qilish uchun /cancel yozing)</i>"
    )


@router.message(Command("cancel"), AddCourseStates())
async def cmd_cancel_add_course(message: Message, state: FSMContext) -> None:
    """Kurs qo'shishni bekor qilish"""
    await state.clear()
    await message.answer("❌ Kurs qo'shish bekor qilindi.")


@router.message(AddCourseStates.name)
async def process_course_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Iltimos, to'g'ri kurs nomini kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(AddCourseStates.description)
    await message.answer("Kurs haqida qisqacha tavsif (description) yozing:")


@router.message(AddCourseStates.description)
async def process_course_description(message: Message, state: FSMContext) -> None:
    desc = message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddCourseStates.price)
    await message.answer("Kursning oylik narxini faqat raqamda kiriting (so'mda, masalan: <i>850000</i>):")


@router.message(AddCourseStates.price)
async def process_course_price(message: Message, state: FSMContext) -> None:
    text = message.text.strip().replace(" ", "").replace(",", "")
    if not text.isdigit():
        await message.answer("Iltimos, narxni faqat butun son ko'rinishida yozing (masalan: 850000):")
        return

    price = int(text)
    await state.update_data(price=price)
    await state.set_state(AddCourseStates.duration)
    await message.answer("Kurs davomiyligini kiriting (Masalan: <i>4 oy</i> yoki <i>6 oy</i>):")


@router.message(AddCourseStates.duration)
async def process_course_duration(message: Message, state: FSMContext) -> None:
    duration = message.text.strip()
    await state.update_data(duration=duration)
    await state.set_state(AddCourseStates.age_limits)
    await message.answer(
        "Yosh chegarasini kiriting (Masalan: <b>12-40</b> yoki minimal va maksimal yoshni defis bilan yozing):"
    )


@router.message(AddCourseStates.age_limits)
async def process_course_age_limits(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    age_min, age_max = 7, 50

    try:
        if "-" in text:
            parts = text.split("-")
            age_min = int(parts[0].strip())
            age_max = int(parts[1].strip())
        elif text.isdigit():
            age_min = int(text)
            age_max = 60
    except Exception:
        pass

    data = await state.get_data()
    await state.clear()

    # Bazaga yangi kursni saqlash
    async with AsyncSessionLocal() as session:
        new_course = await create_course(
            session=session,
            name=data["name"],
            description=data["description"],
            price=data["price"],
            duration=data["duration"],
            age_min=age_min,
            age_max=age_max
        )

    price_str = f"{new_course.price:,}".replace(",", " ") + " so'm"
    await message.answer(
        f"✅ <b>Yangi kurs muvaffaqiyatli qo'shildi!</b>\n\n"
        f"📚 <b>Nomi:</b> {new_course.name}\n"
        f"📝 <b>Tavsif:</b> {new_course.description}\n"
        f"💰 <b>Narxi:</b> {price_str}\n"
        f"⏱ <b>Davomiyligi:</b> {new_course.duration}\n"
        f"👥 <b>Yosh chegarasi:</b> {new_course.age_min}-{new_course.age_max} yosh\n\n"
        "Ushbu kurs avtomatik ravishda bot inline menyusiga va AI system promptiga qo'shildi!"
    )
