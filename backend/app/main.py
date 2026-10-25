# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.config import settings
from app.database import engine, Base, SessionLocal, ensure_schema_compatibility
import app.models  # Register models
from app.crud.department import seed_departments
from app.crud.user import seed_super_admin, seed_admin_dinas
from app.api.api import api_router

# Create database tables automatically
Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed initial data
    db = SessionLocal()
    try:
        seed_departments(db)
        seed_super_admin(db)
        seed_admin_dinas(db)
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

import os
UPLOAD_DIR = os.environ.get("GOVSMART_UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount frontend build (dist) for production serving
FRONTEND_DIST = os.environ.get("FRONTEND_DIST_DIR", "/app/frontend-dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
