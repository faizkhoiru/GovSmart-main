from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, PasswordResetRequest
from app.schemas.token import Token
from app.crud.user import get_user_by_email, get_user_by_nik_or_nip, create_user
from app.core.security import verify_password, create_access_token, get_password_hash
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

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda telah dinonaktifkan. Silakan hubungi Super Admin.",
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/reset-password")
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Reset kata sandi mandiri dengan memverifikasi kecocokan Email dan NIK/NIP yang terdaftar.
    """
    user_by_email = get_user_by_email(db, email=str(payload.email).strip().lower())
    user_by_nik = get_user_by_nik_or_nip(db, nik_or_nip=payload.nik_or_nip.strip())
    if not user_by_email or not user_by_nik or user_by_email.id != user_by_nik.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kombinasi NIK/NIP dan Email tidak cocok dengan akun mana pun.",
        )
    if user_by_email.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun telah dinonaktifkan. Silakan hubungi Super Admin.",
        )
    user_by_email.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "success", "detail": "Kata sandi berhasil diperbarui. Silakan masuk dengan kata sandi baru."}
