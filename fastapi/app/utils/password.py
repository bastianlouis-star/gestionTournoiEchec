import os
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# 1. Configuration de l'algorithme Argon2id selon les recommandations OWASP
# m=65536 (64 MiB), t=3 (3 itérations), p=4 (4 threads)
argon2_hasher = Argon2Hasher(
    memory_cost=65536,
    time_cost=3,
    parallelism=4
)

password_context = PasswordHash([argon2_hasher,])


def get_pepper() -> str:
    """
    Récupère le Pepper depuis l'environnement système / Key Vault.
    Lève une erreur bloquante si le Pepper est absent ou non sécurisé.
    """
    pepper = os.getenv("APP_SECURITY_PEPPER")
    if not pepper or len(pepper) < 32:
        raise RuntimeError("CRITICAL: APP_SECURITY_PEPPER non configuré ou trop court !")
    return pepper


def hash_password(plain_password: str) -> str:
    """
    Génère un hash Argon2id sécurisé en combinant
    le mot de passe clair avec le Pepper global.
    """
    pepper = get_pepper()
    # Combinaison du mot de passe avec le Pepper
    prepared_password = plain_password + pepper
    # Le Salt est généré automatiquement par la bibliothèque
    return password_context.hash(prepared_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie l'exactitude d'un mot de passe fourni.
    """
    pepper = get_pepper()
    prepared_password = plain_password + pepper
    try:
        return password_context.verify(prepared_password, hashed_password)
    except Exception:
        return False
