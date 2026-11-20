import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sample_config import Config


def decrypt_session():
    encrypted = os.environ.get("ENCRYPTED_SESSION", "").strip()
    key_encoded = os.environ.get("SESSION_ENCRYPTION_KEY", "").strip()

    if not encrypted or not key_encoded:
        raise RuntimeError("Missing session encryption environment variables")

    try:
        encrypted_data = base64.b64decode(encrypted, validate=True)
        key = base64.b64decode(key_encoded, validate=True)
        if len(key) != 32:
            raise ValueError("Invalid AES-256 key length")
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        if len(ciphertext) < 16:
            raise ValueError("Invalid encrypted session format")
        return AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception as e:
        raise RuntimeError(
            f"Session decryption failed: {type(e).__name__}: {str(e)[:120]}"
        ) from None


def _safe_env_botlog():
    """Read PRIVATE_GROUP_BOT_API_ID from env safely.
    Returns int if valid, else 'me'."""
    raw = os.environ.get("PRIVATE_GROUP_BOT_API_ID", "").strip()
    if raw and raw.lstrip("-").isdigit():
        return int(raw)
    return "me"


class Development(Config):
    STRING_SESSION = decrypt_session()
    SUDO_USERS = {
        int(user_id)
        for user_id in os.environ.get("SUDO_USERS", "").replace(",", " ").split()
        if user_id.strip().lstrip("-").isdigit()
    }
    BOTLOG_CHATID = _safe_env_botlog()
