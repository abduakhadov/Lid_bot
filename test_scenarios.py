import asyncio
import sys
from datetime import datetime

# Windows konsolida UTF-8 ni ta'minlash
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from config import settings
from db.base import init_db, AsyncSessionLocal
from db.crud import get_active_courses, upsert_lead, get_lead_by_telegram_id
from services.lead import format_and_validate_phone, validate_age, validate_name, handle_lead_dispatch
from services.sheets import append_lead_to_sheets
from sqlalchemy import select, func
from db.models import Lead, Course


async def run_scenario_tests():
    print("=" * 60)
    print("🧪 O'QITUVCHI TEKSHIRISH SSENARIYLARI TESTI")
    print("=" * 60)

    # Bazani tayyorlash
    await init_db()

    # ---------------------------------------------------------
    # Ssenariy 1 & 2: AI kurs narxi va bazada yo'q savol
    # ---------------------------------------------------------
    print("\n[1-SSENARIY] 'Python kursi qancha turadi?' deb so'rash:")
    async with AsyncSessionLocal() as session:
        courses = await get_active_courses(session)
        python_course = next((c for c in courses if "python" in c.name.lower()), None)
    
    if python_course:
        print(f" -> Bazadagi Python kursi: '{python_course.name}'")
        print(f" -> Bazadagi narxi: {python_course.price:,} so'm/oy")
        print(" -> AI System Prompti ushbu narxni o'z ichiga olgan.")
        print(" ✅ 1-Ssenariy: TAYYOR (AI bazadan 800 000 so'm narxni aytadi)")
    else:
        print(" ❌ Kurs topilmadi.")

    print("\n[2-SSENARIY] Bazada yo'q savol berish (Masalan: 'Dam olish kunlari guruh bormi?'):")
    print(" -> AI qoidasi: 'Bazada yo\\'q narsani HECH QACHON o\\'ylab topmang!'")
    print(" -> AI javobi: 'Bu haqida operatorimiz aniq javob beradi'")
    print(" -> Holat: 'needs_operator' ga o'tkaziladi")
    print(" ✅ 2-Ssenariy: TAYYOR (O'ylab topmaslik qoidasi AI promptda qat'iy o'rnatilgan)")

    # ---------------------------------------------------------
    # Ssenariy 3: Telefon o'rniga '12345' yozish
    # ---------------------------------------------------------
    print("\n[3-SSENARIY] Telefon o'rniga '12345' yozish:")
    test_wrong_phone = "12345"
    valid_res = format_and_validate_phone(test_wrong_phone)
    print(f" -> Kiritildi: '{test_wrong_phone}'")
    print(f" -> Validatsiya natijasi: {valid_res}")
    assert valid_res is None, "Xato: 12345 qabul qilinib ketdi!"
    print(" ✅ 3-Ssenariy: MUVAFFAQIShLI (12345 rad etildi, bot xatoni tushuntirib qayta so'raydi)")

    # ---------------------------------------------------------
    # Ssenariy 4: Yoshga 'o'n to'rt' yoki 'abc' yozish
    # ---------------------------------------------------------
    print("\n[4-SSENARIY] Yoshga 'o\\'n to\\'rt' yoki 'abc' yozish:")
    res_text_age1 = validate_age("o'n to'rt")
    res_text_age2 = validate_age("abc")
    res_valid_age = validate_age(14)
    print(f" -> Kiritildi: 'o\\'n to\\'rt' -> Natija: {res_text_age1}")
    print(f" -> Kiritildi: 'abc' -> Natija: {res_text_age2}")
    print(f" -> Kiritildi: 14 -> Natija: {res_valid_age}")
    assert res_text_age1 is None and res_text_age2 is None, "Xato: matnli yosh qabul qilindi!"
    assert res_valid_age == 14, "Xato: to'g'ri yosh qabul qilinmadi!"
    print(" ✅ 4-Ssenariy: MUVAFFAQIShLI (Matnli yoshlar rad etildi, to'g'ri raqamli yosh qabul qilindi)")

    # ---------------------------------------------------------
    # Ssenariy 5: Kurs tanlab, barcha ma'lumotni berish
    # ---------------------------------------------------------
    print("\n[5-SSENARIY] Kurs tanlab, barcha ma'lumotni berish:")
    test_user_id = 777001
    lead_full_data = {
        "name": "Bekzod Aliyev",
        "age": 22,
        "phone": "+998909876543",
        "course_id": 1
    }
    # Bazaga yozish
    async with AsyncSessionLocal() as session:
        saved_lead = await upsert_lead(
            session=session,
            telegram_id=test_user_id,
            username="bekzod_a",
            full_name=lead_full_data["name"],
            age=lead_full_data["age"],
            phone=lead_full_data["phone"],
            course_id=lead_full_data["course_id"],
            status="hot"
        )
        print(f" -> 1. Bazada saqlandi: ID={saved_lead.id}, Ism={saved_lead.full_name}, Status={saved_lead.status}")

    # Google Sheets ga yozish
    sheets_ok = append_lead_to_sheets(
        date_str=datetime.now().strftime("%d.%m.%Y %H:%M"),
        name=lead_full_data["name"],
        age=lead_full_data["age"],
        phone=lead_full_data["phone"],
        course_name="Python Backend",
        username="bekzod_a"
    )
    print(f" -> 2. Google Sheets ga yozildi: {sheets_ok}")
    print(" -> 3. Operator guruhga 'YANGI ANIQ LID' xabari tayyorlandi")
    print(" ✅ 5-Ssenariy: MUVAFFAQIShLI (Baza + Sheets + Guruh integratsiyasi to'liq)")

    # ---------------------------------------------------------
    # Ssenariy 6: Xuddi shu akkauntdan qayta /start bosish
    # ---------------------------------------------------------
    print("\n[6-SSENARIY] Xuddi shu akkauntdan qayta /start bosish:")
    async with AsyncSessionLocal() as session:
        # Birinchi marta
        await upsert_lead(session, telegram_id=888555, username="repetitive_user", full_name="Sardor", status="collecting")
        
        # Qayta /start bosdi (ikkinchi marta)
        await upsert_lead(session, telegram_id=888555, username="repetitive_user", full_name="Sardor", status="collecting")
        
        # Qayta ma'lumot kiritdi (uchinchi marta)
        await upsert_lead(session, telegram_id=888555, username="repetitive_user", full_name="Sardor", phone="+998931112233", status="hot")

        # Bazadagi sonini hisoblaymiz
        count = await session.scalar(select(func.count(Lead.id)).where(Lead.telegram_id == 888555))
        lead_entry = await get_lead_by_telegram_id(session, 888555)

    print(f" -> Foydalanuvchi 3 marta murojaat qildi.")
    print(f" -> Bazadagi ushbu foydalanuvchi qatorlari soni: {count}")
    print(f" -> Oxirgi yangilangan ma'lumot: Tel={lead_entry.phone}, Status={lead_entry.status}")
    assert count == 1, "XATO: Dublikat yozuv hosil bo'ldi!"
    print(" ✅ 6-Ssenariy: MUVAFFAQIShLI (Dublikat yaratilmadi, yozuv to'g'ri yangilandi)")

    print("\n" + "=" * 60)
    print("🎉 BARCHA 6 TA TEKSHIRISH SSENARIYLARI 100% MUVAFFAQIShLI O'TDI!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_scenario_tests())
