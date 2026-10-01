# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

# Regex kekuatan password sesuai PRD:
# - Min 8 karakter
# - Min 1 huruf besar
# - Min 1 huruf kecil
# - Min 1 angka
# - Min 1 simbol khusus
PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$'
)


def validate_password_strength(password: str) -> str:
    if not PASSWORD_REGEX.match(password):
        raise ValueError(
            "Password harus minimal 8 karakter dan mengandung huruf besar, "
            "huruf kecil, angka, dan karakter simbol (contoh: !@#$%^&*)."
        )
    return password


class UserBase(BaseModel):
    nik_or_nip: str = Field(..., min_length=16, max_length=20, description="NIK untuk warga (16 digit), NIP untuk pegawai")
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        return validate_password_strength(v)

class AdminDinasCreate(BaseModel):
    nip: str = Field(..., min_length=16, max_length=20, description="NIP Pegawai")
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        return validate_password_strength(v)

class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True
