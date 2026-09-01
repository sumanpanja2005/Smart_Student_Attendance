from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import db_manager
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.schemas.user import UserResponse
from app.api.deps import get_current_user, require_admin, require_teacher
from app.services.academic_service import AcademicService, sanitize_doc
from app.services.audit_service import AuditService
from app.services.security_audit_service import SecurityAuditService

router = APIRouter(prefix="/students", tags=["Students"])


def populate_student(student_doc: dict) -> dict:
    """Populates student document with user profile details."""
    db = db_manager.db
    student = sanitize_doc(student_doc)
    user_id = student.get("user_id")
    if user_id and ObjectId.is_valid(user_id):
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        student["user"] = sanitize_doc(user_doc)
    return student


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to create a student profile and user account atomically."""
    created = AcademicService.create_student(data)
    AuditService.log_event(
        action="STUDENT_CREATED",
        event_type="STUDENT_CREATED",
        resource_type="STUDENT",
        resource_id=created.get("id"),
        message=f"Admin created student account for {data.first_name} {data.last_name} ({data.student_id})",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return StudentResponse(**created)


@router.get("/me", response_model=StudentResponse)
def get_my_student_profile(current_user: dict = Depends(get_current_user)):
    """Self-service endpoint for logged-in students to fetch their own profile."""
    if current_user["role"] != "STUDENT":
        SecurityAuditService.log_unauthorized_access(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            resource_type="STUDENT",
            endpoint="/students/me",
        )
        raise HTTPException(
            status_code=403, detail="Self-service endpoint is restricted to Students."
        )

    db = db_manager.db
    student_doc = db.students.find_one({"user_id": current_user["id"]})
    if not student_doc:
        raise HTTPException(
            status_code=404, detail="Student profile record not found."
        )

    return StudentResponse(**populate_student(student_doc))


@router.get("", response_model=List[StudentResponse])
def list_students(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
    class_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_teacher),
):
    """Lists student records. Teachers can view students; query filters supported."""
    db = db_manager.db
    query = {}
    if department:
        query["department"] = department
    if semester:
        query["semester"] = semester
    if section:
        query["section"] = section.upper()
    if class_id:
        query["class_id"] = class_id

    if search:
        query["$or"] = [
            {"student_id": {"$regex": search, "$options": "i"}},
            {"roll_number": {"$regex": search, "$options": "i"}},
        ]

    student_docs = list(db.students.find(query).sort("created_at", -1))
    return [StudentResponse(**populate_student(s)) for s in student_docs]


@router.get("/{id}", response_model=StudentResponse)
def get_student(id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves student details by ID (Admin, Teacher, or Student Self)."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Student ID format")

    db = db_manager.db
    student_doc = db.students.find_one({"_id": ObjectId(id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student record not found")

    # Authorization Check
    if current_user["role"] == "STUDENT" and current_user["id"] != str(student_doc.get("user_id")):
        SecurityAuditService.log_idor_attempt(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            target_resource_type="STUDENT",
            target_resource_id=id,
        )
        raise HTTPException(status_code=403, detail="Permission denied")

    return StudentResponse(**populate_student(student_doc))


@router.put("/{id}", response_model=StudentResponse)
def update_student(
    id: str, data: StudentUpdate, current_user: dict = Depends(get_current_user)
):
    """
    Updates student record.
    Students can update their own phone/profile; Admin can update academic info & active status.
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Student ID format")

    db = db_manager.db
    student_doc = db.students.find_one({"_id": ObjectId(id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student not found")

    is_admin = current_user["role"] == "ADMIN"
    is_self = current_user["id"] == str(student_doc.get("user_id"))

    if not is_admin and not is_self:
        SecurityAuditService.log_idor_attempt(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            target_resource_type="STUDENT",
            target_resource_id=id,
        )
        raise HTTPException(status_code=403, detail="Permission denied")

    student_updates = {"updated_at": datetime.now(timezone.utc)}
    user_updates = {"updated_at": datetime.now(timezone.utc)}

    # Personal info
    if data.first_name is not None:
        user_updates["first_name"] = data.first_name.strip()
    if data.last_name is not None:
        user_updates["last_name"] = data.last_name.strip()
    if data.phone is not None:
        user_updates["phone"] = data.phone.strip()

    # Academic fields (Only Admin can update department, semester, section, class_id)
    if is_admin:
        if data.department is not None:
            student_updates["department"] = data.department.strip()
        if data.semester is not None:
            student_updates["semester"] = data.semester
        if data.section is not None:
            student_updates["section"] = data.section.strip().upper()
        if data.class_id is not None:
            student_updates["class_id"] = data.class_id
        if data.is_active is not None:
            student_updates["is_active"] = data.is_active
            user_updates["is_active"] = data.is_active

    if len(user_updates) > 1 and ObjectId.is_valid(student_doc.get("user_id")):
        db.users.update_one(
            {"_id": ObjectId(student_doc["user_id"])}, {"$set": user_updates}
        )

    if len(student_updates) > 1:
        db.students.update_one({"_id": ObjectId(id)}, {"$set": student_updates})
        AuditService.log_event(
            action="STUDENT_UPDATED",
            event_type="STUDENT_UPDATED",
            resource_type="STUDENT",
            resource_id=id,
            message=f"Student record {id} updated.",
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
        )

    updated_student = db.students.find_one({"_id": ObjectId(id)})
    return StudentResponse(**populate_student(updated_student))


@router.delete("/{id}")
def deactivate_student(
    id: str, current_user: dict = Depends(require_admin)
):
    """Admin-only soft deactivation for student profiles."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Student ID format")

    db = db_manager.db
    student_doc = db.students.find_one({"_id": ObjectId(id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student not found")

    db.students.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )

    if ObjectId.is_valid(student_doc.get("user_id")):
        db.users.update_one(
            {"_id": ObjectId(student_doc["user_id"])},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
        )

    AuditService.log_event(
        action="STUDENT_DEACTIVATED",
        event_type="STUDENT_DEACTIVATED",
        resource_type="STUDENT",
        resource_id=id,
        message=f"Admin deactivated student record {id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    return {"status": "ok", "message": "Student account deactivated successfully."}
