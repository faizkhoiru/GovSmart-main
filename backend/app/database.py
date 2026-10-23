# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, inspect, text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    """Repair the old MySQL audit schema created before admin_id became nullable."""
    if engine.dialect.name != "mysql":
        return
    with engine.begin() as connection:
        if "audit_logs" not in inspect(connection).get_table_names():
            return
        connection.execute(text("ALTER TABLE audit_logs MODIFY COLUMN admin_id INT NULL"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
