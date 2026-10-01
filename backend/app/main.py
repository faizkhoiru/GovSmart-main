from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.database import engine, Base, SessionLocal
import app.models  # Register models
from app.crud.department import seed_departments
from app.crud.user import seed_super_admin
from app.api.api import api_router

# Create database tables automatically
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed initial data
    db = SessionLocal()
    try:
        seed_departments(db)
        seed_super_admin(db)
    except Exception as e:
        print(f"Error during database seeding: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to GovSmart API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
