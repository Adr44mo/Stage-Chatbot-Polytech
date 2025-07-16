from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from .database import get_session
from .models import User
from .security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_from_cookie(request: Request, session: Session = Depends(get_session)) -> User:
    """
    Récupère l'utilisateur actuel à partir du cookie d'authentification HttpOnly.
    """
    token = request.cookies.get("admin_token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_from_cookie(user: User = Depends(get_current_user_from_cookie)):
    """
    "Vérifie si l'utilisateur actuel est un administrateur.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
