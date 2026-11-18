
import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sample_config import Config


def decrypt_session():
    encrypted = os.environ.get("ENCRYPTED_SESSION")
    key_encoded = os.environ.get("SESSION_ENCRYPTION_KEY")

    if not encrypted or not key_encoded:
        raise RuntimeError("Missing session encryption environment variables")

    try:
        encrypted_data = base64.b64decode(encrypted, validate=True)
        key = base64.b64decode(key_encoded, validate=True)

        if len(key) != 32:
            raise ValueError("Invalid AES-256 key length")

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        if len(nonce) != 12 or len(ciphertext) < 16:
            raise ValueError("Invalid encrypted session format")

        return AESGCM(key).decrypt(
            nonce, ciphertext, None
        ).decode("utf-8")

    except Exception:
        raise RuntimeError("Session decryption failed") from None


class Development(Config):
    STRING_SESSION = decrypt_session()
    SUDO_USERS = {
        int(user_id)
        for user_id in os.environ.get("SUDO_USERS", "").replace(",", " ").split()
    }
