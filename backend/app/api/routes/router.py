from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.students import router as students_router
from app.api.routes.teachers import router as teachers_router
from app.api.routes.subjects import router as subjects_router
from app.api.routes.classes import router as classes_router
from app.api.routes.face import router as face_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.reports import router as reports_router
from app.api.routes.audit import router as audit_router
from app.api.routes.system import router as system_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(subjects_router)
api_router.include_router(classes_router)
api_router.include_router(face_router)
api_router.include_router(attendance_router)
api_router.include_router(analytics_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
api_router.include_router(audit_router)
api_router.include_router(system_router)
