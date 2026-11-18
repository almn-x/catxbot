import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sample_config import Config


def decrypt_session():
    encrypted = os.environ.get("ENCRYPTED_SESSION", "").strip()
    key_encoded = os.environ.get("SESSION_ENCRYPTION_KEY", "").strip()

    # only lenth not Secret
    print(
        f"[DIAG] encrypted_env_len={len(encrypted)} "
        f"key_env_len={len(key_encoded)}"
    )

    if not encrypted or not key_encoded:
        raise RuntimeError("Missing session encryption environment variables")

    try:
        encrypted_data = base64.b64decode(encrypted, validate=True)
        key = base64.b64decode(key_encoded, validate=True)

        print(
            f"[DIAG] encrypted_decoded_len={len(encrypted_data)} "
            f"key_decoded_len={len(key)}"
        )

        if len(key) != 32:
            raise ValueError(f"Key length is {len(key)}, expected 32")

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        print(
            f"[DIAG] nonce_len={len(nonce)} "
            f"ciphertext_len={len(ciphertext)}"
        )

        if len(ciphertext) < 16:
            raise ValueError(f"Ciphertext too short: {len(ciphertext)}")

        return AESGCM(key).decrypt(
            nonce, ciphertext, None
        ).decode("utf-8")

    except Exception as e:
        raise RuntimeError(
            f"Session decryption failed: {type(e).__name__}: {str(e)[:120]}"
        ) from None


class Development(Config):
    STRING_SESSION = decrypt_session()
    SUDO_USERS = {
        int(user_id)
        for user_id in os.environ.get("SUDO_USERS", "").replace(",", " ").split()
    }
