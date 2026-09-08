import os


def _key() -> bytes:
    configured = os.getenv("INTEGRATION_ENCRYPTION_KEY", "").strip()
    if not configured:
        raise RuntimeError("INTEGRATION_ENCRYPTION_KEY precisa ser configurado")
    return configured.encode()


def encrypt_secret(value: str) -> str:
    from cryptography.fernet import Fernet
    return Fernet(_key()).encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    from cryptography.fernet import Fernet
    return Fernet(_key()).decrypt(value.encode()).decode()
