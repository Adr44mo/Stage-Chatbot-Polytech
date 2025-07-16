import httpx
import os

async def verify_recaptcha_token(token: str) -> bool:
    """Validation du token reCAPTCHA
    Retourne True si le token est valide, False sinon.
    """
    secret = os.getenv("RECAPTCHA_SECRET_KEY")
    # Pas de token si pas de clé secrète (en dev)
    if not secret:
        return True
    # Token obligatoire si clé secrète définie (en prod)
    if not token:
        return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={"secret": secret, "response": token}
            )
            result = response.json()
            return result.get("success", False)
    except Exception as e:
        return False
