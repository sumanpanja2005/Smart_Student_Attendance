from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from app.db.mongo import db_manager
from app.schemas.user import UserResponse, UserCreate, UserUpdate, UserStatusUpdate
from app.api.deps import get_current_user, require_admin
from app.services.academic_service import sanitize_doc
from app.services.audit_service import AuditService
from app.services.security_audit_service import SecurityAuditService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_admin),
):
    """Admin-only endpoint listing platform users with optional filters."""
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    query = {}
    if role:
        query["role"] = role.upper()
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
        ]

    users = list(db.users.find(query).sort("created_at", -1))
    return [UserResponse(**sanitize_doc(u)) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate, current_user: dict = Depends(require_admin)
):
    """
    Admin-only endpoint to create a platform user (ADMIN, TEACHER, or STUDENT).
    Allows existing Admin to create another Admin account.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    existing = db.users.find_one({"email": data.email.lower().strip()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    from app.core.security import hash_password
    now = datetime.now(timezone.utc)
    user_doc = {
        "email": data.email.lower().strip(),
        "password_hash": hash_password(data.password),
        "role": data.role.upper(),
        "first_name": data.first_name.strip(),
        "last_name": data.last_name.strip(),
        "phone": data.phone.strip() if data.phone else None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    res = db.users.insert_one(user_doc)
    user_id = str(res.inserted_id)

    AuditService.log_event(
        action="USER_CREATED",
        event_type="USER_CREATED",
        resource_type="USER",
        resource_id=user_id,
        message=f"Admin created user {data.email} with role {data.role}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    created_user = db.users.find_one({"_id": res.inserted_id})
    return UserResponse(**sanitize_doc(created_user))


@router.get("/{id}", response_model=UserResponse)
def get_user(id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves user profile by ID (Admin or Self only)."""
    if current_user["role"] != "ADMIN" and current_user["id"] != id:
        SecurityAuditService.log_idor_attempt(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            target_resource_type="USER",
            target_resource_id=id,
        )
        raise HTTPException(status_code=403, detail="Permission denied")

    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    db = db_manager.db
    user = db.users.find_one({"_id": ObjectId(id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**sanitize_doc(user))


@router.put("/{id}", response_model=UserResponse)
def update_user(
    id: str, data: UserUpdate, current_user: dict = Depends(get_current_user)
):
    """
    Updates user details.
    Non-admin users cannot change their role, user_id, or active status.
    """
    if current_user["role"] != "ADMIN" and current_user["id"] != id:
        SecurityAuditService.log_idor_attempt(
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            target_resource_type="USER",
            target_resource_id=id,
        )
        raise HTTPException(status_code=403, detail="Permission denied")

    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    db = db_manager.db
    user = db.users.find_one({"_id": ObjectId(id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_fields = {}
    if data.first_name is not None:
        update_fields["first_name"] = data.first_name.strip()
    if data.last_name is not None:
        update_fields["last_name"] = data.last_name.strip()
    if data.phone is not None:
        update_fields["phone"] = data.phone.strip()

    # Role and Status changes restricted to ADMIN
    if current_user["role"] == "ADMIN":
        if data.role is not None:
            update_fields["role"] = data.role
        if data.is_active is not None:
            update_fields["is_active"] = data.is_active

    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        db.users.update_one({"_id": ObjectId(id)}, {"$set": update_fields})
        AuditService.log_event(
            action="USER_UPDATED",
            event_type="USER_UPDATED",
            resource_type="USER",
            resource_id=id,
            message=f"User {user.get('email')} updated profile.",
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
        )

    updated_user = db.users.find_one({"_id": ObjectId(id)})
    return UserResponse(**sanitize_doc(updated_user))


@router.patch("/{id}/status", response_model=UserResponse)
def update_user_status(
    id: str, data: UserStatusUpdate, current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint to activate or deactivate user accounts (Soft deactivation)."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    db = db_manager.db
    user = db.users.find_one({"_id": ObjectId(id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.users.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_active": data.is_active, "updated_at": datetime.now(timezone.utc)}},
    )

    # Sync is_active status to student/teacher profiles if applicable
    db.students.update_many({"user_id": id}, {"$set": {"is_active": data.is_active}})
    db.teachers.update_many({"user_id": id}, {"$set": {"is_active": data.is_active}})

    event_type = "USER_DEACTIVATED" if not data.is_active else "USER_UPDATED"
    AuditService.log_event(
        action=event_type,
        event_type=event_type,
        resource_type="USER",
        resource_id=id,
        message=f"Admin set active status for user {user.get('email')} to {data.is_active}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )

    updated_user = db.users.find_one({"_id": ObjectId(id)})
    return UserResponse(**sanitize_doc(updated_user))
