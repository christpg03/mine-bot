import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    redmine_url: str = os.getenv("REDMINE_URL", "")

    def validate(self):
        if not self.bot_token:
            raise RuntimeError("⚠️ BOT_TOKEN not found in .env")
        if not self.redmine_url:
            raise RuntimeError("⚠️ REDMINE_URL not found in .env")


settings = Settings()
