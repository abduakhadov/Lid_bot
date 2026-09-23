Imtihon topshirig'i
O'quv markaz uchun AI lid-bot
Muddat:
Texnologiyalar:
O'tish bali:
O'quvchi F.I.Sh.:
7 kun
Python 3.11+, aiogram 3.x, LLM API (OpenAI, Gemini yoki Claude, o'quvchi
tanlaydi), PostgreSQL + SQLAlchemy, gspread (Google Sheets), python-dotenv
60 / 100
______________________________________
1. Loyiha haqida
O'quv markaz Telegram bot orqali yangi o'quvchilarni jalb qilmoqchi. /start bosgan
foydalanuvchi bilan bot sun'iy intellekt yordamida jonli suhbat quradi, savollariga javob
beradi, mavjud kurslarni ko'rsatadi va operatorlar uchun lid yig'adi. Lid degani markazga
qiziqish bildirgan va bog'lanish uchun ma'lumot qoldirgan odam.
2. Asosiy talablar
2.1. /start va AI suhbat
• /start bosilganda bot salomlashadi va suhbatni boshlaydi.
• Foydalanuvchi har qanday savol yozishi mumkin, AI kurslar ma'lumoti asosida javob
beradi.
• Kurslar ro'yxati AI ga system prompt orqali bazadan olib beriladi (kodga qattiq
yozilmaydi).
• AI bazada yo'q narsani o'ylab topmasligi shart: narx, jadval yoki kurs haqida ma'lumot
bo'lmasa, "operatorimiz aniq javob beradi" deb aytadi.
• Suhbat tarixi saqlanadi (kamida oxirgi 10 ta xabar), AI oldingi gaplarni eslab turadi.
2.2. Kurslarni ko'rsatish
• Bot kurslarni inline tugmalar orqali ko'rsatadi (nomi, davomiyligi, narxi, yosh chegarasi).
• Foydalanuvchi tugmani bosib kurs tanlashi mumkin, yoki suhbatda "Python ga
yozilmoqchiman" desa, AI ham buni tushunishi kerak.
2.3. Lid ma'lumotlarini yig'ish
AI suhbat davomida tabiiy tarzda (anketa kabi emas) quyidagilarni so'rab oladi:
Maydon
Validatsiya
Ism
Yosh
Bo'sh bo'lmasligi, kamida 2 harf
Faqat son, 5 dan 60 gacha
+998XXXXXXXXX formatiga keltiriladi; "Kontakt yuborish" tugmasi ham bo'lishi
kerak
Telefon
Noto'g'ri ma'lumot kiritilsa, bot xatoni tushuntirib qayta so'raydi.
1-bet
Imtihon topshirig'i: O'quv markaz uchun AI lid-bot
Imtihon topshirig'i: O'quv markaz uchun AI lid-bot 2-bet
AI javobidan ma'lumotlarni ajratib olish uchun structured output ishlatilsin (JSON yoki
function calling). Masalan:
{
  "reply": "Python kursimiz 3 oy davom etadi, haftada 3 marta.",
  "name": "Aziz",
  "age": 14,
  "phone": null,
  "course_id": 2,
  "status": "collecting"
}
status qiymatlari: collecting (ma'lumot yig'ilmoqda), hot (aniq lid), needs_operator
(operator yordami kerak).
2.4. Lidlarni ajratish
Lid turi Qachon hosil bo'ladi Qayerga yuboriladi
Aniq lid Kurs tanlangan va ism, yosh, telefon
to'liq
Baza + Google Sheets + operator
guruh (bir vaqtda)
Operator kerak AI aniq javob bera olmadi yoki user qaror
qila olmadi
Operator guruh
"Operator kerak" holatida ham bot guruhga yuborishdan oldin kamida ism va telefonni so'rab
olishi kerak, aks holda operator bog'lana olmaydi.
2.5. Operator guruhga xabar
Xabar tushunarli formatda bo'lsin (emoji ishlatish mumkin):
YANGI ANIQ LID
Ism:      Aziz Karimov
Yosh:     14
Tel:      +998901234567
Kurs:     Python Backend
Telegram: @aziz_k
Vaqt:     21.09.2026 14:32
OPERATOR YORDAMI KERAK
Ism:             Madina
Tel:             +998931112233
Javobsiz savol:  Dam olish kunlari guruh bormi?
Suhbat xulosasi: (AI yozgan 1-2 gaplik xulosa)
2.6. Ma'lumotlar bazasi
Kamida 2 ta jadval:
• courses: id, name, description, price, duration, age_min, age_max, is_active
• leads: id, telegram_id, username, full_name, age, phone, course_id, status, created_at
Bir xil foydalanuvchi qayta yozilsa, yangi lid yaratilmaydi, mavjudi yangilanadi (dublikat
bo'lmasligi kerak).
2.7. Google Sheets
• Aniq lid bazaga yozilishi bilan jadvalga ham qator qo'shiladi.
• Ustunlar: Sana, Ism, Yosh, Telefon, Kurs, Telegram username.
• Sheets ishlamay qolsa, bot to'xtamasligi kerak: lid bazada saqlanadi, xato logga yoziladi.
2.8. Texnik talablar
• Barcha tokenlar va kalitlar .env da; repoda .env.example bo'lsin, credentials.json va
.env esa .gitignore da.
• Kod papkalarga bo'lingan bo'lsin (handlers, services, db, keyboards), hammasi bitta faylda
bo'lmasin.
• AI API xato bersa, foydalanuvchiga tushunarli javob beriladi va holat "operator kerak" ga
o'tadi.
• Logging ulangan bo'lsin.
3. Topshirish tartibi
1 GitHub repo havolasi
2 README: loyiha tavsifi, o'rnatish va ishga tushirish qadamlari
3 2-3 daqiqalik demo video yoki skrinshotlar (suhbat, guruhdagi xabar, Sheets jadvali)
4. Tekshirish ssenariylari
O'qituvchi botni quyidagi holatlar bo'yicha sinab ko'radi:
1 "Python kursi qancha turadi?" deb so'rash: AI bazadagi narxni aytishi kerak.
2 Bazada yo'q savol berish: AI o'ylab topmasligi, lid guruhga "operator kerak" bo'lib borishi
kerak.
3 Telefon o'rniga "12345" yozish: bot qayta so'rashi kerak.
4 Yoshga "o'n to'rt" yoki "abc" yozish: to'g'ri ishlov berilishi kerak.
5 Kurs tanlab, barcha ma'lumotni berish: lid bazada, Sheets da va guruhda paydo bo'lishi
kerak.
6 Xuddi shu akkauntdan qayta /start bosish: dublikat yaratilmasligi kerak.
5. Baholash mezonlari (100 ball)
Mezon
Bot tuzilmasi, /start, ishga tushishi
AI suhbat sifati (kontekst, o'ylab topmaslik, tarix)
Ball
10
Olingan
20
Ma'lumot yig'ish va validatsiya
Kurslarni ko'rsatish va tanlash
15
10
Lidlarni ajratish va operator guruhga yuborish
Ma'lumotlar bazasi (modellar, dublikatsiz saqlash)
15
10
Google Sheets integratsiyasi
Kod sifati, .env, README, xatolarga ishlov berish
Jami
10
10
100
O'tish bali: 60
3-bet
Imtihon topshirig'i: O'quv markaz uchun AI lid-bot
6. Bonus vazifalar (har biri +5 ball)
• Admin buyruqlari: /add_course, /stats (bugungi lidlar soni, eng ko'p tanlangan kurs)
• Guruhdagi xabarda "Qabul qildim" tugmasi: operator bosganda lid statusi bazada
yangilanadi va xabarda kim qabul qilgani ko'rinadi
• Docker va docker-compose orqali ishga tushirish
• Spamdan himoya (rate limit)
4-bet
Imtihon topshirig'i: O'quv markaz uchun AI lid-bot