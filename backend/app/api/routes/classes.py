from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import db_manager
from app.schemas.class_room import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassDetailResponse,
)
from app.schemas.student import StudentResponse
from app.schemas.teacher import TeacherResponse
from app.schemas.subject import SubjectResponse
from app.api.routes.students import populate_student
from app.api.routes.teachers import populate_teacher
from app.api.deps import get_current_user, require_admin
from app.services.academic_service import sanitize_doc
from app.services.audit_service import AuditService

router = APIRouter(prefix="/classes", tags=["Classes"])


def populate_class_detail(class_doc: dict) -> dict:
    """Populates class document with student, teacher, and subject entities."""
    db = db_manager.db
    cls = sanitize_doc(class_doc)

    student_ids = cls.get("student_ids", [])
    teacher_ids = cls.get("teacher_ids", [])
    subject_ids = cls.get("subject_ids", [])

    # Fetch students
    student_objs = []
    if student_ids:
        s_docs = list(
            db.students.find(
                {"_id": {"$in": [ObjectId(s) for s in student_ids if ObjectId.is_valid(s)]}}
            )
        )
        student_objs = [populate_student(s) for s in s_docs]

    # Fetch teachers
    teacher_objs = []
    if teacher_ids:
        t_docs = list(
            db.teachers.find(
                {"_id": {"$in": [ObjectId(t) for t in teacher_ids if ObjectId.is_valid(t)]}}
            )
        )
        teacher_objs = [populate_teacher(t) for t in t_docs]

    # Fetch subjects
    subject_objs = []
    if subject_ids:
        sub_docs = list(
            db.subjects.find(
                {"_id": {"$in": [ObjectId(sub) for sub in subject_ids if ObjectId.is_valid(sub)]}}
            )
        )
        subject_objs = [sanitize_doc(sub) for sub in sub_docs]

    cls["students"] = student_objs
    cls["teachers"] = teacher_objs
    cls["subjects"] = subject_objs
    return cls


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    data: ClassCreate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to create a class section."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    now = datetime.now(timezone.utc)
    class_doc = {
        "class_name": data.class_name.strip(),
        "department": data.department.strip(),
        "semester": data.semester,
        "section": data.section.strip().upper(),
        "academic_year": data.academic_year.strip(),
        "student_ids": [],
        "teacher_ids": [],
        "subject_ids": [],
        "created_at": now,
        "updated_at": now,
    }

    res = db.classes.insert_one(class_doc)
    cls_id = str(res.inserted_id)
    class_doc["id"] = cls_id
    del class_doc["_id"]

    AuditService.log_event(
        action="CLASS_CREATED",
        event_type="CLASS_CREATED",
        resource_type="CLASS",
        resource_id=cls_id,
        message=f"Admin created class section {data.class_name}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return ClassResponse(**class_doc)


@router.get("", response_model=List[ClassResponse])
def list_classes(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
    teacher_id: Optional[str] = None,
    student_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Lists classes with optional filters."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    query = {}
    if department:
        query["department"] = department
    if semester:
        query["semester"] = semester
    if section:
        query["section"] = section.upper()
    if teacher_id:
        query["teacher_ids"] = teacher_id
    if student_id:
        query["student_ids"] = student_id

    classes = list(db.classes.find(query).sort("class_name", 1))
    return [ClassResponse(**sanitize_doc(c)) for c in classes]


@router.get("/{id}", response_model=ClassDetailResponse)
def get_class(id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves class details with populated students, teachers, and subjects."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Class ID format")

    db = db_manager.db
    class_doc = db.classes.find_one({"_id": ObjectId(id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    return ClassDetailResponse(**populate_class_detail(class_doc))


@router.put("/{id}", response_model=ClassResponse)
def update_class(
    id: str, data: ClassUpdate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to update class details."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Class ID format")

    db = db_manager.db
    class_doc = db.classes.find_one({"_id": ObjectId(id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    updates = {"updated_at": datetime.now(timezone.utc)}
    if data.class_name is not None:
        updates["class_name"] = data.class_name.strip()
    if data.department is not None:
        updates["department"] = data.department.strip()
    if data.semester is not None:
        updates["semester"] = data.semester
    if data.section is not None:
        updates["section"] = data.section.strip().upper()
    if data.academic_year is not None:
        updates["academic_year"] = data.academic_year.strip()

    db.classes.update_one({"_id": ObjectId(id)}, {"$set": updates})

    AuditService.log_event(
        action="CLASS_UPDATED",
        event_type="CLASS_UPDATED",
        resource_type="CLASS",
        resource_id=id,
        message=f"Admin updated class {id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    updated = db.classes.find_one({"_id": ObjectId(id)})
    return ClassResponse(**sanitize_doc(updated))


@router.post("/{class_id}/students/{student_id}", response_model=ClassResponse)
def assign_student_to_class(
    class_id: str, student_id: str, current_user: dict = Depends(require_admin)
):
    """Assigns a student to a class section."""
    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = db_manager.db
    class_doc = db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    student_doc = db.students.find_one({"_id": ObjectId(student_id)})
    if not student_doc:
        raise HTTPException(status_code=404, detail="Student record not found")

    if not student_doc.get("is_active", True):
        raise HTTPException(status_code=400, detail="Cannot assign inactive student to class")

    if student_id in class_doc.get("student_ids", []):
        raise HTTPException(status_code=400, detail="Student is already assigned to this class")

    # Add to class and update student's class_id
    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {
            "$addToSet": {"student_ids": student_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"class_id": class_id, "updated_at": datetime.now(timezone.utc)}},
    )

    AuditService.log_event(
        action="STUDENT_ENROLLED",
        event_type="ACADEMIC_STRUCTURE_CHANGED",
        resource_type="CLASS",
        resource_id=class_id,
        message=f"Enrolled student {student_id} into class {class_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    updated = db.classes.find_one({"_id": ObjectId(class_id)})
    return ClassResponse(**sanitize_doc(updated))


@router.delete("/{class_id}/students/{student_id}", response_model=ClassResponse)
def remove_student_from_class(
    class_id: str, student_id: str, current_user: dict = Depends(require_admin)
):
    """Removes a student from a class section."""
    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = db_manager.db
    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {
            "$pull": {"student_ids": student_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"class_id": None, "updated_at": datetime.now(timezone.utc)}},
    )

    updated = db.classes.find_one({"_id": ObjectId(class_id)})
    return ClassResponse(**sanitize_doc(updated))


@router.post("/{class_id}/teachers/{teacher_id}", response_model=ClassResponse)
def assign_teacher_to_class(
    class_id: str, teacher_id: str, current_user: dict = Depends(require_admin)
):
    """Assigns a teacher to a class section."""
    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(teacher_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = db_manager.db
    class_doc = db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    teacher_doc = db.teachers.find_one({"_id": ObjectId(teacher_id)})
    if not teacher_doc:
        raise HTTPException(status_code=404, detail="Teacher record not found")

    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {
            "$addToSet": {"teacher_ids": teacher_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {
            "$addToSet": {"assigned_class_ids": class_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )

    AuditService.log_event(
        action="TEACHER_ASSIGNED",
        event_type="ACADEMIC_STRUCTURE_CHANGED",
        resource_type="CLASS",
        resource_id=class_id,
        message=f"Assigned teacher {teacher_id} to class {class_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    updated = db.classes.find_one({"_id": ObjectId(class_id)})
    return ClassResponse(**sanitize_doc(updated))


@router.delete("/{class_id}/teachers/{teacher_id}", response_model=ClassResponse)
def remove_teacher_from_class(
    class_id: str, teacher_id: str, current_user: dict = Depends(require_admin)
):
    """Removes a teacher from a class section."""
    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(teacher_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = db_manager.db
    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {
            "$pull": {"teacher_ids": teacher_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {
            "$pull": {"assigned_class_ids": class_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )

    updated = db.classes.find_one({"_id": ObjectId(class_id)})
    return ClassResponse(**sanitize_doc(updated))


@router.post("/{class_id}/subjects/{subject_id}", response_model=ClassResponse)
def assign_subject_to_class(
    class_id: str, subject_id: str, current_user: dict = Depends(require_admin)
):
    """Assigns a subject to a class section."""
    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(subject_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = db_manager.db
    class_doc = db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    subject_doc = db.subjects.find_one({"_id": ObjectId(subject_id)})
    if not subject_doc:
        raise HTTPException(status_code=404, detail="Subject record not found")

    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {
            "$addToSet": {"subject_ids": subject_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )

    updated = db.classes.find_one({"_id": ObjectId(class_id)})
    return ClassResponse(**sanitize_doc(updated))


@router.delete("/{class_id}/subjects/{subject_id}", response_model=ClassResponse)
def remove_subject_from_class(
    class_id: str, subject_id: str, current_user: dict = Depends(require_admin)
):
    """Removes a subject assignment from a class section."""
    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(subject_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = db_manager.db
    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {
            "$pull": {"subject_ids": subject_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )

    updated = db.classes.find_one({"_id": ObjectId(class_id)})
    return ClassResponse(**sanitize_doc(updated))


@router.delete("/{id}")
def delete_class(id: str, current_user: dict = Depends(require_admin)):
    """Admin-only endpoint to delete a class section."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Class ID format")

    db = db_manager.db
    res = db.classes.delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")

    # Unassign class_id from students
    db.students.update_many({"class_id": id}, {"$set": {"class_id": None}})
    # Pull class_id from assigned teachers
    db.teachers.update_many({}, {"$pull": {"assigned_class_ids": id}})

    AuditService.log_event(
        action="CLASS_DELETED",
        event_type="CLASS_DELETED",
        resource_type="CLASS",
        resource_id=id,
        message=f"Admin deleted class section {id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    return {"status": "ok", "message": "Class section deleted successfully."}
