import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db.crud import get_active_courses, get_course_by_id
from keyboards.inline import get_courses_keyboard, get_course_detail_keyboard

logger = logging.getLogger(__name__)
router = Router(name="courses_router")


@router.message(Command("courses"))
async def cmd_courses(message: Message) -> None:
    """Kurslar ro'yxatini inline tugmalar bilan chiqarish"""
    async with AsyncSessionLocal() as session:
        courses = await get_active_courses(session)

    if not courses:
        await message.answer("Hozircha faol kurslar ro'yxati mavjud emas.")
        return

    text = (
        "🎓 <b>Bizning o'quv markazimizdagi mavjud kurslar:</b>\n\n"
        "Quyidagi tugmalar orqali kurs bilan tanishishingiz va o'zingizga ma'qulini tanlashingiz mumkin:"
    )
    await message.answer(text, reply_markup=get_courses_keyboard(courses))


@router.callback_query(F.data.startswith("select_course:"))
async def handle_course_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Foydalanuvchi inline tugma orqali kurs tanlaganda"""
    course_id_str = callback.data.split(":")[1]
    if not course_id_str.isdigit():
        await callback.answer("Noto'g'ri kurs tanlandi.", show_alert=True)
        return

    course_id = int(course_id_str)

    async with AsyncSessionLocal() as session:
        course = await get_course_by_id(session, course_id)

    if not course:
        await callback.answer("Kechirasiz, bu kurs topilmadi.", show_alert=True)
        return

    # FSM contextga tanlangan kursni saqlash
    data = await state.get_data()
    history = data.get("history", [])

    # Tanlangan kurs haqidagi ma'lumotni saqlash
    await state.update_data(selected_course_id=course.id, selected_course_name=course.name)

    # AI tarixiga kurs tanlanganligini qo'shish, shunda AI foydalanuvchining bu kursni tanlaganini biladi
    system_event = f"[Tizim xabari: Foydalanuvchi '{course.name}' kursini tanladi.]"
    history.append({"role": "user", "text": system_event})
    await state.update_data(history=history)

    price_str = f"{course.price:,}".replace(",", " ") + " so'm/oy" if course.price else "Kelishiladi"

    response_text = (
        f"🎯 <b>Ajoyib tanlov! Siz \"{course.name}\" kursini tanladingiz.</b>\n\n"
        f"⏱ <b>Davomiyligi:</b> {course.duration}\n"
        f"💰 <b>Narxi:</b> {price_str}\n"
        f"👥 <b>Yosh chegarasi:</b> {course.age_min} dan {course.age_max} yoshgacha\n"
        f"📝 <b>Tavsif:</b> {course.description}\n\n"
        "Ushbu kursga yozilish yoki qo'shimcha savollaringiz bo'lsa, bemalol yozishingiz mumkin!"
    )

    await callback.message.edit_text(
        text=response_text,
        reply_markup=get_course_detail_keyboard(course.id)
    )
    await callback.answer()


@router.callback_query(F.data == "show_all_courses")
async def handle_show_all_courses(callback: CallbackQuery) -> None:
    """Barcha kurslar ro'yxatini qayta chiqarish"""
    async with AsyncSessionLocal() as session:
        courses = await get_active_courses(session)

    text = (
        "🎓 <b>Bizning o'quv markazimizdagi mavjud kurslar:</b>\n\n"
        "O'zingizga qiziq bo'lgan kursni tanlang:"
    )
    await callback.message.edit_text(text=text, reply_markup=get_courses_keyboard(courses))
    await callback.answer()


@router.callback_query(F.data.startswith("accept_lead:"))
async def handle_accept_lead(callback: CallbackQuery) -> None:
    """Operator / Admin 'Qabul qilish' tugmasini bosganda"""
    from db.models import Lead
    from services.sheets import update_lead_status_in_sheets

    lead_id_str = callback.data.split(":")[1]
    if not lead_id_str.isdigit():
        return

    lead_id = int(lead_id_str)
    operator_name = callback.from_user.full_name or callback.from_user.first_name

    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        if not lead:
            await callback.answer("Lid topilmadi.", show_alert=True)
            return

        if lead.status in ["accepted", "rejected"]:
            status_text = "qabul qilingan" if lead.status == "accepted" else "rad etilgan"
            await callback.answer(f"Ushbu arizaga allaqachon qaror qilingan ({status_text})!", show_alert=True)
            return

        lead.status = "accepted"
        user_tg_id = lead.telegram_id
        lead_phone = lead.phone
        lead_name = lead.full_name
        await session.commit()


    # Google Sheets dagi statusni yangilash (eng oxirgi qo'shilgan mos qatorni topadi)
    if lead_phone or lead_name:
        try:
            update_lead_status_in_sheets(phone=lead_phone or "", new_status="Qabul qilindi", name=lead_name)
        except Exception as e:
            logger.error(f"Sheets statusini update qilishda xatolik: {e}")


    # Admin xabarini tahrirlash (tugmalarni olib tashlash)
    original_text = callback.message.html_text or callback.message.text
    updated_text = f"{original_text}\n\n✅ <b>QABUL QILINDI</b> (Operator: {operator_name})"

    try:
        await callback.message.edit_text(text=updated_text, reply_markup=None)
        await callback.answer("Ariza qabul qilindi!")
    except Exception as e:
        logger.error(f"Xabarni tahrirlashda xatolik: {e}")
        await callback.answer()

    # Foydalanuvchining shaxsiy Telegramiga xabar yuborish
    try:
        user_msg = (
            "🎉 <b>Tabriklaymiz! Sizning kursga yozilish arizangiz qabul qilindi.</b>\n\n"
            "📞 Operatorimiz tez orada siz taqdim etgan telefon raqamingiz orqali bog'lanadi."
        )
        await callback.bot.send_message(chat_id=user_tg_id, text=user_msg)
        logger.info(f"Foydalanuvchiga (ID: {user_tg_id}) 'Qabul qilindi' xabari yuborildi.")
    except Exception as e:
        logger.error(f"Foydalanuvchiga (ID: {user_tg_id}) xabar yuborishda xatolik: {e}")


@router.callback_query(F.data.startswith("reject_lead:"))
async def handle_reject_lead(callback: CallbackQuery) -> None:
    """Operator / Admin 'Rad etish' tugmasini bosganda"""
    from db.models import Lead
    from services.sheets import update_lead_status_in_sheets

    lead_id_str = callback.data.split(":")[1]
    if not lead_id_str.isdigit():
        return

    lead_id = int(lead_id_str)
    operator_name = callback.from_user.full_name or callback.from_user.first_name

    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        if not lead:
            await callback.answer("Lid topilmadi.", show_alert=True)
            return

        if lead.status in ["accepted", "rejected"]:
            status_text = "qabul qilingan" if lead.status == "accepted" else "rad etilgan"
            await callback.answer(f"Ushbu arizaga allaqachon qaror qilingan ({status_text})!", show_alert=True)
            return

        lead.status = "rejected"
        user_tg_id = lead.telegram_id
        lead_phone = lead.phone
        lead_name = lead.full_name
        await session.commit()

    # Google Sheets dagi statusni yangilash (eng oxirgi qo'shilgan mos qatorni topadi)
    if lead_phone or lead_name:
        try:
            update_lead_status_in_sheets(phone=lead_phone or "", new_status="Rad etildi", name=lead_name)
        except Exception as e:
            logger.error(f"Sheets statusini update qilishda xatolik: {e}")


    # Admin xabarini tahrirlash (tugmalarni olib tashlash)
    original_text = callback.message.html_text or callback.message.text
    updated_text = f"{original_text}\n\n❌ <b>RAD ETILDI</b> (Operator: {operator_name})"

    try:
        await callback.message.edit_text(text=updated_text, reply_markup=None)
        await callback.answer("Ariza rad etildi!")
    except Exception as e:
        logger.error(f"Xabarni tahrirlashda xatolik: {e}")
        await callback.answer()

    # Foydalanuvchining shaxsiy Telegramiga xabar yuborish
    try:
        user_msg = (
            "❌ <b>Afsuski, sizning kursga yozilish arizangiz rad etildi.</b>\n\n"
            "💡 Savollaringiz bo'lsa yoki boshqa kurslar bilan tanishmoqchi bo'lsangiz, /start bosib AI bilan qayta bog'lanishingiz mumkin."
        )
        await callback.bot.send_message(chat_id=user_tg_id, text=user_msg)
        logger.info(f"Foydalanuvchiga (ID: {user_tg_id}) 'Rad etildi' xabari yuborildi.")
    except Exception as e:
        logger.error(f"Foydalanuvchiga (ID: {user_tg_id}) xabar yuborishda xatolik: {e}")


