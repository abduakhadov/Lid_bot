from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqamni yuborish uchun reply tugma"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Klaviaturani olib tashlash"""
    return ReplyKeyboardRemove()
