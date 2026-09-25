import asyncio
import json
import logging
import re
from typing import Sequence, Any

from google import genai
from google.genai import types

from config import settings
from db.models import Course
from services.lead import format_and_validate_phone, validate_age, validate_name

logger = logging.getLogger(__name__)

# Yangi google.genai SDK bilan client yaratish
_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Zaxira modellar ro'yxati (tezdan sekinroqqa) — haqiqiy API nomlar
MODELS_TO_TRY = [
    "gemini-flash-lite-latest",  # Eng tez — "latest" alias, har doim eng yangi lite
    "gemini-3.5-flash-lite",     # Tez, arzon
    "gemini-flash-latest",       # Tez full flash
    "gemini-3.5-flash",          # Zaxira
]

# Har bir model urinishiga maksimal vaqt (sekund)
MODEL_TIMEOUT = 8


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
1. Bazada yo'q narsani HECH QACHON o'ylab topmang! Agar dars jadvali, haftaning qaysi kunlari, vaqtlari yoki ro'yxatda yo'q kurslar so'ralsa, \"Bu haqida operatorimiz aniq javob beradi\" deb ayting va statusni \"needs_operator\" qiling.
2. Agar foydalanuvchi yoshini so'z bilan (\"o'n to'rt\", \"yigirma\") yoki matn (\"abc\") bilan yozsa, xatoni xushmuomala tushuntirib, faqat raqamda (masalan: 14) kiritishini so'rang va \"age\": null qoldiring.
3. Agar telefon raqamini noto'g'ri kiritsa (masalan: \"12345\"), xatoni tushuntirib, to'g'ri telefon raqamini kiritishini so'rang va \"phone\": null qoldiring.
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
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

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
    Yangi google.genai SDK orqali structured JSON javob oladi.
    Model kvotasi tugasa zaxira modellar orqali avtomatik qayta urinadi.
    """
    # Faqat oxirgi 10 ta xabar (task.md talabi)
    recent_history = history[-10:] if len(history) > 10 else history

    # Suhbat tarixini yangi SDK formatiga o'tkazish
    gemini_history = []
    for msg in recent_history:
        role = "user" if msg.get("role") == "user" else "model"
        text = msg.get("text", "")
        if text:
            gemini_history.append(
                types.Content(role=role, parts=[types.Part(text=text)])
            )

    system_instruction = build_system_prompt(courses, current_lead_data)

    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            logger.debug(f"Model sinashmoqda: {model_name}")

            # Suhbat tarixi + yangi xabar birlashtirish
            all_contents = gemini_history + [
                types.Content(role="user", parts=[types.Part(text=user_message)])
            ]

            async with asyncio.timeout(MODEL_TIMEOUT):
                response = await _client.aio.models.generate_content(
                    model=model_name,
                    contents=all_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.3,
                        max_output_tokens=400,  # Kamroq token = tezroq javob
                    ),
                )

            raw_text = response.text.strip() if response.text else ""
            if not raw_text:
                continue

            parsed = extract_json_from_text(raw_text)
            if parsed and isinstance(parsed, dict) and "reply" in parsed:
                name = validate_name(parsed.get("name")) or current_lead_data.get("name")
                age = validate_age(parsed.get("age")) or current_lead_data.get("age")
                phone = format_and_validate_phone(str(parsed.get("phone") or "")) or current_lead_data.get("phone")
                course_id = parsed.get("course_id") or current_lead_data.get("course_id")
                status = parsed.get("status", "collecting")

                if name and age and phone and course_id and status != "needs_operator":
                    status = "hot"

                logger.info(f"AI javob olindi: model={model_name}, status={status}")
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

            # JSON bo'lmasa ham raw text qaytarish
            if raw_text:
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

        except TimeoutError:
            logger.warning(f"Model '{model_name}' {MODEL_TIMEOUT}s dan oshdi, keyingi modelga o'tilmoqda...")
            continue
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if any(x in err_str for x in ["429", "quota", "rate", "503", "unavailable", "overloaded"]):
                logger.warning(f"Model '{model_name}' kvota/server xatosi, zaxira modelga o'tilmoqda: {e}")
                continue
            else:
                logger.warning(f"Model '{model_name}' xatosi, zaxira modelga o'tilmoqda: {e}")
                continue

    logger.error(f"Barcha modellar xatolik berdi. So'nggi xatolik: {last_error}", exc_info=True)
    return {
        "reply": (
            "Hozirda tizimda texnik uzilish kuzatildi. "
            "Savolingiz yoki ro'yxatdan o'tishingiz yuzasidan operatorimiz tez orada siz bilan bog'lanadi."
        ),
        "name": current_lead_data.get("name"),
        "age": current_lead_data.get("age"),
        "phone": current_lead_data.get("phone"),
        "course_id": current_lead_data.get("course_id"),
        "status": "needs_operator",
        "unanswered_question": user_message,
        "summary": "AI xizmatida texnik xatolik yuz berdi."
    }
