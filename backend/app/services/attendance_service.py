import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongo import db_manager
from app.services.attendance_repository import AttendanceRepository
from app.services.face_service import recognize_face_from_bytes

logger = logging.getLogger("uvicorn.error")


class AttendanceService:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    @classmethod
    def _get_teacher_doc(cls, user_id: str) -> Optional[dict]:
        db = cls._get_db()
        try:
            if ObjectId.is_valid(user_id):
                doc = db.teachers.find_one({"user_id": ObjectId(user_id)})
                if doc:
                    return doc
        except Exception:
            pass
        try:
            doc = db.teachers.find_one({"user_id": str(user_id)})
            if doc:
                return doc
        except Exception:
            pass
        try:
            if ObjectId.is_valid(user_id):
                doc = db.teachers.find_one({"_id": ObjectId(user_id)})
                if doc:
                    return doc
        except Exception:
            pass
        return None

    @classmethod
    def _get_student_doc(cls, student_id: str) -> Optional[dict]:
        db = cls._get_db()
        try:
            doc = db.students.find_one({"_id": ObjectId(student_id)})
            if doc:
                return doc
        except Exception:
            pass
        try:
            return db.students.find_one({"user_id": ObjectId(student_id)})
        except Exception:
            return db.students.find_one({"student_id": student_id})

    # --- SESSION CREATION & LIFECYCLE ---
    @classmethod
    def create_session(
        cls, current_user: dict, class_id: str, subject_id: str, session_date: Optional[str] = None
    ) -> dict:
        """
        Creates an attendance session.
        Verifies class & subject existence, and teacher assignment authorization.
        """
        db = cls._get_db()
        try:
            class_doc = db.classes.find_one({"_id": ObjectId(class_id)})
        except Exception:
            class_doc = None

        if not class_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with ID '{class_id}' not found.",
            )

        try:
            subject_doc = db.subjects.find_one({"_id": ObjectId(subject_id)})
        except Exception:
            subject_doc = None

        if not subject_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with ID '{subject_id}' not found.",
            )

        teacher_id_str = current_user["id"]
        if current_user["role"] == "TEACHER":
            teacher_doc = cls._get_teacher_doc(current_user["id"])
            if teacher_doc:
                teacher_id_str = str(teacher_doc["_id"])

            assigned_classes = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []
            assigned_subjects = [str(s) for s in teacher_doc.get("assigned_subject_ids", [])] if teacher_doc else []
            class_teacher_ids = [str(t) for t in class_doc.get("teacher_ids", [])]
            class_teacher_id = str(class_doc.get("class_teacher_id")) if class_doc.get("class_teacher_id") else None

            is_class_authorized = (
                str(class_id) in assigned_classes
                or teacher_id_str in class_teacher_ids
                or current_user["id"] in class_teacher_ids
                or class_teacher_id in (teacher_id_str, current_user["id"])
                or (len(assigned_classes) == 0 and len(class_teacher_ids) == 0 and class_teacher_id is None)
            )

            if not is_class_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned or authorized to create attendance sessions for this class.",
                )

        now = datetime.now(timezone.utc)
        session_data = {
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "teacher_id": teacher_id_str,
            "session_date": session_date if session_date else now.strftime("%Y-%m-%d"),
            "start_time": now.strftime("%H:%M:%S"),
            "status": "OPEN",
            "created_by": current_user["id"],
        }
        session_id = AttendanceRepository.create_session(session_data)
        session_doc = AttendanceRepository.get_session(session_id)
        return cls._enrich_session_doc(session_doc)

    @classmethod
    def close_session(cls, current_user: dict, session_id: str) -> dict:
        """Closes an OPEN attendance session (OPEN -> CLOSED)."""
        session = AttendanceRepository.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
            )

        if session["status"] != "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot close session with status '{session['status']}'. Transition only allowed from 'OPEN'.",
            )

        # Authorization check
        if current_user["role"] != "ADMIN":
            teacher_doc = cls._get_teacher_doc(current_user["id"])
            teacher_id_str = str(teacher_doc["_id"]) if teacher_doc else current_user["id"]
            if session["teacher_id"] != teacher_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to close this attendance session.",
                )

        now = datetime.now(timezone.utc)
        AttendanceRepository.update_session_status(session_id, "CLOSED", closed_at=now)
        updated = AttendanceRepository.get_session(session_id)
        return cls._enrich_session_doc(updated)

    @classmethod
    def cancel_session(cls, current_user: dict, session_id: str) -> dict:
        """Cancels an OPEN attendance session (OPEN -> CANCELLED)."""
        session = AttendanceRepository.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
            )

        if session["status"] != "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel session with status '{session['status']}'. Transition only allowed from 'OPEN'.",
            )

        # Authorization check
        if current_user["role"] != "ADMIN":
            teacher_doc = cls._get_teacher_doc(current_user["id"])
            teacher_id_str = str(teacher_doc["_id"]) if teacher_doc else current_user["id"]
            if session["teacher_id"] != teacher_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to cancel this attendance session.",
                )

        AttendanceRepository.update_session_status(session_id, "CANCELLED")
        updated = AttendanceRepository.get_session(session_id)
        return cls._enrich_session_doc(updated)

    # --- FACE RECOGNITION ATTENDANCE ---
    @classmethod
    def mark_face_attendance(cls, session_id: str, image_bytes: bytes) -> dict:
        """
        Server-side face-based attendance endpoint handler.
        Calls existing Step 3 face service helper, checks enrollment, duplicate check,
        and inserts attendance record.
        """
        session = AttendanceRepository.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
            )

        if session["status"] != "OPEN":
            return {
                "success": False,
                "recognized": False,
                "attendance_marked": False,
                "already_marked": False,
                "student_id": None,
                "message": f"Cannot mark attendance for a session with status '{session['status']}'.",
            }

        # Step 3 Server-Side Face Recognition
        recognized, student_id, sim, rec_msg = recognize_face_from_bytes(image_bytes)
        if not recognized or not student_id:
            return {
                "success": False,
                "recognized": False,
                "attendance_marked": False,
                "already_marked": False,
                "student_id": None,
                "similarity": sim,
                "message": rec_msg,
            }

        # Student Enrollment Validation
        student_doc = cls._get_student_doc(student_id)
        if not student_doc:
            return {
                "success": False,
                "recognized": True,
                "attendance_marked": False,
                "already_marked": False,
                "student_id": student_id,
                "similarity": sim,
                "message": "Recognized student profile not found in system.",
            }

        student_class_id = str(student_doc.get("class_id")) if student_doc.get("class_id") else None
        if not student_class_id or student_class_id != str(session["class_id"]):
            return {
                "success": False,
                "recognized": True,
                "attendance_marked": False,
                "already_marked": False,
                "student_id": student_id,
                "similarity": sim,
                "message": "Student is not enrolled in this class.",
            }

        # Duplicate Attendance Check
        existing = AttendanceRepository.get_session_record_for_student(
            session_id, student_id
        )
        if existing:
            return {
                "success": True,
                "recognized": True,
                "attendance_marked": False,
                "already_marked": True,
                "student_id": student_id,
                "similarity": sim,
                "status": existing["status"],
                "message": "Attendance already marked.",
            }

        # Create Attendance Record
        record_data = {
            "session_id": session_id,
            "student_id": student_id,
            "class_id": session["class_id"],
            "subject_id": session["subject_id"],
            "attendance_date": session["session_date"],
            "status": "PRESENT",
            "marked_by": session["teacher_id"],
            "marking_method": "FACE",
            "similarity": sim,
            "remarks": None,
        }
        success, rec_doc, is_dup = AttendanceRepository.create_attendance_record(record_data)
        if is_dup or not success:
            return {
                "success": True,
                "recognized": True,
                "attendance_marked": False,
                "already_marked": True,
                "student_id": student_id,
                "similarity": sim,
                "status": "PRESENT",
                "message": "Attendance already marked.",
            }

        return {
            "success": True,
            "recognized": True,
            "attendance_marked": True,
            "already_marked": False,
            "student_id": student_id,
            "similarity": sim,
            "status": "PRESENT",
            "message": "Attendance marked successfully.",
        }

    # --- MANUAL & BULK ATTENDANCE ---
    @classmethod
    def mark_manual_attendance(
        cls,
        current_user: dict,
        session_id: str,
        student_id: str,
        att_status: str,
        remarks: Optional[str] = None,
    ) -> dict:
        """Single manual attendance marking for student in session."""
        session = AttendanceRepository.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
            )

        if session["status"] != "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark manual attendance for a session with status '{session['status']}'.",
            )

        # Student Enrollment Validation
        student_doc = cls._get_student_doc(student_id)
        if not student_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found."
            )

        student_class_id = str(student_doc.get("class_id")) if student_doc.get("class_id") else None
        if not student_class_id or student_class_id != str(session["class_id"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is not enrolled in this class.",
            )

        # Duplicate Check
        existing = AttendanceRepository.get_session_record_for_student(
            session_id, student_id
        )
        if existing:
            return {
                "student_id": student_id,
                "success": True,
                "already_marked": True,
                "message": "Attendance already exists for this student.",
            }

        record_data = {
            "session_id": session_id,
            "student_id": student_id,
            "class_id": session["class_id"],
            "subject_id": session["subject_id"],
            "attendance_date": session["session_date"],
            "status": att_status,
            "marked_by": current_user["id"],
            "marking_method": "MANUAL",
            "similarity": None,
            "remarks": remarks,
        }
        success, rec_doc, is_dup = AttendanceRepository.create_attendance_record(record_data)
        return {
            "student_id": student_id,
            "success": success,
            "already_marked": is_dup,
            "message": "Attendance already exists for this student." if is_dup else "Manual attendance recorded successfully.",
        }

    @classmethod
    def bulk_manual_attendance(
        cls, current_user: dict, session_id: str, records: List[dict]
    ) -> dict:
        """
        Bulk manual attendance marking.
        Validates students against session class. Does NOT overwrite existing face records.
        """
        session = AttendanceRepository.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
            )

        if session["status"] != "OPEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark bulk attendance for a session with status '{session['status']}'.",
            )

        results = []
        successful_count = 0

        for item in records:
            st_id = item["student_id"]
            st_status = item["status"]
            st_remarks = item.get("remarks")

            student_doc = cls._get_student_doc(st_id)
            if not student_doc:
                results.append(
                    {
                        "student_id": st_id,
                        "success": False,
                        "already_marked": False,
                        "message": "Student not found.",
                    }
                )
                continue

            student_class_id = str(student_doc.get("class_id")) if student_doc.get("class_id") else None
            if not student_class_id or student_class_id != str(session["class_id"]):
                results.append(
                    {
                        "student_id": st_id,
                        "success": False,
                        "already_marked": False,
                        "message": "Student is not enrolled in this class.",
                    }
                )
                continue

            existing = AttendanceRepository.get_session_record_for_student(
                session_id, st_id
            )
            if existing:
                results.append(
                    {
                        "student_id": st_id,
                        "success": False,
                        "already_marked": True,
                        "message": "Attendance already exists.",
                    }
                )
                continue

            record_data = {
                "session_id": session_id,
                "student_id": st_id,
                "class_id": session["class_id"],
                "subject_id": session["subject_id"],
                "attendance_date": session["session_date"],
                "status": st_status,
                "marked_by": current_user["id"],
                "marking_method": "MANUAL",
                "similarity": None,
                "remarks": st_remarks,
            }
            success, rec_doc, is_dup = AttendanceRepository.create_attendance_record(record_data)
            if success and not is_dup:
                successful_count += 1
                results.append(
                    {
                        "student_id": st_id,
                        "success": True,
                        "already_marked": False,
                        "message": "Attendance recorded.",
                    }
                )
            else:
                results.append(
                    {
                        "student_id": st_id,
                        "success": False,
                        "already_marked": True,
                        "message": "Attendance already exists.",
                    }
                )

        return {
            "session_id": session_id,
            "total_processed": len(records),
            "successful_count": successful_count,
            "results": results,
        }

    # --- ATTENDANCE CORRECTION ---
    @classmethod
    def update_attendance_record(
        cls, current_user: dict, record_id: str, new_status: Optional[str], remarks: Optional[str]
    ) -> dict:
        """
        Explicit attendance correction endpoint.
        Works even on CLOSED sessions for authorized users (Admin or assigned Teacher).
        Sets marking_method = 'MANUAL' while preserving original similarity score.
        """
        record = AttendanceRepository.get_attendance_record(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found."
            )

        session = AttendanceRepository.get_session(record["session_id"])
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Associated session not found."
            )

        # Authorization check
        if current_user["role"] != "ADMIN":
            teacher_doc = cls._get_teacher_doc(current_user["id"])
            teacher_id_str = str(teacher_doc["_id"]) if teacher_doc else current_user["id"]
            if session["teacher_id"] != teacher_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to correct attendance for this session.",
                )

        update_fields = {"marking_method": "MANUAL"}
        if new_status:
            update_fields["status"] = new_status
        if remarks is not None:
            update_fields["remarks"] = remarks

        updated = AttendanceRepository.update_attendance_record(record_id, update_fields)
        return cls._enrich_record_doc(updated)

    # --- ENRICHMENT HELPERS ---
    @classmethod
    def _enrich_session_doc(cls, doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        db = cls._get_db()
        try:
            class_doc = db.classes.find_one({"_id": ObjectId(doc["class_id"])})
        except Exception:
            class_doc = None

        try:
            subject_doc = db.subjects.find_one({"_id": ObjectId(doc["subject_id"])})
        except Exception:
            subject_doc = None

        try:
            teacher_doc = db.teachers.find_one({"_id": ObjectId(doc["teacher_id"])})
            if not teacher_doc:
                user_doc = db.users.find_one({"_id": ObjectId(doc["teacher_id"])})
            else:
                user_doc = db.users.find_one({"_id": teacher_doc.get("user_id")})
        except Exception:
            user_doc = None

        class_name = (class_doc.get("class_name") or class_doc.get("name")) if class_doc else None
        doc["class_name"] = class_name if class_name else "Class"

        subject_name = (subject_doc.get("subject_name") or subject_doc.get("name")) if subject_doc else None
        doc["subject_name"] = subject_name if subject_name else "Subject"

        if user_doc:
            doc["teacher_name"] = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip()
        else:
            doc["teacher_name"] = "Teacher"

        # Roster Awareness & Counts
        try:
            class_obj_id = ObjectId(doc["class_id"])
            enrolled_students = list(db.students.find({"$or": [{"class_id": doc["class_id"]}, {"class_id": class_obj_id}]}))
        except Exception:
            enrolled_students = list(db.students.find({"class_id": doc["class_id"]}))

        doc["total_students"] = len(enrolled_students)

        records = AttendanceRepository.list_session_records(doc["id"])
        present = sum(1 for r in records if r["status"] == "PRESENT")
        late = sum(1 for r in records if r["status"] == "LATE")
        excused = sum(1 for r in records if r["status"] == "EXCUSED")
        marked_absent = sum(1 for r in records if r["status"] == "ABSENT")

        # Roster-aware absent count: marked absent + enrolled students with no record
        marked_student_ids = {r["student_id"] for r in records}
        unmarked_count = sum(1 for st in enrolled_students if str(st["_id"]) not in marked_student_ids and str(st.get("user_id")) not in marked_student_ids)

        doc["present_count"] = present
        doc["late_count"] = late
        doc["excused_count"] = excused
        doc["absent_count"] = marked_absent + unmarked_count

        return doc

    @classmethod
    def _enrich_record_doc(cls, doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        db = cls._get_db()
        student_doc = cls._get_student_doc(doc["student_id"])
        if student_doc:
            user_doc = db.users.find_one({"_id": student_doc.get("user_id")})
            if user_doc:
                doc["student_name"] = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip()
            doc["roll_number"] = student_doc.get("roll_number", "")
        return doc
