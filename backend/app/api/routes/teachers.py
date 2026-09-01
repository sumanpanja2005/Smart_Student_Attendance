from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import db_manager
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse
from app.api.deps import get_current_user, require_admin, require_teacher
from app.services.academic_service import AcademicService, sanitize_doc
from app.services.audit_service import AuditService
from app.services.security_audit_service import SecurityAuditService

router = APIRouter(prefix="/teachers", tags=["Teachers"])


def populate_teacher(teacher_doc: dict) -> dict:
    """Populates teacher document with user profile details."""
    db = db_manager.db
    teacher = sanitize_doc(teacher_doc)
    user_id = teacher.get("user_id")
    if user_id and ObjectId.is_valid(user_id):
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        teacher["user"] = sanitize_doc(user_doc)
    return teacher


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    data: TeacherCreate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to create a teacher profile and user account atomically."""
    created = AcademicService.create_teacher(data)
    AuditService.log_event(
        action="TEACHER_CREATED",
        event_type="TEACHER_CREATED",
        resource_type="TEACHER",
        resource_id=created.get("id"),
        message=f"Admin created teacher account for {data.first_name} {data.last_name} ({data.employee_id})",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return TeacherResponse(**created)


@router.get("/me", response_model=TeacherResponse)
def get_my_teacher_profile(current_user: dict = Depends(get_current_user)):
    """Self-service endpoint for logged-in teachers to fetch their own profile."""
    if current_user["role"] != "TEACHER":
        SecurityAuditService.log_unauthorized_access(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            resource_type="TEACHER",
            endpoint="/teachers/me",
        )
        raise HTTPException(
            status_code=403, detail="Self-service endpoint is restricted to Teachers."
        )

    db = db_manager.db
    teacher_doc = db.teachers.find_one({"user_id": current_user["id"]})
    if not teacher_doc:
        raise HTTPException(
            status_code=404, detail="Teacher profile record not found."
        )

    return TeacherResponse(**populate_teacher(teacher_doc))


@router.get("", response_model=List[TeacherResponse])
def list_teachers(
    department: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_teacher),
):
    """Lists teacher records."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    query = {}
    if department:
        query["department"] = department
    if search:
        query["$or"] = [
            {"employee_id": {"$regex": search, "$options": "i"}},
            {"department": {"$regex": search, "$options": "i"}},
        ]

    teachers = list(db.teachers.find(query).sort("created_at", -1))
    return [TeacherResponse(**populate_teacher(t)) for t in teachers]


@router.get("/{id}", response_model=TeacherResponse)
def get_teacher(id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves teacher details by ID (Admin, Teacher, or self)."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Teacher ID format")

    db = db_manager.db
    teacher_doc = db.teachers.find_one({"_id": ObjectId(id)})
    if not teacher_doc:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return TeacherResponse(**populate_teacher(teacher_doc))


@router.put("/{id}", response_model=TeacherResponse)
def update_teacher(
    id: str, data: TeacherUpdate, current_user: dict = Depends(get_current_user)
):
    """Updates teacher details (Admin or Teacher self)."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Teacher ID format")

    db = db_manager.db
    teacher_doc = db.teachers.find_one({"_id": ObjectId(id)})
    if not teacher_doc:
        raise HTTPException(status_code=404, detail="Teacher not found")

    is_admin = current_user["role"] == "ADMIN"
    is_self = current_user["id"] == str(teacher_doc.get("user_id"))

    if not is_admin and not is_self:
        SecurityAuditService.log_idor_attempt(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            target_resource_type="TEACHER",
            target_resource_id=id,
        )
        raise HTTPException(status_code=403, detail="Permission denied")

    now = datetime.now(timezone.utc)
    teacher_updates = {"updated_at": now}
    user_updates = {"updated_at": now}

    if data.first_name is not None:
        user_updates["first_name"] = data.first_name.strip()
    if data.last_name is not None:
        user_updates["last_name"] = data.last_name.strip()
    if data.phone is not None:
        user_updates["phone"] = data.phone.strip()

    if data.department is not None:
        teacher_updates["department"] = data.department.strip()
    if data.designation is not None:
        teacher_updates["designation"] = data.designation.strip()

    if is_admin and data.is_active is not None:
        teacher_updates["is_active"] = data.is_active
        user_updates["is_active"] = data.is_active

    if len(user_updates) > 1 and ObjectId.is_valid(teacher_doc.get("user_id")):
        db.users.update_one(
            {"_id": ObjectId(teacher_doc["user_id"])}, {"$set": user_updates}
        )

    if len(teacher_updates) > 1:
        db.teachers.update_one({"_id": ObjectId(id)}, {"$set": teacher_updates})
        AuditService.log_event(
            action="TEACHER_UPDATED",
            event_type="TEACHER_UPDATED",
            resource_type="TEACHER",
            resource_id=id,
            message=f"Teacher profile {id} updated.",
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
        )

    updated_teacher = db.teachers.find_one({"_id": ObjectId(id)})
    return TeacherResponse(**populate_teacher(updated_teacher))


@router.delete("/{id}")
def deactivate_teacher(
    id: str, current_user: dict = Depends(require_admin)
):
    """Admin-only soft deactivation for teacher profiles."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Teacher ID format")

    db = db_manager.db
    teacher_doc = db.teachers.find_one({"_id": ObjectId(id)})
    if not teacher_doc:
        raise HTTPException(status_code=404, detail="Teacher not found")

    db.teachers.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )

    if ObjectId.is_valid(teacher_doc.get("user_id")):
        db.users.update_one(
            {"_id": ObjectId(teacher_doc["user_id"])},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
        )

    AuditService.log_event(
        action="TEACHER_DEACTIVATED",
        event_type="TEACHER_DEACTIVATED",
        resource_type="TEACHER",
        resource_id=id,
        message=f"Admin deactivated teacher profile {id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    return {"status": "ok", "message": "Teacher account deactivated successfully."}
