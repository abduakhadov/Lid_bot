import json
import logging
import re
from typing import Sequence, Any
import google.generativeai as genai
from config import settings
from db.models import Course
from services.lead import format_and_validate_phone, validate_age, validate_name

logger = logging.getLogger(__name__)

# Gemini API ni sozlash
genai.configure(api_key=settings.GEMINI_API_KEY)


def build_system_prompt(courses: Sequence[Course], current_lead_data: dict[str, Any]) -> str:
    """Kurslar va hozirgi lid holati asosida structured output system prompt shakllantirish"""
    courses_info = []
    for c in courses:
        price_str = f"{c.price:,}".replace(",", " ") + " so'm/oy" if c.price else "Ko'rsatilmagan"
        courses_info.append(
            f"• ID: {c.id} | Kurs: {c.name} | Narxi: {price_str} | Davomiyligi: {c.duration} | "
            f"Yosh chegarasi: {c.age_min}-{c.age_max} yosh | Tavsif: {c.description}"
        )
    courses_text = "\n".join(courses_info) if courses_info else "Hozircha kurslar ro'yxati mavjud emas."

    # Hozirgacha yig'ilgan ma'lumotlar
    c_name = current_lead_data.get("name") or "noma'lum"
    c_age = current_lead_data.get("age") or "noma'lum"
    c_phone = current_lead_data.get("phone") or "noma'lum"
    c_course_id = current_lead_data.get("course_id") or "noma'lum"

    return f"""Siz o'quv markazining sun'iy intellektga ega, do'stona va professional maslahatchisisiz.
Vazifangiz:
1. Kurslar haqidagi savollarga javob berish.
2. O'quvchilar bilan jonli va tabiiy suhbat qurish (hech qachon rasmiy anketa kabi quruq savol-javob qilmang!).
3. Kursga yozilish niyati bo'lganda tabiiy tarzda 3 ta ma'lumotni so'rab olish:
   - Ism (kamida 2 harf)
   - Yosh (faqat son, 5 dan 60 gacha)
   - Telefon raqami (+998XXXXXXXXX formatida)

O'QUV MARKAZIDAGI MAVJUD KURSLAR:
{courses_text}

HOZIRGACHA FOYDALANUVCHIDAN YIG'ILGAN MA'LUMOTLAR:
- Ism: {c_name}
- Yosh: {c_age}
- Telefon: {c_phone}
- Tanlangan kurs ID: {c_course_id}

MUHIM VALIDATSIYA VA QOIDALAR:
1. Bazada yo'q narsani HECH QACHON o'ylab topmang! Agar dars jadvali, haftaning qaysi kunlari, vaqtlari yoki ro'yxatda yo'q kurslar so'ralsa, "Bu haqida operatorimiz aniq javob beradi" deb ayting va statusni "needs_operator" qiling.
2. Agar foydalanuvchi yoshini so'z bilan ("o'n to'rt", "yigirma") yoki matn ("abc") bilan yozsa, xatoni xushmuomala tushuntirib, faqat raqamda (masalan: 14) kiritishini so'rang va "age": null qoldiring.
3. Agar telefon raqamini noto'g'ri kiritsa (masalan: "12345"), xatoni tushuntirib, to'g'ri telefon raqamini kiritishini so'rang va "phone": null qoldiring.
4. Javobingizni FAQAT va FAQAT quyidagi JSON formatda qaytaring (boshqa hech qanday ortiqcha matnsiz):

{{
  "reply": "Foydalanuvchiga ko'rsatiladigan o'zbek tilidagi xushmuomala javob matni",
  "name": "foydalanuvchi ismi yoki null",
  "age": 14,
  "phone": "+998901234567 yoki null",
  "course_id": 1,
  "status": "collecting",
  "unanswered_question": "agar status needs_operator bo'lsa javobsiz qolgan savol matni, aks holda null",
  "summary": "agar status needs_operator bo'lsa suhbat haqida 1-2 gaplik xulosa, aks holda null"
}}

status qiymatlari:
- "collecting": Ma'lumotlar yig'ilmoqda (hali ism, yosh, telefon yoki kurs to'liq emas).
- "hot": Kurs tanlangan VA ism, yosh, telefon to'liq va to'g'ri bo'ldi (aniq lid).
- "needs_operator": AI aniq javob bera olmadi yoki ma'lumot bazada yo'q yoki foydalanuvchi operator bilan bog'lanishni xohladi. Bu holatda "unanswered_question" va "summary" maydonlarini albatta to'ldiring!
"""


def extract_json_from_text(text: str) -> dict[str, Any] | None:
    """Matn ichidan JSON obyektni xavfsiz ajratib olish"""
    try:
        # To'g'ridan-to'g'ri JSON deb ko'rish
        return json.loads(text)
    except Exception:
        pass

    # Markdown ```json ... ``` blokini qidirish
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Shunchaki birinchi { va oxirgi } oralig'ini qidirish
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None


async def get_structured_ai_response(
    history: list[dict[str, str]],
    user_message: str,
    courses: Sequence[Course],
    current_lead_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Gemini modeliga murojaat qilib, structured JSON ma'lumot oladi.
    """
    try:
        system_instruction = build_system_prompt(courses, current_lead_data)
        
        # JSON rejimida Gemini GenerativeModel
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_instruction,
            generation_config={"response_mime_type": "application/json"}
        )

        recent_history = history[-10:] if len(history) > 10 else history
        gemini_history = []
        for msg in recent_history:
            role = "user" if msg.get("role") == "user" else "model"
            text = msg.get("text", "")
            if text:
                gemini_history.append({"role": role, "parts": [text]})

        chat = model.start_chat(history=gemini_history)
        response = await chat.send_message_async(user_message)
        raw_text = response.text.strip()
        
        parsed = extract_json_from_text(raw_text)
        if parsed and isinstance(parsed, dict) and "reply" in parsed:
            # Qiymatlarni tekshirish va tozalash
            name = validate_name(parsed.get("name")) or current_lead_data.get("name")
            age = validate_age(parsed.get("age")) or current_lead_data.get("age")
            phone = format_and_validate_phone(str(parsed.get("phone") or "")) or current_lead_data.get("phone")
            course_id = parsed.get("course_id") or current_lead_data.get("course_id")
            status = parsed.get("status", "collecting")

            # Agar hamma ma'lumotlar bor bo'lsa, avtomatik "hot" ga o'tkazish
            if name and age and phone and course_id and status != "needs_operator":
                status = "hot"

            return {
                "reply": parsed.get("reply", ""),
                "name": name,
                "age": age,
                "phone": phone,
                "course_id": course_id,
                "status": status,
                "unanswered_question": parsed.get("unanswered_question"),
                "summary": parsed.get("summary")
            }

        # Agar JSON bo'lmay qolsa, oddiy matn deb olamiz
        return {
            "reply": raw_text,
            "name": current_lead_data.get("name"),
            "age": current_lead_data.get("age"),
            "phone": current_lead_data.get("phone"),
            "course_id": current_lead_data.get("course_id"),
            "status": "collecting",
            "unanswered_question": None,
            "summary": None
        }
    except Exception as e:
        logger.error(f"Gemini Structured AI xatoligi: {e}", exc_info=True)
        return {
            "reply": (
                "Hozirda tizimda texnik uzilish kuzatildi. "
                "Savolingiz yoki ro'yxatdan o'tishingiz yuzasidan operatorimiz tez orada siz bilan bog'lanadi."
            ),
            "name": current_lead_data.get("name"),
            "age": current_lead_data.get("age"),
            "phone": current_lead_data.get("phone"),
            "course_id": current_lead_data.get("course_id"),
            "status": "needs_operator"
        }
