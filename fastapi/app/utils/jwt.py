import os
from datetime import datetime, timedelta, timezone

import jwt

# Clé secrète de signature (32 octets / 256 bits minimum)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_DEV_ONLY_SECRET_KEY_EXEMPLAR_32BYTES_MIN")
ALGORITHM = "HS256"


def generate_jwt(subject: str, role: str, id: int) -> str:
    """Génère un JWT signé."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "id": id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt(token: str) -> dict:
    """Décode et valide la signature ainsi que l'expiration du JWT."""
    try:
        # Contrôle strict de la signature, de la péremption et de l'algorithme autorisé
        decoded_payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True, "verify_signature": True}
        )
        return decoded_payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Le jeton a expiré.")
    except jwt.InvalidSignatureError:
        raise ValueError("La signature du jeton est invalide (tentative d'altération).")
    except jwt.PyJWTError as e:
        raise ValueError(f"Jeton invalide : {str(e)}")
