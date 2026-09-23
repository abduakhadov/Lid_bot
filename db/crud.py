from datetime import datetime, time
from typing import Sequence, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Course, Lead


async def get_active_courses(session: AsyncSession) -> Sequence[Course]:
    """Bazadagi barcha faol kurslarni qaytaradi"""
    stmt = select(Course).where(Course.is_active.is_(True)).order_by(Course.id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_course_by_id(session: AsyncSession, course_id: int) -> Course | None:
    """ID bo'yicha kursni qaytaradi"""
    stmt = select(Course).where(Course.id == course_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_course(
    session: AsyncSession,
    name: str,
    description: str,
    price: int,
    duration: str,
    age_min: int = 5,
    age_max: int = 60
) -> Course:
    """Yangi kurs qo'shish (Admin buyrug'i uchun)"""
    course = Course(
        name=name,
        description=description,
        price=price,
        duration=duration,
        age_min=age_min,
        age_max=age_max,
        is_active=True
    )
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


async def get_lead_by_telegram_id(session: AsyncSession, telegram_id: int) -> Lead | None:
    """Telegram ID bo'yicha lidni topish"""
    stmt = select(Lead).where(Lead.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_lead(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
    age: int | None = None,
    phone: str | None = None,
    course_id: int | None = None,
    status: str = "collecting"
) -> Lead:
    """
    Lidni saqlash yoki yangilash.
    Bir xil foydalanuvchi qayta yozilsa, dublikat yaratilmaydi, mavjudi yangilanadi.
    """
    stmt = select(Lead).where(Lead.telegram_id == telegram_id)
    result = await session.execute(stmt)
    lead = result.scalar_one_or_none()

    if lead:
        if username is not None:
            lead.username = username
        if full_name is not None:
            lead.full_name = full_name
        if age is not None:
            lead.age = age
        if phone is not None:
            lead.phone = phone
        if course_id is not None:
            lead.course_id = course_id
        lead.status = status
    else:
        lead = Lead(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            age=age,
            phone=phone,
            course_id=course_id,
            status=status
        )
        session.add(lead)

    await session.commit()
    await session.refresh(lead)
    return lead


async def get_lead_statistics(session: AsyncSession) -> dict[str, Any]:
    """
    Admin statistikasi:
    - Bugungi lidlar soni
    - Jami lidlar soni
    - Eng ko'p tanlangan kurs
    - Hot va needs_operator lidlar soni
    """
    # Jami lidlar
    total_leads = await session.scalar(select(func.count(Lead.id))) or 0

    # Bugungi lidlar
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_leads = await session.scalar(
        select(func.count(Lead.id)).where(Lead.created_at >= today_start)
    ) or 0

    # Aniq lidlar va Operator yordami kerak bo'lganlar
    hot_leads = await session.scalar(
        select(func.count(Lead.id)).where(Lead.status.in_(["hot", "accepted"]))
    ) or 0

    needs_operator_leads = await session.scalar(
        select(func.count(Lead.id)).where(Lead.status == "needs_operator")
    ) or 0

    # Eng ko'p tanlangan kurs
    stmt = (
        select(Course.name, func.count(Lead.id).label("count"))
        .join(Lead, Course.id == Lead.course_id)
        .group_by(Course.id, Course.name)
        .order_by(desc("count"))
        .limit(1)
    )
    res = await session.execute(stmt)
    top_course_row = res.first()
    
    top_course_name = top_course_row[0] if top_course_row else "Hali tanlanmagan"
    top_course_count = top_course_row[1] if top_course_row else 0

    return {
        "today_leads": today_leads,
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "needs_operator_leads": needs_operator_leads,
        "top_course_name": top_course_name,
        "top_course_count": top_course_count
    }


async def seed_initial_courses(session: AsyncSession) -> None:
    """Agar bazada kurslar bo'lmasa, boshlang'ich kurslarni kiritadi"""
    courses = await get_active_courses(session)
    if not courses:
        initial = [
            Course(
                name="Python Backend",
                description="Python asoslari, Django, PostgreSQL, REST API va botlar yaratish.",
                price=800000,
                duration="5 oy",
                age_min=13,
                age_max=45,
                is_active=True
            ),
            Course(
                name="Frontend Dasturlash",
                description="HTML, CSS, JavaScript, React va zamonaviy web interfeyslar.",
                price=750000,
                duration="4 oy",
                age_min=12,
                age_max=40,
                is_active=True
            ),
            Course(
                name="Kompyuter Savodxonligi",
                description="Windows, Word, Excel, PowerPoint va internetdan to'g'ri foydalanish.",
                price=500000,
                duration="2 oy",
                age_min=7,
                age_max=60,
                is_active=True
            ),
        ]
        session.add_all(initial)
        await session.commit()
