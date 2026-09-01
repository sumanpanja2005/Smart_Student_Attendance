import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status

from app.core.security import hash_password
from app.db.mongo import db_manager
from app.schemas.student import StudentCreate, StudentUpdate
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.user import UserResponse

logger = logging.getLogger("uvicorn.error")


def sanitize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Converts MongoDB _id to string id and removes sensitive fields."""
    if doc is None:
        return None
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res["_id"])
        del res["_id"]
    res.pop("password_hash", None)
    return res


class AcademicService:
    @staticmethod
    def create_student(data: StudentCreate) -> Dict[str, Any]:
        """
        Creates a User account and corresponding Student profile in a controlled operation.
        Rolls back user account creation if student document insertion fails.
        """
        db = db_manager.db
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_531_SERVICE_UNAVAILABLE if hasattr(status, "HTTP_531_SERVICE_UNAVAILABLE") else 503,
                detail="Database connection is unavailable",
            )

        # 1. Prepare User document
        now = datetime.now(timezone.utc)
        user_doc = {
            "email": data.email.lower().strip(),
            "password_hash": hash_password(data.password),
            "role": "STUDENT",
            "first_name": data.first_name.strip(),
            "last_name": data.last_name.strip(),
            "phone": data.phone.strip() if data.phone else None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        # 2. Insert User document
        try:
            user_res = db.users.insert_one(user_doc)
            user_id = str(user_res.inserted_id)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email '{data.email}' already exists.",
            )
        except Exception as exc:
            logger.error(f"Failed to create user account for student: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account.",
            )

        # 3. Prepare Student profile document
        student_doc = {
            "user_id": user_id,
            "student_id": data.student_id.strip(),
            "roll_number": data.roll_number.strip(),
            "department": data.department.strip(),
            "semester": data.semester,
            "section": data.section.strip().upper(),
            "class_id": data.class_id,
            "admission_year": data.admission_year,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        # 4. Insert Student document (with rollback if duplicate student_id)
        try:
            student_res = db.students.insert_one(student_doc)
            student_id_pk = str(student_res.inserted_id)
        except DuplicateKeyError as exc:
            # Rollback: delete created user account
            db.users.delete_one({"_id": user_res.inserted_id})
            err_msg = str(exc)
            if "student_id" in err_msg:
                detail = f"Student ID '{data.student_id}' is already registered."
            else:
                detail = "Duplicate entry detected for student record."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        except Exception as exc:
            # Rollback user
            db.users.delete_one({"_id": user_res.inserted_id})
            logger.error(f"Failed to create student profile: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create student profile.",
            )

        # Return populated response
        student_doc["id"] = student_id_pk
        del student_doc["_id"]
        user_doc["id"] = user_id
        del user_doc["_id"]
        user_doc.pop("password_hash", None)
        student_doc["user"] = user_doc
        return student_doc

    @staticmethod
    def create_teacher(data: TeacherCreate) -> Dict[str, Any]:
        """
        Creates a User account and corresponding Teacher profile in a controlled operation.
        Rolls back user creation if teacher document fails.
        """
        db = db_manager.db
        if db is None:
            raise HTTPException(
                status_code=503, detail="Database connection is unavailable"
            )

        now = datetime.now(timezone.utc)
        user_doc = {
            "email": data.email.lower().strip(),
            "password_hash": hash_password(data.password),
            "role": "TEACHER",
            "first_name": data.first_name.strip(),
            "last_name": data.last_name.strip(),
            "phone": data.phone.strip() if data.phone else None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        try:
            user_res = db.users.insert_one(user_doc)
            user_id = str(user_res.inserted_id)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email '{data.email}' already exists.",
            )
        except Exception as exc:
            logger.error(f"Failed to create user account for teacher: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account.",
            )

        teacher_doc = {
            "user_id": user_id,
            "employee_id": data.employee_id.strip(),
            "department": data.department.strip(),
            "designation": data.designation.strip(),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        try:
            teacher_res = db.teachers.insert_one(teacher_doc)
            teacher_id_pk = str(teacher_res.inserted_id)
        except DuplicateKeyError as exc:
            db.users.delete_one({"_id": user_res.inserted_id})
            err_msg = str(exc)
            if "employee_id" in err_msg:
                detail = f"Employee ID '{data.employee_id}' is already registered."
            else:
                detail = "Duplicate entry detected for teacher record."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        except Exception as exc:
            db.users.delete_one({"_id": user_res.inserted_id})
            logger.error(f"Failed to create teacher profile: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create teacher profile.",
            )

        teacher_doc["id"] = teacher_id_pk
        del teacher_doc["_id"]
        user_doc["id"] = user_id
        del user_doc["_id"]
        user_doc.pop("password_hash", None)
        teacher_doc["user"] = user_doc
        return teacher_doc
