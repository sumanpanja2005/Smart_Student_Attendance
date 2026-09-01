from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import db_manager
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.api.deps import get_current_user, require_admin
from app.services.academic_service import sanitize_doc
from app.services.audit_service import AuditService

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to create a subject."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    now = datetime.now(timezone.utc)
    subject_doc = {
        "subject_code": data.subject_code.strip().upper(),
        "subject_name": data.subject_name.strip(),
        "department": data.department.strip(),
        "semester": data.semester,
        "credits": data.credits,
        "description": data.description.strip() if data.description else None,
        "created_at": now,
        "updated_at": now,
    }

    try:
        res = db.subjects.insert_one(subject_doc)
        sub_id = str(res.inserted_id)
        subject_doc["id"] = sub_id
        del subject_doc["_id"]

        AuditService.log_event(
            action="SUBJECT_CREATED",
            event_type="SUBJECT_CREATED",
            resource_type="SUBJECT",
            resource_id=sub_id,
            message=f"Admin created subject {data.subject_code} ({data.subject_name})",
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
        )
        return SubjectResponse(**subject_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject code '{data.subject_code}' already exists.",
        )


@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Lists subjects with optional filters."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    query = {}
    if department:
        query["department"] = department
    if semester:
        query["semester"] = semester
    if search:
        query["$or"] = [
            {"subject_code": {"$regex": search, "$options": "i"}},
            {"subject_name": {"$regex": search, "$options": "i"}},
        ]

    subjects = list(db.subjects.find(query).sort("subject_code", 1))
    return [SubjectResponse(**sanitize_doc(s)) for s in subjects]


@router.get("/{id}", response_model=SubjectResponse)
def get_subject(id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves subject by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Subject ID format")

    db = db_manager.db
    subject = db.subjects.find_one({"_id": ObjectId(id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    return SubjectResponse(**sanitize_doc(subject))


@router.put("/{id}", response_model=SubjectResponse)
def update_subject(
    id: str, data: SubjectUpdate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to update subject details."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Subject ID format")

    db = db_manager.db
    subject = db.subjects.find_one({"_id": ObjectId(id)})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    updates = {"updated_at": datetime.now(timezone.utc)}
    if data.subject_name is not None:
        updates["subject_name"] = data.subject_name.strip()
    if data.department is not None:
        updates["department"] = data.department.strip()
    if data.semester is not None:
        updates["semester"] = data.semester
    if data.credits is not None:
        updates["credits"] = data.credits
    if data.description is not None:
        updates["description"] = data.description.strip()

    db.subjects.update_one({"_id": ObjectId(id)}, {"$set": updates})

    AuditService.log_event(
        action="SUBJECT_UPDATED",
        event_type="SUBJECT_UPDATED",
        resource_type="SUBJECT",
        resource_id=id,
        message=f"Admin updated subject {id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    updated = db.subjects.find_one({"_id": ObjectId(id)})
    return SubjectResponse(**sanitize_doc(updated))


@router.delete("/{id}")
def delete_subject(id: str, current_user: dict = Depends(require_admin)):
    """Admin-only endpoint to delete a subject."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid Subject ID format")

    db = db_manager.db
    res = db.subjects.delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Remove subject ID from any classes
    db.classes.update_many({}, {"$pull": {"subject_ids": id}})

    AuditService.log_event(
        action="SUBJECT_DELETED",
        event_type="SUBJECT_DELETED",
        resource_type="SUBJECT",
        resource_id=id,
        message=f"Admin deleted subject {id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return {"status": "ok", "message": "Subject deleted successfully."}
