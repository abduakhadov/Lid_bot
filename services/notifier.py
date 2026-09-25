import logging
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings

logger = logging.getLogger(__name__)


def get_accept_lead_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    """Operator/Admin uchun 'Qabul qilish' va 'Rad etish' tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_lead:{lead_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_lead:{lead_id}"),
            ]
        ]
    )



def get_target_chat_ids() -> list[int]:
    """Xabar yuborilishi kerak bo'lgan barcha chat/user ID larni yig'ish"""
    targets: list[int] = []
    if settings.OPERATOR_GROUP_ID:
        targets.append(settings.OPERATOR_GROUP_ID)
    for admin_id in settings.admin_id_list:
        if admin_id not in targets:
            targets.append(admin_id)
    return targets


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
    Adminlarga (va Operator guruhiga) 'YANGI ANIQ LID' xabarini yuborish.
    """
    targets = get_target_chat_ids()
    if not targets:
        logger.warning("Na OPERATOR_GROUP_ID, na ADMIN_IDS sozlanmagan. Xabar yuborilmadi.")
        return False

    date_str = (created_at or datetime.now()).strftime("%d.%m.%Y %H:%M")
    tg_user = f"@{username}" if username else "Mavjud emas"

    message_text = (
        "🔥 <b>YANGI ANIQ LID REGISTRATSIYASI</b>\n\n"
        f"<b>Ism:</b>      {full_name}\n"
        f"<b>Yosh:</b>     {age}\n"
        f"<b>Tel:</b>      {phone}\n"
        f"<b>Kurs:</b>     {course_name}\n"
        f"<b>Telegram:</b> {tg_user}\n"
        f"<b>Vaqt:</b>     {date_str}"
    )

    success = False
    for chat_id in targets:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=get_accept_lead_keyboard(lead_id)
            )
            success = True
            logger.info(f"Yangi aniq lid xabari yuborildi (Lead ID: {lead_id}, Chat ID: {chat_id})")
        except Exception as e:
            logger.error(f"Xabar yuborishda xatolik (Chat ID: {chat_id}): {e}")
    return success


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
    Adminlarga (va Operator guruhiga) 'OPERATOR YORDAMI KERAK' xabarini yuborish.
    """
    targets = get_target_chat_ids()
    if not targets:
        logger.warning("Na OPERATOR_GROUP_ID, na ADMIN_IDS sozlanmagan. Xabar yuborilmadi.")
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

    success = False
    for chat_id in targets:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=get_accept_lead_keyboard(lead_id)
            )
            success = True
            logger.info(f"Operator yordami so'rovi yuborildi (Lead ID: {lead_id}, Chat ID: {chat_id})")
        except Exception as e:
            logger.error(f"Xabar yuborishda xatolik (Chat ID: {chat_id}): {e}")
    return success

