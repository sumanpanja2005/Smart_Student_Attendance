import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongo import db_manager
from app.services.attendance_repository import AttendanceRepository
from app.services.analytics_repository import AnalyticsRepository

logger = logging.getLogger("uvicorn.error")


class AnalyticsService:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    @classmethod
    def _get_student_doc(cls, student_id: str) -> Optional[dict]:
        db = cls._get_db()
        if not student_id:
            return None
        student_id_str = str(student_id)
        # 1. Try finding by student _id
        try:
            if ObjectId.is_valid(student_id_str):
                doc = db.students.find_one({"_id": ObjectId(student_id_str)})
                if doc:
                    return doc
        except Exception:
            pass
        # 2. Try finding by user_id as ObjectId
        try:
            if ObjectId.is_valid(student_id_str):
                doc = db.students.find_one({"user_id": ObjectId(student_id_str)})
                if doc:
                    return doc
        except Exception:
            pass
        # 3. Try finding by user_id as string
        try:
            doc = db.students.find_one({"user_id": student_id_str})
            if doc:
                return doc
        except Exception:
            pass
        # 4. Try finding by student_id code (e.g. STU-501)
        try:
            doc = db.students.find_one({"student_id": student_id_str})
            if doc:
                return doc
        except Exception:
            pass
        # 5. Fallback: check if student_id is a User ID, finding user doc first
        try:
            if ObjectId.is_valid(student_id_str):
                user = db.users.find_one({"_id": ObjectId(student_id_str)})
                if user:
                    doc = db.students.find_one({"$or": [{"user_id": user["_id"]}, {"user_id": str(user["_id"])}]})
                    if doc:
                        return doc
        except Exception:
            pass
        return None

    # --- DETERMINISTIC EXPLAINABLE RISK ENGINE ---
    @classmethod
    def compute_student_risk(
        cls,
        summary: dict,
        subject_summaries: List[dict],
        recent_records: List[dict],
    ) -> Tuple[float, str, List[str]]:
        """
        Computes deterministic, explainable risk score (0-100), risk level (LOW/MEDIUM/HIGH/CRITICAL),
        and human-readable risk factors.
        Policy:
          0-29: LOW
          30-59: MEDIUM
          60-79: HIGH
          80-100: CRITICAL
        """
        pct = float(summary.get("attendance_percentage", 0.0))
        eligible = int(summary.get("eligible_sessions", 0))
        present = int(summary.get("present", 0))
        absent = int(summary.get("absent", 0))
        late = int(summary.get("late", 0))

        factors = []
        raw_score = 0.0

        if eligible == 0:
            return 0.0, "LOW", ["No completed academic attendance sessions recorded yet."]

        # Base Risk Score calculation from percentage
        if pct < 75.0:
            base_risk = (75.0 - pct) * 2.5 + 30.0
        elif pct < 85.0:
            base_risk = (85.0 - pct) * 2.0 + 10.0
        else:
            base_risk = max(0.0, (100.0 - pct) * 0.4)

        raw_score += base_risk

        # Factor 1: Overall Attendance Percentage
        if pct < 65.0:
            raw_score += 15.0
            factors.append(f"Critical attendance shortage: Overall attendance is {pct:.1f}% (below 65%).")
        elif pct < 75.0:
            raw_score += 10.0
            factors.append(f"Attendance below threshold: Overall attendance is {pct:.1f}% (below 75% required).")

        # Factor 2: Recent Absence Frequency (Last 5 sessions)
        recent_5 = recent_records[:5]
        recent_absences = sum(1 for r in recent_5 if r.get("status") in ("ABSENT", "DERIVED"))
        if recent_absences >= 3:
            raw_score += 15.0
            factors.append(f"High recent absence frequency: {recent_absences} absences recorded in last 5 sessions.")
        elif recent_absences >= 2:
            raw_score += 8.0
            factors.append(f"Increasing absence trend: {recent_absences} absences recorded in last 5 sessions.")

        # Factor 3: Frequent Tardiness
        if late >= 3:
            raw_score += 8.0
            factors.append(f"Frequent tardiness: {late} late arrivals recorded.")

        # Factor 4: Subject-Specific Weakness
        weak_subjects = [s["subject_name"] for s in subject_summaries if s.get("attendance_percentage", 100.0) < 70.0]
        if weak_subjects:
            raw_score += 10.0
            subj_str = ", ".join(weak_subjects)
            factors.append(f"Subject-specific attendance weakness: Attendance is below 70% in {subj_str}.")

        final_score = min(100.0, max(0.0, round(raw_score, 1)))

        if final_score < 30.0:
            level = "LOW"
        elif final_score < 60.0:
            level = "MEDIUM"
        elif final_score < 80.0:
            level = "HIGH"
        else:
            level = "CRITICAL"

        if not factors:
            factors.append("Good academic standing: Attendance meets or exceeds 85% requirement.")

        return final_score, level, factors

    # --- TREND ANALYSIS ---
    @classmethod
    def calculate_student_trend(
        cls, student_id: str, period_type: str = "daily"
    ) -> List[dict]:
        """Calculates chronological attendance trend points (daily/weekly/monthly)."""
        db = cls._get_db()
        student_doc = cls._get_student_doc(student_id)
        if not student_doc:
            return []

        student_class_id = str(student_doc.get("class_id")) if student_doc.get("class_id") else None

        session_query = {"status": "CLOSED"}
        if student_class_id:
            try:
                session_query["$or"] = [{"class_id": student_class_id}, {"class_id": ObjectId(student_class_id)}]
            except Exception:
                session_query["class_id"] = student_class_id

        closed_sessions = list(db.attendance_sessions.find(session_query).sort("session_date", 1))
        if not closed_sessions:
            return []

        closed_ids = [str(s["_id"]) for s in closed_sessions]
        records = list(
            db.attendance_records.find(
                {"student_id": str(student_id), "session_id": {"$in": closed_ids}}
            )
        )
        rec_map = {r["session_id"]: r["status"] for r in records}

        points_map: Dict[str, dict] = {}

        for s in closed_sessions:
            s_id = str(s["_id"])
            dt_str = s.get("session_date", "")
            if not dt_str:
                continue

            if period_type == "weekly":
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d")
                    period_key = f"Week {dt.isocalendar()[1]} ({dt.year})"
                except Exception:
                    period_key = dt_str[:7]
            elif period_type == "monthly":
                period_key = dt_str[:7]  # YYYY-MM
            else:
                period_key = dt_str  # YYYY-MM-DD

            if period_key not in points_map:
                points_map[period_key] = {
                    "period": period_key,
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "excused": 0,
                }

            status_val = rec_map.get(s_id, "ABSENT")
            if status_val == "PRESENT":
                points_map[period_key]["present"] += 1
            elif status_val == "LATE":
                points_map[period_key]["late"] += 1
            elif status_val == "EXCUSED":
                points_map[period_key]["excused"] += 1
            else:
                points_map[period_key]["absent"] += 1

        result_points = []
        for p_key, data in points_map.items():
            pres = data["present"]
            lt = data["late"]
            absn = data["absent"]
            elig = pres + lt + absn
            pct = round(((pres + lt) / elig) * 100.0, 1) if elig > 0 else 0.0

            result_points.append(
                {
                    "period": data["period"],
                    "present": pres,
                    "absent": absn,
                    "late": lt,
                    "excused": data["excused"],
                    "attendance_percentage": pct,
                }
            )

        return result_points

    # --- STUDENT ANALYTICS ---
    @classmethod
    def get_student_analytics(cls, student_id: str) -> dict:
        """Calculates comprehensive analytics and risk profile for a student."""
        db = cls._get_db()
        student_doc = cls._get_student_doc(student_id)
        if not student_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found."
            )

        student_id_str = str(student_doc["_id"])
        user_doc = None
        if student_doc.get("user_id"):
            try:
                user_doc = db.users.find_one({"_id": ObjectId(student_doc["user_id"])})
            except Exception:
                user_doc = db.users.find_one({"_id": str(student_doc["user_id"])})
        
        student_name = ""
        if user_doc:
            student_name = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip()
        if not student_name:
            student_name = student_doc.get("name") or student_doc.get("student_id") or "Student"

        class_doc = None
        if student_doc.get("class_id"):
            try:
                class_doc = db.classes.find_one({"_id": ObjectId(student_doc["class_id"])})
            except Exception:
                class_doc = db.classes.find_one({"_id": str(student_doc["class_id"])})
        
        class_name = (class_doc.get("class_name") or class_doc.get("name")) if class_doc else "Class"

        # Calculate Summary & Subject Summaries from Step 4 repository
        summary = AttendanceRepository.calculate_student_summary(student_id_str)
        subject_summaries = AttendanceRepository.calculate_subject_summaries(student_id_str)
        recent_records = AttendanceRepository.list_student_records(student_id_str)
        trend_points = cls.calculate_student_trend(student_id_str, period_type="daily")

        risk_score, risk_level, risk_factors = cls.compute_student_risk(
            summary, subject_summaries, recent_records
        )

        now = datetime.now(timezone.utc)
        analytics_data = {
            "student_id": student_id_str,
            "student_name": student_name,
            "roll_number": student_doc.get("roll_number", "") or student_doc.get("student_id", ""),
            "class_name": class_name,
            "overall_attendance_percentage": summary.get("attendance_percentage", 0.0),
            "present_count": summary.get("present", 0),
            "absent_count": summary.get("absent", 0),
            "late_count": summary.get("late", 0),
            "excused_count": summary.get("excused", 0),
            "eligible_session_count": summary.get("eligible_sessions", 0),
            "total_session_count": summary.get("total_sessions", 0),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "subject_summaries": subject_summaries,
            "recent_trend": trend_points,
            "calculated_at": now,
        }

        # Cache analytics
        AnalyticsRepository.save_student_analytics(analytics_data)
        return analytics_data

    # --- CLASS ANALYTICS ---
    @classmethod
    def get_class_analytics(cls, class_id: str) -> dict:
        """Calculates class-level analytics and risk distribution."""
        db = cls._get_db()
        try:
            class_doc = db.classes.find_one({"_id": ObjectId(class_id)})
        except Exception:
            class_doc = None

        if not class_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found."
            )

        class_id_str = str(class_doc["_id"])
        try:
            enrolled_students = list(db.students.find({"$or": [{"class_id": class_id_str}, {"class_id": ObjectId(class_id_str)}]}))
        except Exception:
            enrolled_students = list(db.students.find({"class_id": class_id_str}))

        total_students = len(enrolled_students)

        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        total_pct_sum = 0.0
        below_threshold = 0
        total_present = 0
        total_absent = 0
        total_late = 0

        for st in enrolled_students:
            st_id_str = str(st["_id"])
            st_summary = AttendanceRepository.calculate_student_summary(st_id_str)
            pct = st_summary.get("attendance_percentage", 0.0)
            total_pct_sum += pct
            if pct < 75.0:
                below_threshold += 1

            total_present += st_summary.get("present", 0)
            total_absent += st_summary.get("absent", 0)
            total_late += st_summary.get("late", 0)

            sub_sums = AttendanceRepository.calculate_subject_summaries(st_id_str)
            _, level, _ = cls.compute_student_risk(st_summary, sub_sums, [])
            risk_dist[level] = risk_dist.get(level, 0) + 1

        avg_pct = round(total_pct_sum / total_students, 1) if total_students > 0 else 0.0

        # Calculate subject averages for class
        subject_ids = [str(s) for s in class_doc.get("subject_ids", [])]
        subject_averages = []
        for sub_id in subject_ids:
            try:
                sub_doc = db.subjects.find_one({"_id": ObjectId(sub_id)})
            except Exception:
                sub_doc = None
            if not sub_doc:
                continue

            sub_code = sub_doc.get("subject_code", "SUB")
            sub_name = sub_doc.get("subject_name", "Subject")

            # Get sessions for subject in this class
            sessions = list(db.attendance_sessions.find({"class_id": class_id_str, "subject_id": sub_id, "status": "CLOSED"}))
            s_ids = [str(s["_id"]) for s in sessions]

            sub_present = 0
            sub_absent = 0
            sub_late = 0

            for st in enrolled_students:
                recs = list(db.attendance_records.find({"student_id": str(st["_id"]), "session_id": {"$in": s_ids}})) if s_ids else []
                rec_map = {r["session_id"]: r["status"] for r in recs}
                for s_id in s_ids:
                    st_val = rec_map.get(s_id, "ABSENT")
                    if st_val == "PRESENT":
                        sub_present += 1
                    elif st_val == "LATE":
                        sub_late += 1
                    else:
                        sub_absent += 1

            sub_elig = sub_present + sub_late + sub_absent
            sub_avg = round(((sub_present + sub_late) / sub_elig) * 100.0, 1) if sub_elig > 0 else 0.0

            subject_averages.append(
                {
                    "subject_id": sub_id,
                    "subject_code": sub_code,
                    "subject_name": sub_name,
                    "total_sessions": len(sessions),
                    "average_attendance_percentage": sub_avg,
                    "present_count": sub_present,
                    "absent_count": sub_absent,
                    "late_count": sub_late,
                }
            )

        return {
            "class_id": class_id_str,
            "class_name": class_doc.get("name", "Class"),
            "department": class_doc.get("department", ""),
            "total_students": total_students,
            "average_attendance_percentage": avg_pct,
            "students_below_threshold": below_threshold,
            "risk_distribution": risk_dist,
            "subject_averages": subject_averages,
            "present_count": total_present,
            "absent_count": total_absent,
            "late_count": total_late,
        }

    # --- SUBJECT ANALYTICS FOR CLASS ---
    @classmethod
    def get_subject_analytics_for_class(cls, class_id: str, subject_id: str) -> dict:
        """Calculates analytics for a specific subject within a class."""
        db = cls._get_db()
        try:
            sub_doc = db.subjects.find_one({"_id": ObjectId(subject_id)})
        except Exception:
            sub_doc = None

        if not sub_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
            )

        sessions = list(db.attendance_sessions.find({"class_id": str(class_id), "subject_id": str(subject_id), "status": "CLOSED"}))
        s_ids = [str(s["_id"]) for s in sessions]

        try:
            enrolled = list(db.students.find({"$or": [{"class_id": str(class_id)}, {"class_id": ObjectId(class_id)}]}))
        except Exception:
            enrolled = list(db.students.find({"class_id": str(class_id)}))

        total_present = 0
        total_absent = 0
        total_late = 0

        for st in enrolled:
            recs = list(db.attendance_records.find({"student_id": str(st["_id"]), "session_id": {"$in": s_ids}})) if s_ids else []
            rec_map = {r["session_id"]: r["status"] for r in recs}
            for s_id in s_ids:
                st_val = rec_map.get(s_id, "ABSENT")
                if st_val == "PRESENT":
                    total_present += 1
                elif st_val == "LATE":
                    total_late += 1
                else:
                    total_absent += 1

        elig = total_present + total_late + total_absent
        avg_pct = round(((total_present + total_late) / elig) * 100.0, 1) if elig > 0 else 0.0

        return {
            "subject_id": str(subject_id),
            "subject_code": sub_doc.get("subject_code", "SUB"),
            "subject_name": sub_doc.get("subject_name", "Subject"),
            "total_sessions": len(sessions),
            "average_attendance_percentage": avg_pct,
            "present_count": total_present,
            "absent_count": total_absent,
            "late_count": total_late,
        }

    # --- AT-RISK STUDENTS LIST ---
    @classmethod
    def get_risk_students(
        cls, risk_level: Optional[str] = None, allowed_class_ids: Optional[List[str]] = None
    ) -> List[dict]:
        """Returns list of students filtered by risk level (LOW/MEDIUM/HIGH/CRITICAL)."""
        db = cls._get_db()
        query = {}
        if allowed_class_ids is not None:
            # Class filter
            class_objs = []
            for cid in allowed_class_ids:
                class_objs.append(cid)
                try:
                    class_objs.append(ObjectId(cid))
                except Exception:
                    pass
            query["class_id"] = {"$in": class_objs}

        all_students = list(db.students.find(query))
        at_risk_list = []

        for st in all_students:
            st_id_str = str(st["_id"])
            st_analytics = cls.get_student_analytics(st_id_str)

            st_level = st_analytics["risk_level"]
            if risk_level and st_level != risk_level.upper():
                continue

            at_risk_list.append(
                {
                    "student_id": st_id_str,
                    "student_name": st_analytics["student_name"],
                    "roll_number": st_analytics["roll_number"],
                    "class_name": st_analytics["class_name"],
                    "attendance_percentage": st_analytics["overall_attendance_percentage"],
                    "risk_score": st_analytics["risk_score"],
                    "risk_level": st_level,
                    "risk_factors": st_analytics["risk_factors"],
                }
            )

        # Sort by risk score descending
        at_risk_list.sort(key=lambda x: x["risk_score"], reverse=True)
        return at_risk_list

    # --- ROLE-AWARE DASHBOARD ---
    @classmethod
    def get_dashboard_analytics(cls, current_user: dict) -> dict:
        """Calculates role-tailored dashboard analytics metrics."""
        db = cls._get_db()
        role = current_user.get("role")

        if role == "STUDENT":
            st_analytics = cls.get_student_analytics(current_user["id"])
            return {
                "total_students": 1,
                "overall_average_percentage": st_analytics["overall_attendance_percentage"],
                "risk_counts": {st_analytics["risk_level"]: 1},
                "recent_sessions_count": st_analytics["total_session_count"],
                "top_at_risk_students": [],
            }

        if role == "TEACHER":
            teacher_doc = db.teachers.find_one({"user_id": ObjectId(current_user["id"])})
            assigned_class_ids = [str(c) for c in teacher_doc.get("assigned_class_ids", [])] if teacher_doc else []

            # If assigned_class_ids empty, find classes where teacher is class_teacher or in teacher_ids
            if not assigned_class_ids and teacher_doc:
                t_id_str = str(teacher_doc["_id"])
                t_classes = list(db.classes.find({"$or": [{"class_teacher_id": t_id_str}, {"teacher_ids": t_id_str}, {"class_teacher_id": ObjectId(t_id_str)}]}) )
                assigned_class_ids = [str(c["_id"]) for c in t_classes]

            risk_students = cls.get_risk_students(allowed_class_ids=assigned_class_ids)
            total_students = len(risk_students)
            avg_pct = round(sum(s["attendance_percentage"] for s in risk_students) / total_students, 1) if total_students > 0 else 0.0

            risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            for s in risk_students:
                risk_counts[s["risk_level"]] = risk_counts.get(s["risk_level"], 0) + 1

            top_risk = [s for s in risk_students if s["risk_level"] in ("HIGH", "CRITICAL")][:5]
            recent_sessions = db.attendance_sessions.count_documents({"class_id": {"$in": assigned_class_ids}})

            return {
                "total_students": total_students,
                "overall_average_percentage": avg_pct,
                "risk_counts": risk_counts,
                "recent_sessions_count": recent_sessions,
                "top_at_risk_students": top_risk,
            }

        # ADMIN
        all_risk_students = cls.get_risk_students()
        total_students = len(all_risk_students)
        avg_pct = round(sum(s["attendance_percentage"] for s in all_risk_students) / total_students, 1) if total_students > 0 else 0.0

        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for s in all_risk_students:
            risk_counts[s["risk_level"]] = risk_counts.get(s["risk_level"], 0) + 1

        top_risk = [s for s in all_risk_students if s["risk_level"] in ("HIGH", "CRITICAL")][:5]
        recent_sessions = db.attendance_sessions.count_documents({})

        return {
            "total_students": total_students,
            "overall_average_percentage": avg_pct,
            "risk_counts": risk_counts,
            "recent_sessions_count": recent_sessions,
            "top_at_risk_students": top_risk,
        }
