import logging
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings

logger = logging.getLogger(__name__)


def get_accept_lead_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    """Operator uchun 'Qabul qildim' tugmasi (Bonus vazifa)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qabul qildim", callback_data=f"accept_lead:{lead_id}")]
        ]
    )


async def send_hot_lead_notification(
    bot: Bot,
    lead_id: int,
    full_name: str,
    age: int | str,
    phone: str,
    course_name: str,
    username: str | None,
    created_at: datetime | None = None
) -> bool:
    """
    Operator guruhiga 'YANGI ANIQ LID' xabarini yuborish.
    """
    if not settings.OPERATOR_GROUP_ID:
        logger.warning("OPERATOR_GROUP_ID sozlanmagan. Operator guruhga xabar yuborilmadi.")
        return False

    date_str = (created_at or datetime.now()).strftime("%d.%m.%Y %H:%M")
    tg_user = f"@{username}" if username else "Mavjud emas"

    message_text = (
        "🔥 <b>YANGI ANIQ LID</b>\n\n"
        f"<b>Ism:</b>      {full_name}\n"
        f"<b>Yosh:</b>     {age}\n"
        f"<b>Tel:</b>      {phone}\n"
        f"<b>Kurs:</b>     {course_name}\n"
        f"<b>Telegram:</b> {tg_user}\n"
        f"<b>Vaqt:</b>     {date_str}"
    )

    try:
        await bot.send_message(
            chat_id=settings.OPERATOR_GROUP_ID,
            text=message_text,
            reply_markup=get_accept_lead_keyboard(lead_id)
        )
        logger.info(f"Yangi aniq lid operator guruhiga yuborildi (Lead ID: {lead_id})")
        return True
    except Exception as e:
        logger.error(f"Operator guruhiga xabar yuborishda xatolik: {e}")
        return False


async def send_needs_operator_notification(
    bot: Bot,
    lead_id: int,
    full_name: str,
    phone: str,
    unanswered_question: str,
    summary: str,
    username: str | None
) -> bool:
    """
    Operator guruhiga 'OPERATOR YORDAMI KERAK' xabarini yuborish.
    """
    if not settings.OPERATOR_GROUP_ID:
        logger.warning("OPERATOR_GROUP_ID sozlanmagan. Operator guruhga xabar yuborilmadi.")
        return False

    tg_user = f"@{username}" if username else "Mavjud emas"

    message_text = (
        "⚠️ <b>OPERATOR YORDAMI KERAK</b>\n\n"
        f"<b>Ism:</b>             {full_name}\n"
        f"<b>Tel:</b>             {phone}\n"
        f"<b>Telegram:</b>        {tg_user}\n"
        f"<b>Javobsiz savol:</b>  {unanswered_question}\n"
        f"<b>Suhbat xulosasi:</b> {summary}"
    )

    try:
        await bot.send_message(
            chat_id=settings.OPERATOR_GROUP_ID,
            text=message_text,
            reply_markup=get_accept_lead_keyboard(lead_id)
        )
        logger.info(f"Operator yordami so'rovi guruhga yuborildi (Lead ID: {lead_id})")
        return True
    except Exception as e:
        logger.error(f"Operator guruhiga xabar yuborishda xatolik: {e}")
        return False
