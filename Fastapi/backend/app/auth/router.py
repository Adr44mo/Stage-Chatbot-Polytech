from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List

from .models import User, UserCreate, UserRead
from .dependencies import get_current_user_from_cookie, get_current_admin_from_cookie, get_session
from .security import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from .dependencies import get_current_admin


router = APIRouter(prefix="/auth", tags=["auth"])

def authenticate_user(session: Session, username: str, password: str):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or not admin")
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(hours=1)
    )
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        secure=False,  # mettre True en prod avec HTTPS
        samesite="lax",
        max_age=3600,
        path="/"
    )
    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="admin_token", path="/")
    return {"message": "Logged out"}

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user_from_cookie)):
    return current_user

@router.get("/admin/users", response_model=List[UserRead])
def read_all_users(admin: User = Depends(get_current_admin_from_cookie), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.post("/register", response_model=UserRead)
def register_user(user_create: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_create.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        username=user_create.username,
        hashed_password=get_password_hash(user_create.password),
        role="user" # Default role is 'user', can be changed later~~
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

