# 🎓 O'quv Markaz uchun AI Lid-Bot

Telegram orqali yangi o'quvchilarni jalb qilish, ularning savollariga Google Gemini sun'iy intellekti yordamida jonli va tabiiy javob berish, markaz kurslarini ko'rsatish hamda operatorlar uchun saralangan lidlar (leads) yig'ishga mo'ljallangan aqlli bot.

---

## 🚀 Asosiy Imkoniyatlar

1. **🤖 Gemini AI bilan jonli suhbat:**
   - Kurslar haqidagi ma'lumotlar bazadan dinamik olinib, AI system promptiga uzatiladi (kodga qattiq yozilmagan).
   - **O'ylab topmaslik (No Hallucination):** Bazada yo'q ma'lumotlar (aniq jadval, dars kunlari yoki mavjud bo'lmagan kurslar) so'ralsa, AI *"Operatorimiz aniq javob beradi"* deb javob beradi.
   - **Suhbat tarixi:** Kamida oxirgi 10 ta xabar eslab turiladi.

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
   - **"✅ Qabul qildim" tugmasi:** Operator guruhdagi xabar ostidagi tugmani bosganda, lid statusi bazada `accepted` ga o'zgaradi va xabarda qaysi operator qabul qilgani ko'rinadi.
   - Dublikatdan 100% himoya (`upsert_lead`).
   - Xavfsizlik: Barcha maxfiy kalitlar `.env` da, `.gitignore` to'liq sozlangan.

---

## 🛠 Texnologiyalar

- **Dasturlash tili:** Python 3.11+
- **Telegram Bot Framework:** `aiogram 3.x`
- **Sun'iy intellekt:** Google Gemini API (`gemini-2.0-flash`)
- **Ma'lumotlar bazasi:** SQLite3 / PostgreSQL + `SQLAlchemy 2.0 (asyncio)` + `aiosqlite` / `asyncpg`
- **Jadval integratsiyasi:** `gspread` + `google-auth`
- **Konfiguratsiya:** `pydantic-settings`, `python-dotenv`

---

## 📂 Loyiha tuzilmasi

```text
Bot/
├── db/                     # Ma'lumotlar bazasi
│   ├── base.py             # Dvigatel, sessiya va jadvallarni yaratish
│   ├── models.py           # Course va Lead SQLAlchemy modellari
│   └── crud.py             # Baza bilan ishlash (kurslar, upsert_lead)
├── handlers/               # Telegram hodisalari
│   ├── start.py            # /start komandasi va salomlashish
│   ├── courses.py          # Kurslar inline menyusi va operator callback
│   ├── contact.py          # Telefon kontaktini qabul qilish
│   └── chat.py             # AI suhbat va lid ajratish
├── keyboards/              # Tugmalar
│   ├── inline.py           # Kurslar inline klaviaturasi
│   └── reply.py            # Kontakt yuborish reply klaviaturasi
├── services/               # Biznes logika
│   ├── ai.py               # Gemini AI integratsiyasi (structured JSON)
│   ├── lead.py             # Validatsiyalar va lidlarni tarqatish
│   ├── notifier.py         # Operator guruhiga xabarnomalar
│   └── sheets.py           # Google Sheets ga avtomatik yozish
├── .env                    # Maxfiy sozlamalar (gitignore)
├── .env.example            # Namunaviy konfiguratsiya
├── .gitignore              # Git e'tibor bermaydigan fayllar
├── config.py               # Pydantic sozlamalari
├── main.py                 # Botni ishga tushiruvchi markaziy fayl
├── requirements.txt        # Kerakli Python kutubxonalari
└── README.md               # Loyiha qo'llanmasi
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
`.env.example` faylidan nusxa olib `.env` faylini yarating:
```env
# Telegram Bot Token (@BotFather dan olingan)
BOT_TOKEN=8983489219:AAGziMFmT9tPB9IxTD4TrwuRMXLYYdd_3uU

# Google Gemini API (@aistudio.google.com dan)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Ma'lumotlar bazasi
DATABASE_URL=sqlite+aiosqlite:///bot.db

# Operatorlar guruhi ID raqami
OPERATOR_GROUP_ID=-1001234567890

# Google Sheets
GOOGLE_SHEET_NAME=Leads
GOOGLE_CREDENTIALS_FILE=credentials.json

# Bot adminlari ID raqamlari
ADMIN_IDS=123456789
```

### 5. Google Sheets ulanishi
1. Google Cloud Console da Service Account ochib, kalitni `credentials.json` nomi bilan loyiha papkasiga joylashtiring.
2. Google Sheets da **`Leads`** nomli jadval oching.
3. Jadval sozlamalaridan ("Настройки доступа") Service Account emailiga **"Редактор" (Editor)** huquqini bering.

### 6. Botni ishga tushirish
```bash
python main.py
```

---

## 🧪 Tekshirish Ssenariylari

1. **"Python kursi qancha turadi?" deb so'rash:**
   - AI bazadagi aniq narxni aytadi: *800 000 so'm/oy*.
2. **Bazada yo'q savol berish (Masalan: "Yakshanba kuni dars bormi?"):**
   - AI o'ylab topmaydi va *"Bu haqida operatorimiz aniq javob beradi"* deb javob beradi. Holat `needs_operator` ga o'tadi.
3. **Telefon o'rniga "12345" yozish:**
   - Bot raqam noto'g'ri ekanligini tushuntirib, to'g'ri raqamni kiritishni so'raydi.
4. **Yoshga "o'n to'rt" yoki "abc" yozish:**
   - Bot yosh faqat raqamda bo'lishi kerakligini xushmuomala tushuntirib qayta so'raydi.
5. **Kurs tanlab, barcha ma'lumotlarni berish:**
   - Lid bazada saqlanadi, Google Sheets da qator paydo bo'ladi va operator guruhga `YANGI ANIQ LID` xabari boradi.
6. **Xuddi shu akkauntdan qayta /start bosish:**
   - Bazada dublikat yaratilmaydi, mavjud foydalanuvchi ma'lumotlari yangilanadi.
