from fastapi import APIRouter
from app.api.endpoints import auth, admin, departments, reports, chat

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autentikasi"])
api_router.include_router(admin.router, prefix="/admin", tags=["Manajemen Admin & Profil"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departemen / Dinas"])
api_router.include_router(reports.router, prefix="/reports", tags=["Laporan Pengaduan"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chatbot"])
