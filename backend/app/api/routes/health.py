from fastapi import APIRouter
from app.db.mongo import db_manager
from app.services.face_service import get_model_status

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """
    System Health Check.
    Returns database state ('connected', 'disconnected', 'not_configured')
    and AI face model state ('ready', 'not_loaded', 'unavailable').
    Does NOT trigger heavy AI model loading during health check.
    """
    db_status = db_manager.get_status()
    face_status = get_model_status()

    return {
        "status": "ok",
        "message": "Smart Attendance API is running",
        "database": db_status,
        "face_model": face_status,
    }
