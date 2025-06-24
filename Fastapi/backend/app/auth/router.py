from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List

from .models import User, UserCreate, UserRead
from .dependencies import get_current_user, get_current_admin, get_session
from .security import verify_password, get_password_hash, create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])

def authenticate_user(session: Session, username: str, password: str):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

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

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin/users", response_model=List[UserRead])
def read_all_users(admin: User = Depends(get_current_admin), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.post("/admin/create-user")
def create_user_as_admin(
    user_create: UserCreate,
    role: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    user = User(
        username=user_create.username,
        hashed_password=get_password_hash(user_create.password),
        role=role
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": f"{role.capitalize()} user created", "user_id": user.id}

