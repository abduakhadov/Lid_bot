# O'quv Markaz uchun AI Lid-Bot — Implementation Plan

## Loyiha haqida

Telegram bot orqali o'quv markaz uchun AI yordamida lid (potensial o'quvchi) yig'uvchi bot.
Bot Gemini AI bilan suhbat quradi, kurslarni ko'rsatadi, ism/yosh/telefon yig'adi va lidlarni
PostgreSQL + Google Sheets + operator guruhga yuboradi.

**Stack:** Python 3.11+, aiogram 3.x, Google Gemini API, PostgreSQL + SQLAlchemy (async), gspread, Docker

---

## Papka tuzilmasi

```
Bot/
├── .env                    # (gitignore)
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── main.py                 # Bot entry point
├── config.py               # Settings (pydantic-settings)
├── db/
│   ├── __init__.py
│   ├── base.py             # SQLAlchemy engine, session
│   ├── models.py           # Course, Lead modellari
│   └── crud.py             # CRUD operatsiyalari
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start handler
│   ├── chat.py             # AI suhbat handler
│   ├── courses.py          # Kurslar callback handler
│   ├── contact.py          # Kontakt yuborish handler
│   └── admin.py            # /add_course, /stats (bonus)
├── keyboards/
│   ├── __init__.py
│   ├── inline.py           # Kurslar inline klaviatura
│   └── reply.py            # Kontakt tugmasi
├── services/
│   ├── __init__.py
│   ├── ai.py               # Gemini API service (structured output)
│   ├── sheets.py           # Google Sheets service
│   ├── lead.py             # Lid yaratish/yangilash logikasi
│   └── notifier.py         # Operator guruhga xabar yuborish
├── middlewares/
│   ├── __init__.py
│   └── throttle.py         # Rate limit (bonus)
└── credentials.json        # (gitignore) Google Service Account
```

---

## Proposed Changes

### 1. Loyiha asosi

#### [NEW] `.env.example`
Bot tokeni, Gemini API key, DB URL, operator guruh ID, Google Sheets ID

#### [NEW] `.gitignore`
`.env`, `credentials.json` va `__pycache__` ni ignore qiladi

#### [NEW] `requirements.txt`
```
aiogram==3.x
google-generativeai
sqlalchemy[asyncio]
asyncpg
gspread
google-auth
python-dotenv
pydantic-settings
```

#### [NEW] `config.py`
pydantic-settings orqali barcha env o'zgaruvchilarni yuklaydi

---

### 2. Ma'lumotlar bazasi

#### [NEW] `db/base.py`
- Async SQLAlchemy engine (asyncpg driver)
- `get_session` dependency

#### [NEW] `db/models.py`
```python
class Course:
    id, name, description, price, duration, age_min, age_max, is_active

class Lead:
    id, telegram_id, username, full_name, age, phone, course_id, status, created_at
```

#### [NEW] `db/crud.py`
- `get_courses()` — faol kurslar
- `upsert_lead()` — dublikatsiz saqlash (ON CONFLICT UPDATE)
- `get_stats()` — bugungi lidlar, kurs statistikasi
- `get_lead_by_telegram_id()`

---

### 3. AI Service

#### [NEW] `services/ai.py`
- Gemini `gemini-2.0-flash` modeli
- System prompt: kurslar ro'yxati dinamik o'qiladi bazadan
- Structured output (JSON schema):
```json
{
  "reply": "string",
  "name": "string|null",
  "age": "int|null",
  "phone": "string|null",
  "course_id": "int|null",
  "status": "collecting|hot|needs_operator"
}
```
- Suhbat tarixi — `FSMContext` da saqlanadi (oxirgi 10 xabar)
- API xatoda — foydalanuvchiga xato xabari + `needs_operator` statusi

---

### 4. Keyboards

#### [NEW] `keyboards/inline.py`
- Kurslar inline tugmalari: `course_{id}` callback data
- Operator guruhda "Qabul qildim" tugmasi (bonus)

#### [NEW] `keyboards/reply.py`
- "📞 Kontakt yuborish" tugmasi (ReplyKeyboardMarkup)

---

### 5. Handlers

#### [NEW] `handlers/start.py`
- `/start` → salomlashadi, FSM state ni tozalaydi, suhbatni boshlaydi

#### [NEW] `handlers/chat.py`
- Har qanday matn → AI ga yuboradi → structured output parse qiladi
- `collecting` → davom ettiradi
- `hot` → lidni bazaga yozadi → Sheets → operator guruhga
- `needs_operator` → ism+telefon bor bo'lsa guruhga yuboradi

#### [NEW] `handlers/courses.py`
- `course_{id}` callback → kurs tanlangan, AI ga bildiriladi

#### [NEW] `handlers/contact.py`
- Kontakt tugmasi bosilganda telefon raqamni oladi va AI ga uzatadi

#### [NEW] `handlers/admin.py` (bonus)
- `/add_course` — kurs qo'shish (step-by-step FSM)
- `/stats` — bugungi lidlar soni va eng ko'p tanlangan kurs

---

### 6. Services

#### [NEW] `services/sheets.py`
- Google Sheets ga qator qo'shish
- Xato bo'lsa — log yozadi, bot to'xtamaydi

#### [NEW] `services/notifier.py`
- Operator guruhga formatlangan xabar yuboradi
- "Aniq lid" vs "Operator kerak" formatlari

#### [NEW] `services/lead.py`
- Lid yaratish/yangilash orkestratsiyasi

---

### 7. Middlewares

#### [NEW] `middlewares/throttle.py` (bonus)
- Foydalanuvchi haddan ziyod xabar yubormesligi uchun rate limit
- Redis yoki in-memory dict bilan

---

### 8. Docker (bonus)

#### [NEW] `Dockerfile`
#### [NEW] `docker-compose.yml`
- `bot` + `postgres` servislar
- Volume, healthcheck

---

### 9. Hujjatlar

#### [NEW] `README.md`
- Loyiha tavsifi
- O'rnatish qadamlari
- Ishga tushirish (oddiy + Docker)

---

## Verification Plan

### Tekshirish ssenariylari (task.md bo'yicha)
1. "Python kursi qancha turadi?" → AI bazadagi narxni aytadi
2. Bazada yo'q savol → "operator kerak" bo'lib boradi
3. Telefon o'rniga "12345" → bot qayta so'raydi
4. Yoshga "o'n to'rt" yoki "abc" → to'g'ri ishlov
5. Kurs tanlab, to'liq ma'lumot → lid bazada + Sheets + guruhda
6. Qayta /start → dublikat yaratilmaydi

### Manual Verification
- Bot ishga tushishi va `/start` javobi
- AI javob sifati
- Google Sheets da qator paydo bo'lishi
- Operator guruhda xabar ko'rinishi
- Docker bilan ishga tushirish

---

## Baholash bo'yicha maqsad: **100/100 + bonus**
