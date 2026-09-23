from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Any


class Settings(BaseSettings):
    # Telegram Bot
    BOT_TOKEN: str
    
    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///bot.db"
    
    # Operator guruh
    OPERATOR_GROUP_ID: int = 0
    
    # Google Sheets
    GOOGLE_SHEET_NAME: str = "Leads"
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"
    
    # Admins
    ADMIN_IDS: str = ""
    
    # Throttle / Rate limit
    RATE_LIMIT: float = 1.0

    @field_validator("OPERATOR_GROUP_ID", mode="before")
    @classmethod
    def parse_operator_group_id(cls, v: Any) -> int:
        if v is None or v == "" or str(v).strip() == "":
            return 0
        return int(v)

    @field_validator("RATE_LIMIT", mode="before")
    @classmethod
    def parse_rate_limit(cls, v: Any) -> float:
        if v is None or v == "" or str(v).strip() == "":
            return 1.0
        return float(v)

    @property
    def admin_id_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
