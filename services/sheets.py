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
    username: str,
    status: str = "Yangi (Kutilmoqda)"
) -> bool:
    """
    Google Sheets jadvaliga yangi lid qatorini qo'shish.
    Ustunlar: Sana, Ism, Yosh, Telefon, Kurs, Telegram username, Status.
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
            sheet.append_row(["Sana", "Ism", "Yosh", "Telefon", "Kurs", "Telegram username", "Status"])
        elif len(existing[0]) < 7:
            sheet.update_cell(1, 7, "Status")

        # Qator qo'shish
        username_str = f"@{username}" if username and not username.startswith("@") else (username or "Mavjud emas")
        row_data = [
            date_str,
            str(name),
            str(age),
            str(phone),
            str(course_name),
            username_str,
            status
        ]
        sheet.append_row(row_data)
        logger.info(f"Lid muvaffaqiyatli Google Sheets ga yozildi: {row_data}")
        return True
    except Exception as e:
        logger.error(f"Google Sheets ga yozishda xatolik yuz berdi: {e}", exc_info=True)
        return False


def update_lead_status_in_sheets(phone: str, new_status: str) -> bool:
    """
    Telefon raqami bo'yicha Google Sheets dagi lid statusini yangilash.
    """
    creds_file = settings.GOOGLE_CREDENTIALS_FILE
    if not os.path.exists(creds_file):
        return False

    try:
        credentials = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        sheet_name = settings.GOOGLE_SHEET_NAME.strip()
        spreadsheet = None
        try:
            spreadsheet = gc.open(sheet_name)
        except Exception:
            files = gc.list_spreadsheet_files()
            for f in files:
                if f.get("name", "").strip().lower() == sheet_name.lower():
                    spreadsheet = gc.open_by_key(f.get("id"))
                    break

        if not spreadsheet:
            return False

        sheet = spreadsheet.sheet1
        cell = sheet.find(phone)
        if cell:
            sheet.update_cell(cell.row, 7, new_status)
            logger.info(f"Sheets da lid statusi yangilandi (Qator {cell.row}: {new_status})")
            return True
    except Exception as e:
        logger.error(f"Google Sheets statusini yangilashda xatolik: {e}")
    return False

