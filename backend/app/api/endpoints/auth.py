from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.crud.user import get_user_by_email, get_user_by_nik_or_nip, create_user
from app.core.security import verify_password, create_access_token
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=422, detail="Email already registered")
        
    db_user = get_user_by_nik_or_nip(db, nik_or_nip=user.nik_or_nip)
    if db_user:
        raise HTTPException(status_code=422, detail="NIK/NIP already registered")
        
    return create_user(db=db, user=user)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=form_data.username)
    
    if not user:
        user = get_user_by_nik_or_nip(db, nik_or_nip=form_data.username)
        
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/NIK or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
