# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, inspect, text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    """Repair schema for evolved models (nullable cols, new columns)."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    with engine.begin() as connection:
        # Legacy: make admin_id nullable on audit_logs (MySQL only)
        if engine.dialect.name == "mysql" and "audit_logs" in table_names:
            cols = {c["name"] for c in inspector.get_columns("audit_logs")}
            if "admin_id" in cols:
                connection.execute(text("ALTER TABLE audit_logs MODIFY COLUMN admin_id INT NULL"))
        # Add evolved columns to reports if not present
        if "reports" in table_names:
            cols = {c["name"] for c in inspector.get_columns("reports")}
            if "foto_feedback" not in cols:
                connection.execute(text("ALTER TABLE reports ADD COLUMN foto_feedback VARCHAR(255) NULL"))
            if "created_at" not in cols:
                connection.execute(text("ALTER TABLE reports ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NULL"))
            if "rating_kepuasan" not in cols:
                connection.execute(text("ALTER TABLE reports ADD COLUMN rating_kepuasan INT NULL"))
            if "ulasan_warga" not in cols:
                connection.execute(text("ALTER TABLE reports ADD COLUMN ulasan_warga TEXT NULL"))
            if "rated_at" not in cols:
                connection.execute(text("ALTER TABLE reports ADD COLUMN rated_at DATETIME NULL"))
        # Add optional profile columns to users if not present
        if "users" in table_names:
            ucols = {c["name"] for c in inspector.get_columns("users")}
            if "nama_lengkap" not in ucols:
                connection.execute(text("ALTER TABLE users ADD COLUMN nama_lengkap VARCHAR(120) NULL"))
            if "no_telepon" not in ucols:
                connection.execute(text("ALTER TABLE users ADD COLUMN no_telepon VARCHAR(30) NULL"))
            if "alamat" not in ucols:
                connection.execute(text("ALTER TABLE users ADD COLUMN alamat VARCHAR(255) NULL"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
