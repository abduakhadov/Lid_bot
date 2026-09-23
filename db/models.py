from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # so'mda
    duration: Mapped[str] = mapped_column(String(100), nullable=True)  # Masalan: "3 oy", "6 oy"
    age_min: Mapped[int] = mapped_column(Integer, nullable=True, default=5)
    age_max: Mapped[int] = mapped_column(Integer, nullable=True, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="course")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="collecting", nullable=False)  # collecting, hot, needs_operator
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    course: Mapped["Course | None"] = relationship("Course", back_populates="leads")
