# 🎓 O'quv Markaz uchun AI Lid-Bot

Telegram orqali yangi o'quvchilarni jalb qilish, ularning savollariga Google Gemini sun'iy intellekti yordamida jonli va tabiiy javob berish, markaz kurslarini ko'rsatish hamda operatorlar uchun saralangan lidlar (leads) yig'ishga mo'ljallangan aqlli bot.

---

## 🚀 Asosiy Imkoniyatlar

1. **🤖 Gemini AI bilan jonli suhbat:**
   - Kurslar haqidagi ma'lumotlar bazadan dinamik olinib, AI system promptiga uzatiladi (kodga qattiq yozilmagan).
   - **O'ylab topmaslik (No Hallucination):** Bazada yo'q ma'lumotlar (aniq jadval, dars kunlari yoki mavjud bo'lmagan kurslar) so'ralsa, AI *"Operatorimiz aniq javob beradi"* deb javob beradi.
   - **Suhbat tarixi:** Kamida oxirgi 10 ta xabar eslab turiladi.
   - **Model fallback:** Birinchi model ishlamasa, avtomatik ravishda zaxira modelga o'tadi.

2. **📚 Kurslarni inline tugmalar orqali ko'rsatish:**
   - Kurs nomi, davomiyligi, narxi va yosh chegarasi aniq ko'rsatiladi.
   - Tugma orqali kurs tanlash yoki suhbatda tabiiy tilda (masalan, *"Python ga yozilmoqchiman"*) aytilsa ham AI buni avtomatik tushunadi.

3. **📋 Structured Output va Lid yig'ish:**
   - AI javobi qat'iy structured JSON formatida tahlil qilinadi (`name`, `age`, `phone`, `course_id`, `status`).
   - Maydonlar validatsiyasi:
     - **Ism:** Kamida 2 harfdan iborat bo'lishi tekshiriladi.
     - **Yosh:** Faqat 5 dan 60 gacha bo'lgan son qabul qilinadi (matn yozilsa, xato tushuntirilib qayta so'raladi).
     - **Telefon:** `+998XXXXXXXXX` formatiga keltiriladi hamda *"📱 Kontaktni yuborish"* tugmasi taqdim etiladi.

4. **🎯 Lidlarni ajratish va yetkazish:**
   - **🔥 Aniq lid (`hot`):** Kurs tanlangan, ism, yosh va telefon to'liq bo'lganda **bir vaqtning o'zida**:
     1. Ma'lumotlar bazasiga saqlanadi (dublikatsiz, mavjudi yangilanadi).
     2. Google Sheets jadvaliga yangi qator bo'lib yoziladi.
     3. Operatorlar guruhiga formatlangan xabarnoma yuboriladi.
   - **⚠️ Operator kerak (`needs_operator`):** AI aniq javob bera olmaganida yoki mijoz operatorni so'raganda. Guruhga yuborishdan oldin bot kamida ism va telefonni so'rab oladi.

5. **📊 Google Sheets integratsiyasi:**
   - Ustunlar: `Sana`, `Ism`, `Yosh`, `Telefon`, `Kurs`, `Telegram username`.
   - Sheets ishlamay qolsa ham bot to'xtamaydi: xato logga yoziladi, ma'lumotlar bazada xavfsiz saqlanadi.

6. **🎁 Bonus imkoniyatlar:**
   - **Admin buyruqlari:** `/add_course` — yangi kurs qo'shish, `/stats` — bugungi lidlar soni va eng ko'p tanlangan kurs.
   - **"✅ Qabul qildim" tugmasi:** Operator guruhdagi xabar ostidagi tugmani bosganda, lid statusi bazada `accepted` ga o'zgaradi va xabarda qaysi operator qabul qilgani ko'rinadi.
   - **Spamdan himoya:** `ThrottlingMiddleware` orqali rate limiting.
   - Dublikatdan 100% himoya (`upsert_lead`).
   - Xavfsizlik: Barcha maxfiy kalitlar `.env` da, `.gitignore` to'liq sozlangan.

---

## 🛠 Texnologiyalar

| Kutubxona | Maqsad |
|-----------|--------|
| `aiogram 3.x` | Telegram Bot Framework |
| `google-genai` | Google Gemini AI (yangi SDK) |
| `SQLAlchemy 2.0 (asyncio)` + `aiosqlite` | Ma'lumotlar bazasi (SQLite) |
| `gspread` + `google-auth` | Google Sheets integratsiyasi |
| `pydantic-settings` | Konfiguratsiya va `.env` |
| `python-dotenv` | Environment variables |

---

## 📂 Loyiha tuzilmasi

```text
Bot/
├── db/
│   ├── base.py             # Engine, sessiya va jadvallarni yaratish
│   ├── models.py           # Course va Lead SQLAlchemy modellari
│   └── crud.py             # Baza bilan ishlash (kurslar, upsert_lead, stats)
├── handlers/
│   ├── start.py            # /start komandasi va salomlashish
│   ├── courses.py          # Kurslar inline menyusi va "Qabul qildim" callback
│   ├── contact.py          # Telefon kontaktini qabul qilish
│   ├── admin.py            # /stats, /add_course (faqat adminlar)
│   └── chat.py             # AI suhbat va lid ajratish
├── keyboards/
│   ├── inline.py           # Kurslar inline klaviaturasi
│   └── reply.py            # Kontakt yuborish reply klaviaturasi
├── middlewares/
│   └── throttle.py         # Spam himoyasi (rate limiting)
├── services/
│   ├── ai.py               # Gemini AI (structured JSON, fallback modellar)
│   ├── lead.py             # Validatsiyalar va lidlarni tarqatish
│   ├── notifier.py         # Operator guruhiga xabarnomalar
│   └── sheets.py           # Google Sheets ga avtomatik yozish
├── .env                    # Maxfiy sozlamalar (gitignore da)
├── .env.example            # Namunaviy konfiguratsiya
├── .gitignore
├── config.py               # Pydantic sozlamalari
├── main.py                 # Botni ishga tushiruvchi markaziy fayl
└── requirements.txt
```

---

## ⚙️ O'rnatish va Ishga tushirish

### 1. Repozitoriyani klonlash
```bash
git clone <GITHUB_REPO_URL>
cd Bot
```

### 2. Virtual muhit yaratish va faollashtirish

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Sozlamalarni kiritish (`.env`)

`.env.example` faylidan nusxa olib `.env` faylini yarating va to'ldiring:

```env
# Telegram Bot Token (@BotFather dan olingan)
BOT_TOKEN=your_bot_token_here

# Google Gemini API (https://aistudio.google.com dan)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Ma'lumotlar bazasi (SQLite)
DATABASE_URL=sqlite+aiosqlite:///bot.db

# Operatorlar guruhi Telegram ID raqami (manfiy bo'lishi mumkin)
OPERATOR_GROUP_ID=-1001234567890

# Google Sheets
GOOGLE_SHEET_NAME=Leads
GOOGLE_CREDENTIALS_FILE=credentials.json

# Bot adminlari (vergul bilan ajratilgan Telegram ID lar)
ADMIN_IDS=123456789,987654321

# Rate limit — foydalanuvchi xabarlari orasidagi minimal vaqt (sekund)
RATE_LIMIT=1.0
```

### 5. Google Sheets ulanishi

1. [Google Cloud Console](https://console.cloud.google.com) da yangi Service Account oching.
2. JSON kalitni yuklab, loyiha papkasiga `credentials.json` nomi bilan saqlang.
3. Google Sheets da **`Leads`** nomli jadval oching.
4. Jadval sozlamalaridan Service Account emailiga **Editor** huquqi bering.

> ⚠️ `credentials.json` va `.env` fayllari `.gitignore` da — ularni repoga yuklang **emas**!

### 6. Botni ishga tushirish
```bash
python main.py
```

---

## 🧪 Tekshirish Ssenariylari

| # | Test | Kutilgan natija |
|---|------|-----------------|
| 1 | *"Python kursi qancha turadi?"* | AI bazadagi aniq narxni aytadi |
| 2 | *"Yakshanba kuni dars bormi?"* | AI o'ylab topmaydi, `needs_operator` holatiga o'tadi |
| 3 | Telefon: `12345` | Bot xato tushuntirib, to'g'ri format so'raydi |
| 4 | Yosh: `o'n to'rt` yoki `abc` | Bot faqat raqam so'raydi |
| 5 | Kurs tanlab, barcha ma'lumot berish | Baza + Sheets + operator guruhga xabar |
| 6 | Xuddi shu akkauntdan qayta `/start` | Bazada dublikat yaratilmaydi |
| 7 | Operator guruhda `✅ Qabul qildim` bosish | Status `accepted` ga o'zgaradi, kim qabul qilgani ko'rinadi |

---

## 👤 Admin Buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/stats` | Bugungi va jami lidlar soni, eng ko'p tanlangan kurs |
| `/add_course` | Yangi kurs qo'shish (bosqichma-bosqich) |

> Faqat `.env` dagi `ADMIN_IDS` da ko'rsatilgan foydalanuvchilar uchun ishlaydi.
