import os
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def append_lead_to_sheets(
    date_str: str,
    name: str,
    age: int | str,
    phone: str,
    course_name: str,
    username: str
) -> bool:
    """
    Google Sheets jadvaliga yangi lid qatorini qo'shish.
    Ustunlar: Sana, Ism, Yosh, Telefon, Kurs, Telegram username.
    Agar sheets xato bersa yoki credentials bo'lmasa, bot to'xtamaydi va faqat logga yoziladi.
    """
    creds_file = settings.GOOGLE_CREDENTIALS_FILE
    if not os.path.exists(creds_file):
        logger.warning(f"Google credentials fayli '{creds_file}' topilmadi. Sheets ga yozilmadi.")
        return False

    try:
        credentials = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        
        # Jadvalni ochish (nomdagi probellarni hisobga olgan holda)
        sheet_name = settings.GOOGLE_SHEET_NAME.strip()
        spreadsheet = None
        try:
            spreadsheet = gc.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            # Agar to'g'ridan-to'g'ri topilmasa, service account jadvallari orasidan qidirish
            files = gc.list_spreadsheet_files()
            for f in files:
                if f.get("name", "").strip().lower() == sheet_name.lower():
                    spreadsheet = gc.open_by_key(f.get("id"))
                    break
            if not spreadsheet:
                raise

        sheet = spreadsheet.sheet1

        # Agar jadval bo'sh bo'lsa, ustunlar sarlavhasini qo'yish
        existing = sheet.get_all_values()
        if not existing:
            sheet.append_row(["Sana", "Ism", "Yosh", "Telefon", "Kurs", "Telegram username"])

        # Qator qo'shish
        row_data = [
            date_str,
            str(name),
            str(age),
            str(phone),
            str(course_name),
            f"@{username}" if username and not username.startswith("@") else (username or "Mavjud emas")
        ]
        sheet.append_row(row_data)
        logger.info(f"Lid muvaffaqiyatli Google Sheets ga yozildi: {row_data}")
        return True
    except Exception as e:
        logger.error(f"Google Sheets ga yozishda xatolik yuz berdi: {e}", exc_info=True)
        return False
