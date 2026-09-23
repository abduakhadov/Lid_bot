import re
import logging
from datetime import datetime
from typing import Any
from aiogram import Bot
from db.base import AsyncSessionLocal
from db.crud import upsert_lead, get_course_by_id
from services.sheets import append_lead_to_sheets
from services.notifier import send_hot_lead_notification, send_needs_operator_notification

logger = logging.getLogger(__name__)


def format_and_validate_phone(phone_input: str) -> str | None:
    """
    Telefon raqamini tekshirish va +998XXXXXXXXX formatiga keltirish.
    To'g'ri bo'lsa formatlangan telefon raqamini, noto'g'ri bo'lsa None qaytaradi.
    """
    if not phone_input:
        return None

    digits = re.sub(r"\D", "", phone_input.strip())

    if len(digits) == 12 and digits.startswith("998"):
        return f"+{digits}"

    if len(digits) == 9:
        return f"+998{digits}"

    return None


def validate_age(age_input: Any) -> int | None:
    """
    Yoshni tekshirish: faqat son bo'lishi va 5 dan 60 gacha bo'lishi kerak.
    """
    if age_input is None:
        return None

    if isinstance(age_input, int):
        if 5 <= age_input <= 60:
            return age_input
        return None

    if isinstance(age_input, str):
        val = age_input.strip()
        if val.isdigit():
            num = int(val)
            if 5 <= num <= 60:
                return num
        return None

    return None


def validate_name(name_input: str | None) -> str | None:
    """
    Ismni tekshirish: bo'sh bo'lmasligi, kamida 2 ta harf bo'lishi kerak.
    """
    if not name_input:
        return None

    cleaned = name_input.strip()
    letters = re.findall(r"[a-zA-Zа-яА-ЯёЁo'g'shchO'G'SHCH]", cleaned)
    if len(letters) >= 2:
        return cleaned

    return None


async def handle_lead_dispatch(
    bot: Bot,
    telegram_id: int,
    username: str | None,
    lead_data: dict[str, Any],
    status: str,
    last_user_message: str = "",
    ai_summary: str = ""
) -> dict[str, Any]:
    """
    Lidlarni ajratish va kerakli manzillarga yuborish:
    1. Aniq lid (hot): Kurs tanlangan va ism, yosh, telefon to'liq bo'lsa
       -> Baza + Google Sheets + Operator guruhga bir vaqtda yuboriladi.
    2. Operator kerak (needs_operator):
       -> Faqat ism va telefon mavjud bo'lganda operator guruhga yuboriladi.
    """
    name = lead_data.get("name")
    age = lead_data.get("age")
    phone = lead_data.get("phone")
    course_id = lead_data.get("course_id")

    # 1. ANIQ LID (HOT)
    is_hot = bool(course_id and name and age and phone and status == "hot")

    if is_hot:
        course_name = "Noma'lum kurs"
        async with AsyncSessionLocal() as session:
            course = await get_course_by_id(session, int(course_id))
            if course:
                course_name = course.name

            # 1. Bazaga yozish (dublikat bo'lmasdan yangilanadi)
            db_lead = await upsert_lead(
                session=session,
                telegram_id=telegram_id,
                username=username,
                full_name=name,
                age=int(age),
                phone=phone,
                course_id=int(course_id),
                status="hot"
            )
            lead_db_id = db_lead.id

        now = datetime.now()
        date_str = now.strftime("%d.%m.%Y %H:%M")

        # 2. Google Sheets ga yozish
        append_lead_to_sheets(
            date_str=date_str,
            name=name,
            age=age,
            phone=phone,
            course_name=course_name,
            username=username or ""
        )

        # 3. Operator guruhga yuborish
        await send_hot_lead_notification(
            bot=bot,
            lead_id=lead_db_id,
            full_name=name,
            age=age,
            phone=phone,
            course_name=course_name,
            username=username,
            created_at=now
        )

        return {"dispatched": True, "type": "hot"}

    # 2. OPERATOR KERAK (NEEDS_OPERATOR)
    if status == "needs_operator":
        # Kamida ism va telefon olingan bo'lishi shart!
        if name and phone:
            async with AsyncSessionLocal() as session:
                db_lead = await upsert_lead(
                    session=session,
                    telegram_id=telegram_id,
                    username=username,
                    full_name=name,
                    age=int(age) if age else None,
                    phone=phone,
                    course_id=int(course_id) if course_id else None,
                    status="needs_operator"
                )
                lead_db_id = db_lead.id

            await send_needs_operator_notification(
                bot=bot,
                lead_id=lead_db_id,
                full_name=name,
                phone=phone,
                unanswered_question=last_user_message or "Aniqlanmagan savol",
                summary=ai_summary or "Foydalanuvchi operator bilan bog'lanishni so'radi.",
                username=username
            )
            return {"dispatched": True, "type": "needs_operator"}
        else:
            # Agar ism yoki telefon hali yo'q bo'lsa, yuborilmaydi (so'rab olinishi kerak)
            return {"dispatched": False, "type": "waiting_contact_for_operator"}

    # COLLECTING holatida shunchaki bazani yangilab qo'yish mumkin
    if name or phone or course_id:
        async with AsyncSessionLocal() as session:
            await upsert_lead(
                session=session,
                telegram_id=telegram_id,
                username=username,
                full_name=name,
                age=int(age) if age else None,
                phone=phone,
                course_id=int(course_id) if course_id else None,
                status="collecting"
            )

    return {"dispatched": False, "type": "collecting"}
