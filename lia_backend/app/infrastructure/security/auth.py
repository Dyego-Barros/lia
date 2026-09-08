import base64
import binascii
import hashlib
import hmac
import json
import os
import time


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"{_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_text, digest_text = encoded.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_text + "==")
        expected = base64.urlsafe_b64decode(digest_text + "==")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, role: str) -> str:
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": user_id, "role": role, "iat": now, "exp": now + 8 * 60 * 60}, separators=(",", ":")).encode())
    unsigned = f"{header}.{payload}"
    signature = _b64(hmac.new(_secret().encode(), unsigned.encode(), hashlib.sha256).digest())
    return f"{unsigned}.{signature}"


def decode_token(token: str) -> dict:
    try:
        header, payload, signature = token.split(".")
        header_data = json.loads(base64.urlsafe_b64decode(header + "=="))
        if header_data.get("alg") != "HS256" or header_data.get("typ") != "JWT":
            raise ValueError("Cabeçalho JWT inválido")
        unsigned = f"{header}.{payload}"
        expected = _b64(hmac.new(_secret().encode(), unsigned.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Assinatura inválida")
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if not isinstance(data.get("sub"), int) or not isinstance(data.get("role"), str):
            raise ValueError("Payload JWT inválido")
        if int(data["exp"]) < int(time.time()):
            raise ValueError("Token expirado")
        return data
    except (ValueError, KeyError, TypeError, binascii.Error, json.JSONDecodeError) as exc:
        raise ValueError("Token inválido") from exc


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret or secret == "change-this-jwt-secret-in-production" or len(secret) < 32:
        raise RuntimeError("JWT_SECRET precisa ter ao menos 32 caracteres aleatórios")
    return secret
