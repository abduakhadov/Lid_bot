import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db.crud import get_active_courses
from keyboards.reply import remove_keyboard
from services.lead import format_and_validate_phone, handle_lead_dispatch
from services.ai import get_structured_ai_response

logger = logging.getLogger(__name__)
router = Router(name="contact_router")


@router.message(F.contact)
async def handle_contact_received(message: Message, state: FSMContext) -> None:
    """
    Foydalanuvchi 'Kontakt yuborish' tugmasi orqali telefon raqamini yuborganda.
    """
    if not message.contact:
        return

    raw_phone = message.contact.phone_number
    phone = format_and_validate_phone(raw_phone)

    if not phone:
        await message.answer(
            "Kechirasiz, kontakt formatini aniqlab bo'lmadi. "
            "Iltimos, telefon raqamingizni +998901234567 shaklida yozib yuboring.",
            reply_markup=remove_keyboard()
        )
        return

    # FSM context ma'lumotlarini olish
    data = await state.get_data()
    history = data.get("history", [])

    lead_data = {
        "name": data.get("name") or (message.from_user.full_name if message.from_user else None),
        "age": data.get("age"),
        "phone": phone,
        "course_id": data.get("selected_course_id") or data.get("course_id")
    }

    await state.update_data(phone=phone)

    # Bazadan kurslarni olish
    async with AsyncSessionLocal() as session:
        courses = await get_active_courses(session)

    contact_msg = f"Telefon raqamim: {phone}"
    ai_result = await get_structured_ai_response(
        history=history,
        user_message=contact_msg,
        courses=courses,
        current_lead_data=lead_data
    )

    new_name = ai_result.get("name") or lead_data["name"]
    new_age = ai_result.get("age") or lead_data["age"]
    new_course_id = ai_result.get("course_id") or lead_data["course_id"]
    status = ai_result.get("status", "collecting")

    # State ni AI qaytargan ma'lumotlar bilan yangilash
    await state.update_data(
        name=new_name,
        age=new_age,
        phone=phone,
        course_id=new_course_id,
        status=status
    )

    # Tarixni yangilash
    history.append({"role": "user", "text": contact_msg})
    history.append({"role": "model", "text": ai_result.get("reply", "")})
    await state.update_data(history=history[-20:])

    # Lidlarni ajratish
    updated_lead_data = {
        "name": new_name,
        "age": new_age,
        "phone": phone,
        "course_id": new_course_id
    }

    already_hot_sent = data.get("hot_lead_sent", False)
    already_operator_sent = data.get("operator_need_sent", False)

    if status == "hot" and not already_hot_sent:
        dispatch_res = await handle_lead_dispatch(
            bot=message.bot,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            lead_data=updated_lead_data,
            status="hot",
            last_user_message=contact_msg
        )
        if dispatch_res.get("dispatched"):
            await state.update_data(hot_lead_sent=True)

    elif status == "needs_operator" and not already_operator_sent and new_name and phone:
        dispatch_res = await handle_lead_dispatch(
            bot=message.bot,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            lead_data=updated_lead_data,
            status="needs_operator",
            last_user_message=contact_msg,
            ai_summary=ai_result.get("reply", "")
        )
        if dispatch_res.get("dispatched"):
            await state.update_data(operator_need_sent=True)

    # Javobni qaytarish va tugmani yashirish
    await message.answer(ai_result.get("reply", "Rahmat, raqamingiz qabul qilindi!"), reply_markup=remove_keyboard())
