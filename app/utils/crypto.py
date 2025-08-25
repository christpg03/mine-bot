import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()


class CryptoManager:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise RuntimeError("⚠️ ENCRYPTION_KEY not found in .env")
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode())

    def decrypt(self, token: bytes) -> str:
        return self.fernet.decrypt(token).decode()
