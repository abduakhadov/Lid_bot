from typing import Sequence
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import Course


def get_courses_keyboard(courses: Sequence[Course]) -> InlineKeyboardMarkup:
    """
    Kurslarni inline tugmalar ko'rinishida chiqarish.
    Har bir tugmada: nomi, davomiyligi, narxi, yosh chegarasi ko'rsatiladi.
    """
    builder = InlineKeyboardBuilder()

    for course in courses:
        price_str = f"{course.price:,}".replace(",", " ") + " so'm" if course.price else "Narxi kelishiladi"
        age_str = f"{course.age_min}-{course.age_max} yosh"
        
        # Tugma matni: Nomi | Davomiyligi | Narxi | Yoshi
        btn_text = f"📚 {course.name} | {course.duration} | {price_str} | {age_str}"
        
        builder.button(
            text=btn_text,
            callback_data=f"select_course:{course.id}"
        )

    # Har bir kurs alohida qatorda
    builder.adjust(1)
    return builder.as_markup()


def get_course_detail_keyboard(course_id: int) -> InlineKeyboardMarkup:
    """Kurs tanlangandan keyin qayta kurslarni ko'rish tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Boshqa kursni tanlash", callback_data="show_all_courses")
    return builder.as_markup()
