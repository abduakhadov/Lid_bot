import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Spamdan himoya (Rate limit) middleware.
    Foydalanuvchi tez-tez xabar yuborganida cheklov qo'yadi.
    """
    def __init__(self, rate_limit: float = None):
        self.rate_limit = rate_limit or settings.RATE_LIMIT
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Faqat Message hodisalari uchun
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            current_time = time.time()
            last_time = self.user_timestamps.get(user_id, 0.0)

            # Agar belgilangan vaqtdan tezroq xabar yozsa
            if current_time - last_time < self.rate_limit:
                # Birinchi marta ogohlantirish
                if current_time - last_time > 0.3:
                    await event.answer("⚠️ Iltimos, juda tez xabar yubormang. Biroz kuting!")
                return  # Keyingi handlerga o'tkazmaslik

            # Oxirgi yuborgan vaqtini saqlash
            self.user_timestamps[user_id] = current_time

            # Xotirani tozalash (agar 5000 tadan oshsa)
            if len(self.user_timestamps) > 5000:
                cutoff = current_time - 60
                self.user_timestamps = {
                    uid: t for uid, t in self.user_timestamps.items() if t > cutoff
                }

        return await handler(event, data)
