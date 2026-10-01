from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, AdminDinasCreate
from app.core.security import get_password_hash

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_nik_or_nip(db: Session, nik_or_nip: str):
    return db.query(User).filter(User.nik_or_nip == nik_or_nip).first()

def create_user(db: Session, user: UserCreate, role: str = "warga"):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        nik_or_nip=user.nik_or_nip,
        password_hash=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_admin_dinas(db: Session, admin_in: AdminDinasCreate):
    hashed_password = get_password_hash(admin_in.password)
    db_user = User(
        email=admin_in.email,
        nik_or_nip=admin_in.nip,
        password_hash=hashed_password,
        role="admin"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def seed_super_admin(db: Session):
    existing = get_user_by_email(db, "superadmin@govsmart.go.id")
    if not existing:
        hashed_password = get_password_hash("SuperAdmin123!")
        super_admin = User(
            email="superadmin@govsmart.go.id",
            nik_or_nip="199001012026011001",
            password_hash=hashed_password,
            role="super_admin"
        )
        db.add(super_admin)
        db.commit()
