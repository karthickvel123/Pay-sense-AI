import os
from dotenv import load_dotenv

class Settings:
    @property
    def RAZORPAY_KEY_ID(self) -> str:
        load_dotenv(override=True)
        return os.getenv("RAZORPAY_KEY_ID", "")

    @property
    def RAZORPAY_KEY_SECRET(self) -> str:
        load_dotenv(override=True)
        return os.getenv("RAZORPAY_KEY_SECRET", "")

    @property
    def GEMINI_API_KEY(self) -> str:
        load_dotenv(override=True)
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./paysense.db")

    @property
    def APP_MODE(self) -> str:
        return os.getenv("APP_MODE", "test")

settings = Settings()
