import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from db.base import AsyncSessionLocal
from db.crud import get_active_courses
from keyboards.reply import get_contact_keyboard, remove_keyboard
from services.ai import get_structured_ai_response
from services.lead import handle_lead_dispatch

logger = logging.getLogger(__name__)
router = Router(name="chat_router")


@router.message(F.text)
async def handle_user_message(message: Message, state: FSMContext) -> None:
    """
    Foydalanuvchi xabariga structured AI orqali javob berish.
    Lid ma'lumotlarini (ism, yosh, telefon, kurs) yig'ish,
    hot lid yoki needs_operator bo'yicha ajratish.
    """
    user_text = message.text.strip()
    if not user_text:
        return

    # Typing indikatorini ko'rsatish
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # FSMContext dan oldingi ma'lumotlarni olish
    data = await state.get_data()
    history = data.get("history", [])

    current_lead_data = {
        "name": data.get("name"),
        "age": data.get("age"),
        "phone": data.get("phone"),
        "course_id": data.get("selected_course_id") or data.get("course_id")
    }

    # Bazadan faol kurslar ro'yxatini olish
    async with AsyncSessionLocal() as session:
        courses = await get_active_courses(session)

    # Structured AI dan javob olish
    ai_result = await get_structured_ai_response(
        history=history,
        user_message=user_text,
        courses=courses,
        current_lead_data=current_lead_data
    )

    reply_text = ai_result.get("reply", "")
    new_name = ai_result.get("name")
    new_age = ai_result.get("age")
    new_phone = ai_result.get("phone")
    new_course_id = ai_result.get("course_id") or current_lead_data["course_id"]
    status = ai_result.get("status", "collecting")

    # FSMContext ni yangilash
    await state.update_data(
        name=new_name,
        age=new_age,
        phone=new_phone,
        course_id=new_course_id,
        status=status
    )

    # Yangilangan lid ma'lumotlari
    updated_lead_data = {
        "name": new_name,
        "age": new_age,
        "phone": new_phone,
        "course_id": new_course_id
    }

    # Suhbat tarixiga qo'shish
    history.append({"role": "user", "text": user_text})
    history.append({"role": "model", "text": reply_text})
    await state.update_data(history=history[-20:])

    # Lidlarni ajratish va kerakli joylarga yuborish
    already_hot_sent = data.get("hot_lead_sent", False)
    already_operator_sent = data.get("operator_need_sent", False)

    if status == "hot" and not already_hot_sent:
        dispatch_res = await handle_lead_dispatch(
            bot=message.bot,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            lead_data=updated_lead_data,
            status="hot",
            last_user_message=user_text
        )
        if dispatch_res.get("dispatched"):
            await state.update_data(hot_lead_sent=True)

    elif status == "needs_operator" and not already_operator_sent:
        unanswered_q = ai_result.get("unanswered_question") or user_text
        ai_summary = ai_result.get("summary") or reply_text

        # Agar ism yoki telefon yo'q bo'lsa, xabarga qo'shimcha qilish
        if not new_name or not new_phone:
            if not new_phone:
                reply_text += "\n\n📞 <i>Operatorimiz siz bilan bog'lana olishi uchun, iltimos, telefon raqamingizni qoldiring:</i>"
            elif not new_name:
                reply_text += "\n\n👤 <i>Operatorimiz sizga qanday murojaat qilishini bilishi uchun ismingizni yozib yuboring:</i>"
        else:
            # Ism va telefon bor - guruhga yuborish
            dispatch_res = await handle_lead_dispatch(
                bot=message.bot,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                lead_data=updated_lead_data,
                status="needs_operator",
                last_user_message=unanswered_q,
                ai_summary=ai_summary
            )
            if dispatch_res.get("dispatched"):
                await state.update_data(operator_need_sent=True)

    # Kontakt tugmasini ko'rsatish shartlari
    reply_markup = None
    lower_reply = reply_text.lower()
    if not new_phone and ("telefon" in lower_reply or "kontakt" in lower_reply or "raqam" in lower_reply):
        reply_markup = get_contact_keyboard()
    elif new_phone:
        reply_markup = remove_keyboard()

    if reply_markup:
        await message.answer(reply_text, reply_markup=reply_markup)
    else:
        await message.answer(reply_text)
