import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.db.mongo import db_manager

logger = logging.getLogger("uvicorn.error")


class AttendanceRepository:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    # --- SESSIONS ---
    @classmethod
    def create_session(cls, session_data: dict) -> str:
        """Creates a new attendance session document."""
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        doc = {
            "class_id": str(session_data["class_id"]),
            "subject_id": str(session_data["subject_id"]),
            "teacher_id": str(session_data["teacher_id"]),
            "session_date": session_data.get("session_date", now.strftime("%Y-%m-%d")),
            "start_time": session_data.get("start_time", now.strftime("%H:%M:%S")),
            "end_time": session_data.get("end_time"),
            "status": session_data.get("status", "OPEN"),
            "created_by": str(session_data["created_by"]),
            "created_at": now,
            "closed_at": None,
        }
        res = db.attendance_sessions.insert_one(doc)
        return str(res.inserted_id)

    @classmethod
    def get_session(cls, session_id: str) -> Optional[dict]:
        """Retrieves an attendance session by ID."""
        db = cls._get_db()
        try:
            doc = db.attendance_sessions.find_one({"_id": ObjectId(session_id)})
            if doc:
                doc["id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    @classmethod
    def list_sessions(cls, filters: dict = None) -> List[dict]:
        """Lists attendance sessions with optional query filters."""
        db = cls._get_db()
        query = {}
        if filters:
            if filters.get("class_id"):
                query["class_id"] = str(filters["class_id"])
            if filters.get("subject_id"):
                query["subject_id"] = str(filters["subject_id"])
            if filters.get("teacher_id"):
                query["teacher_id"] = str(filters["teacher_id"])
            if filters.get("session_date"):
                query["session_date"] = filters["session_date"]
            if filters.get("status"):
                query["status"] = filters["status"]

        cursor = db.attendance_sessions.find(query).sort("created_at", -1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(doc)
        return results

    @classmethod
    def update_session_status(
        cls, session_id: str, new_status: str, closed_at: Optional[datetime] = None
    ) -> bool:
        """Updates session status ('CLOSED' or 'CANCELLED')."""
        db = cls._get_db()
        update_doc = {"status": new_status}
        if closed_at:
            update_doc["closed_at"] = closed_at
        res = db.attendance_sessions.update_one(
            {"_id": ObjectId(session_id)}, {"$set": update_doc}
        )
        return res.modified_count > 0

    # --- RECORDS ---
    @classmethod
    def create_attendance_record(
        cls, record_data: dict
    ) -> Tuple[bool, Optional[dict], bool]:
        """
        Creates an attendance record.
        Enforces (session_id, student_id) database unique constraint.
        Returns (success: bool, record_doc: Optional[dict], is_duplicate: bool).
        """
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        doc = {
            "session_id": str(record_data["session_id"]),
            "student_id": str(record_data["student_id"]),
            "class_id": str(record_data["class_id"]),
            "subject_id": str(record_data["subject_id"]),
            "attendance_date": record_data.get("attendance_date", now.strftime("%Y-%m-%d")),
            "status": record_data.get("status", "PRESENT"),
            "marked_by": str(record_data["marked_by"]),
            "marking_method": record_data.get("marking_method", "FACE"),
            "marked_at": now,
            "similarity": record_data.get("similarity"),
            "remarks": record_data.get("remarks"),
            "updated_at": now,
        }
        try:
            res = db.attendance_records.insert_one(doc)
            doc["id"] = str(res.inserted_id)
            return True, doc, False
        except DuplicateKeyError:
            # Duplicate key error caught gracefully
            existing = db.attendance_records.find_one(
                {
                    "session_id": str(record_data["session_id"]),
                    "student_id": str(record_data["student_id"]),
                }
            )
            if existing:
                existing["id"] = str(existing["_id"])
            return True, existing, True
        except Exception as exc:
            logger.error(f"Failed to create attendance record: {exc}")
            return False, None, False

    @classmethod
    def get_attendance_record(cls, record_id: str) -> Optional[dict]:
        """Retrieves an attendance record by ID."""
        db = cls._get_db()
        try:
            doc = db.attendance_records.find_one({"_id": ObjectId(record_id)})
            if doc:
                doc["id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    @classmethod
    def get_session_record_for_student(
        cls, session_id: str, student_id: str
    ) -> Optional[dict]:
        """Check if an attendance record exists for student in session."""
        db = cls._get_db()
        doc = db.attendance_records.find_one(
            {"session_id": str(session_id), "student_id": str(student_id)}
        )
        if doc:
            doc["id"] = str(doc["_id"])
        return doc

    @classmethod
    def list_session_records(cls, session_id: str) -> List[dict]:
        """Lists all attendance records for a session."""
        db = cls._get_db()
        cursor = db.attendance_records.find({"session_id": str(session_id)}).sort(
            "marked_at", 1
        )
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(doc)
        return results

    @classmethod
    def list_student_records(
        cls, student_id: str, filters: dict = None
    ) -> List[dict]:
        """Lists attendance records for a specific student with optional filters."""
        db = cls._get_db()
        query = {"student_id": str(student_id)}
        if filters:
            if filters.get("subject_id"):
                query["subject_id"] = str(filters["subject_id"])
            if filters.get("status"):
                query["status"] = filters["status"]
            if filters.get("date_from") or filters.get("date_to"):
                date_query = {}
                if filters.get("date_from"):
                    date_query["$gte"] = filters["date_from"]
                if filters.get("date_to"):
                    date_query["$lte"] = filters["date_to"]
                query["attendance_date"] = date_query

        cursor = db.attendance_records.find(query).sort("marked_at", -1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(doc)
        return results

    @classmethod
    def update_attendance_record(
        cls, record_id: str, update_fields: dict
    ) -> Optional[dict]:
        """
        Updates an existing attendance record.
        Preserves original similarity value if original method was FACE.
        Sets updated_at timestamp.
        """
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        set_doc = {"updated_at": now}

        if "status" in update_fields and update_fields["status"]:
            set_doc["status"] = update_fields["status"]
        if "remarks" in update_fields:
            set_doc["remarks"] = update_fields["remarks"]
        if "marking_method" in update_fields:
            set_doc["marking_method"] = update_fields["marking_method"]

        res = db.attendance_records.find_one_and_update(
            {"_id": ObjectId(record_id)},
            {"$set": set_doc},
            return_document=True,
        )
        if res:
            res["id"] = str(res["_id"])
        return res

    # --- SUMMARIES ---
    @classmethod
    def calculate_student_summary(cls, student_id: str) -> dict:
        """
        Calculates overall attendance summary for a student.
        EXCUSED status is excluded from denominator. LATE counts as attended.
        Derived absence is calculated from closed sessions where student had no record.
        """
        db = cls._get_db()
        student_doc = None
        sid_str = str(student_id)
        try:
            if ObjectId.is_valid(sid_str):
                student_doc = db.students.find_one({"_id": ObjectId(sid_str)}) or db.students.find_one({"user_id": ObjectId(sid_str)})
        except Exception:
            pass
        if not student_doc:
            student_doc = db.students.find_one({"user_id": sid_str}) or db.students.find_one({"student_id": sid_str})

        student_class_id = str(student_doc.get("class_id")) if student_doc and student_doc.get("class_id") else None

        # Closed sessions for student's class (exclude CANCELLED sessions!)
        session_query = {"status": "CLOSED"}
        if student_class_id:
            try:
                session_query["$or"] = [{"class_id": student_class_id}, {"class_id": ObjectId(student_class_id)}]
            except Exception:
                session_query["class_id"] = student_class_id

        closed_sessions = list(db.attendance_sessions.find(session_query))
        total_sessions = len(closed_sessions)
        closed_session_ids = [str(s["_id"]) for s in closed_sessions]

        possible_ids = [sid_str]
        if student_doc:
            possible_ids.extend([str(student_doc["_id"]), str(student_doc.get("student_id", "")), str(student_doc.get("user_id", ""))])
        possible_ids = list(set(filter(None, possible_ids)))

        # Get student's records for these closed sessions
        records = list(
            db.attendance_records.find(
                {
                    "student_id": {"$in": possible_ids},
                    "session_id": {"$in": closed_session_ids},
                }
            )
        ) if closed_session_ids else []

        record_by_session = {r["session_id"]: r["status"] for r in records}

        present_count = 0
        absent_count = 0
        late_count = 0
        excused_count = 0

        for s_id in closed_session_ids:
            st = record_by_session.get(s_id)
            if st == "PRESENT":
                present_count += 1
            elif st == "LATE":
                late_count += 1
            elif st == "EXCUSED":
                excused_count += 1
            elif st == "ABSENT":
                absent_count += 1
            else:
                # Derived absence for closed session with no record
                absent_count += 1

        eligible_sessions = present_count + absent_count + late_count
        if eligible_sessions > 0:
            percentage = round(((present_count + late_count) / eligible_sessions) * 100.0, 2)
        else:
            percentage = 0.0

        return {
            "total_sessions": total_sessions,
            "eligible_sessions": eligible_sessions,
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "excused": excused_count,
            "attendance_percentage": percentage,
        }

    @classmethod
    def calculate_subject_summaries(cls, student_id: str) -> List[dict]:
        """Calculates subject-wise attendance summary for a student."""
        db = cls._get_db()
        student_doc = None
        sid_str = str(student_id)
        try:
            if ObjectId.is_valid(sid_str):
                student_doc = db.students.find_one({"_id": ObjectId(sid_str)}) or db.students.find_one({"user_id": ObjectId(sid_str)})
        except Exception:
            pass
        if not student_doc:
            student_doc = db.students.find_one({"user_id": sid_str}) or db.students.find_one({"student_id": sid_str})

        student_class_id = str(student_doc.get("class_id")) if student_doc and student_doc.get("class_id") else None

        session_query = {"status": "CLOSED"}
        if student_class_id:
            try:
                session_query["$or"] = [{"class_id": student_class_id}, {"class_id": ObjectId(student_class_id)}]
            except Exception:
                session_query["class_id"] = student_class_id

        closed_sessions = list(db.attendance_sessions.find(session_query))

        # Group sessions by subject_id
        sessions_by_subject: Dict[str, List[dict]] = {}
        for s in closed_sessions:
            sub_id = str(s["subject_id"])
            if sub_id not in sessions_by_subject:
                sessions_by_subject[sub_id] = []
            sessions_by_subject[sub_id].append(s)

        possible_ids = [sid_str]
        if student_doc:
            possible_ids.extend([str(student_doc["_id"]), str(student_doc.get("student_id", "")), str(student_doc.get("user_id", ""))])
        possible_ids = list(set(filter(None, possible_ids)))

        results = []
        for sub_id, s_list in sessions_by_subject.items():
            try:
                subject_doc = db.subjects.find_one({"_id": ObjectId(sub_id)})
            except Exception:
                subject_doc = None

            sub_code = subject_doc.get("subject_code", "SUB") if subject_doc else "SUB"
            sub_name = subject_doc.get("subject_name", "Subject") if subject_doc else "Subject"

            s_ids = [str(s["_id"]) for s in s_list]
            records = list(
                db.attendance_records.find(
                    {
                        "student_id": {"$in": possible_ids},
                        "session_id": {"$in": s_ids},
                    }
                )
            )
            record_by_session = {r["session_id"]: r["status"] for r in records}

            present_count = 0
            absent_count = 0
            late_count = 0
            excused_count = 0

            for s_id in s_ids:
                st = record_by_session.get(s_id)
                if st == "PRESENT":
                    present_count += 1
                elif st == "LATE":
                    late_count += 1
                elif st == "EXCUSED":
                    excused_count += 1
                elif st == "ABSENT":
                    absent_count += 1
                else:
                    absent_count += 1

            eligible = present_count + absent_count + late_count
            pct = round(((present_count + late_count) / eligible) * 100.0, 2) if eligible > 0 else 0.0

            results.append(
                {
                    "subject_id": sub_id,
                    "subject_code": sub_code,
                    "subject_name": sub_name,
                    "total_sessions": len(s_list),
                    "eligible_sessions": eligible,
                    "present": present_count,
                    "absent": absent_count,
                    "late": late_count,
                    "excused": excused_count,
                    "attendance_percentage": pct,
                }
            )

        return results
