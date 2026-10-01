import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.crud.department import seed_departments
from app.crud.user import seed_super_admin, create_user
from app.schemas.user import UserCreate
from app.core.security import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed default data for test run
    seed_departments(session)
    seed_super_admin(session)
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def warga_user(db):
    user_in = UserCreate(
        email="warga.test@lamongan.go.id",
        nik_or_nip="3524010101950001",
        password="Password123!"
    )
    return create_user(db, user_in, role="warga")

@pytest.fixture(scope="function")
def warga_headers(warga_user):
    token = create_access_token(subject=warga_user.email)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def super_admin_headers(db):
    token = create_access_token(subject="superadmin@govsmart.go.id")
    return {"Authorization": f"Bearer {token}"}
