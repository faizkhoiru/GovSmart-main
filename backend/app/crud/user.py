from sqlalchemy.orm import Session
from app.models.user import User
from app.models.department import Department
from app.schemas.user import UserCreate, AdminDinasCreate, AdminDinasUpdate
from app.core.security import get_password_hash

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_nik_or_nip(db: Session, nik_or_nip: str):
    return db.query(User).filter(User.nik_or_nip == nik_or_nip).first()

def get_user_by_dept_id(db: Session, dept_id: int):
    return db.query(User).filter(User.dept_id == dept_id).first()

def get_admin_dinas_list(db: Session, skip: int = 0, limit: int = 100):
    results = (
        db.query(User, Department.nama_dinas.label("nama_dinas"))
        .outerjoin(Department, User.dept_id == Department.id)
        .filter(User.role == "admin", User.is_active == True)
        .order_by(User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    # Attach nama_dinas onto each User so response_model (UserResponse) can read it.
    for user, nama_dinas in results:
        setattr(user, "nama_dinas", nama_dinas)
    return [r[0] for r in results]

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
        role="admin",
        dept_id=admin_in.dept_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_admin_dinas(db: Session, admin_id: int, admin_in: AdminDinasUpdate):
    db_admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not db_admin:
        return None
    update_data = admin_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]
    for field, value in update_data.items():
        setattr(db_admin, field, value)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def soft_delete_admin_dinas(db: Session, admin_id: int):
    db_admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not db_admin:
        return None
    db_admin.is_active = False
    db.commit()
    db.refresh(db_admin)
    return db_admin

def hard_delete_admin_dinas(db: Session, admin_id: int):
    db_admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not db_admin:
        return None
    db.delete(db_admin)
    db.commit()
    return db_admin

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


def seed_admin_dinas(db: Session, per_department: int = 2):
    """Create idempotent demo admin accounts for every seeded department."""
    departments = db.query(Department).order_by(Department.id).all()
    password_hash = get_password_hash("AdminDinas123!")
    created = 0

    for department in departments:
        for account_number in range(1, per_department + 1):
            email = f"admin.dinas{department.id}.{account_number}@govsmart.go.id"
            if get_user_by_email(db, email):
                continue
            db.add(User(
                email=email,
                nik_or_nip=f"19900000000000{department.id:02d}{account_number:02d}",
                password_hash=password_hash,
                role="admin",
                dept_id=department.id,
            ))
            created += 1

    if created:
        db.commit()
    return created