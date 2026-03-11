import base64
import hashlib
from cryptography.fernet import Fernet


def _fernet(secret_key: str) -> Fernet:
    key = hashlib.sha256(secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value: str, secret_key: str) -> str:
    return _fernet(secret_key).encrypt(value.encode()).decode()


def decrypt(value: str, secret_key: str) -> str:
    return _fernet(secret_key).decrypt(value.encode()).decode()


def mask(value: str) -> str:
    if len(value) <= 4:
        return "••••"
    return "••••••••" + value[-4:]
