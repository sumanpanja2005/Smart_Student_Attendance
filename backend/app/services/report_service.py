import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongo import db_manager
from app.services.attendance_repository import AttendanceRepository
from app.services.analytics_service import AnalyticsService
from app.services.pdf_service import PDFService
from app.services.notification_service import NotificationService

logger = logging.getLogger("uvicorn.error")

from app.core.config import settings

STORAGE_DIR = os.path.abspath(settings.REPORTS_DIR)
os.makedirs(STORAGE_DIR, exist_ok=True)


class ReportService:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    @classmethod
    def _save_report_metadata(
        cls,
        report_type: str,
        title: str,
        generated_by: str,
        file_name: str,
        file_path: str,
        student_id: Optional[str] = None,
        class_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        doc = {
            "report_type": report_type,
            "title": title,
            "generated_by": str(generated_by),
            "student_id": str(student_id) if student_id else None,
            "class_id": str(class_id) if class_id else None,
            "subject_id": str(subject_id) if subject_id else None,
            "date_from": date_from,
            "date_to": date_to,
            "file_name": file_name,
            "file_path": file_path,
            "created_at": now,
        }
        res = db.generated_reports.insert_one(doc)
        report_id = str(res.inserted_id)

        # Trigger notification
        NotificationService.trigger_report_ready_notification(
            user_id=generated_by,
            report_type=report_type,
            file_name=file_name,
            report_id=report_id,
        )
        return report_id

    # --- STUDENT ATTENDANCE REPORT ---
    @classmethod
    def generate_student_report(
        cls,
        current_user: dict,
        student_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        subject_id: Optional[str] = None,
    ) -> dict:
        db = cls._get_db()
        try:
            st_doc = db.students.find_one({"_id": ObjectId(student_id)})
        except Exception:
            st_doc = None
        if not st_doc:
            st_doc = db.students.find_one({"user_id": ObjectId(student_id)})
        if not st_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found."
            )

        st_id_str = str(st_doc["_id"])
        user_doc = db.users.find_one({"_id": st_doc.get("user_id")})
        st_name = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip() if user_doc else "Student"

        try:
            class_doc = db.classes.find_one({"_id": ObjectId(st_doc.get("class_id"))})
        except Exception:
            class_doc = None
        class_name = class_doc.get("name", "Class") if class_doc else "Class"

        # Read-only attendance summary & records
        summary = AttendanceRepository.calculate_student_summary(st_id_str)
        filters = {}
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if subject_id:
            filters["subject_id"] = subject_id

        records = AttendanceRepository.list_student_records(st_id_str, filters)

        # Metadata
        metadata = {
            "Student Name": st_name,
            "Student ID": st_doc.get("student_id", ""),
            "Roll Number": st_doc.get("roll_number", ""),
            "Department": st_doc.get("department", ""),
            "Class Section": class_name,
            "Date Generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

        # Stats
        summary_stats = {
            "Attendance %": f"{summary.get('attendance_percentage', 0.0)}%",
            "Present Count": str(summary.get("present", 0)),
            "Late Count": str(summary.get("late", 0)),
            "Absent Count": str(summary.get("absent", 0)),
            "Excused Count": str(summary.get("excused", 0)),
            "Eligible Sessions": str(summary.get("eligible_sessions", 0)),
        }

        # Table
        headers = ["Date", "Subject", "Marked Method", "Status", "Remarks"]
        rows = []
        for r in records:
            sub_name = "Subject"
            if r.get("subject_id"):
                try:
                    s_doc = db.subjects.find_one({"_id": ObjectId(r["subject_id"])})
                    if s_doc:
                        sub_name = f"{s_doc.get('subject_code', '')} - {s_doc.get('subject_name', '')}"
                except Exception:
                    pass

            rows.append(
                [
                    r.get("attendance_date", ""),
                    sub_name,
                    r.get("marking_method", "MANUAL"),
                    r.get("status", "PRESENT"),
                    r.get("remarks") or "-",
                ]
            )

        if not rows:
            rows = [["-", "No attendance records found for criteria", "-", "-", "-"]]

        timestamp_slug = int(datetime.now(timezone.utc).timestamp())
        file_name = f"student_attendance_{st_doc.get('student_id', 'STU')}_{timestamp_slug}.pdf"
        file_path = os.path.join(STORAGE_DIR, file_name)

        PDFService.generate_pdf_report(
            report_title="Student Academic Attendance Report",
            subtitle=f"Official Attendance Transcript for {st_name}",
            metadata=metadata,
            summary_stats=summary_stats,
            table_headers=headers,
            table_rows=rows,
            output_filepath=file_path,
        )

        report_id = cls._save_report_metadata(
            report_type="STUDENT_ATTENDANCE",
            title=f"Attendance Report: {st_name}",
            generated_by=current_user["id"],
            file_name=file_name,
            file_path=file_path,
            student_id=st_id_str,
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "id": report_id,
            "report_type": "STUDENT_ATTENDANCE",
            "title": f"Attendance Report: {st_name}",
            "generated_by": current_user["id"],
            "student_id": st_id_str,
            "file_name": file_name,
            "created_at": datetime.now(timezone.utc),
        }

    # --- CLASS ATTENDANCE REPORT ---
    @classmethod
    def generate_class_report(
        cls,
        current_user: dict,
        class_id: str,
        subject_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
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
        class_name = class_doc.get("name", "Class")

        try:
            enrolled = list(db.students.find({"$or": [{"class_id": class_id_str}, {"class_id": ObjectId(class_id_str)}]}))
        except Exception:
            enrolled = list(db.students.find({"class_id": class_id_str}))

        metadata = {
            "Class Name": class_name,
            "Department": class_doc.get("department", ""),
            "Academic Year": class_doc.get("academic_year", ""),
            "Total Roster Students": str(len(enrolled)),
            "Date Generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

        total_pct_sum = 0.0
        below_thresh = 0

        headers = ["Roll Number", "Student Name", "Present", "Late", "Absent", "Excused", "Attendance %"]
        rows = []

        for st in enrolled:
            st_id_str = str(st["_id"])
            user_doc = db.users.find_one({"_id": st.get("user_id")})
            st_name = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip() if user_doc else "Student"

            st_sum = AttendanceRepository.calculate_student_summary(st_id_str)
            pct = st_sum.get("attendance_percentage", 0.0)
            total_pct_sum += pct
            if pct < 75.0:
                below_thresh += 1

            rows.append(
                [
                    st.get("roll_number", ""),
                    st_name,
                    str(st_sum.get("present", 0)),
                    str(st_sum.get("late", 0)),
                    str(st_sum.get("absent", 0)),
                    str(st_sum.get("excused", 0)),
                    f"{pct}%",
                ]
            )

        avg_pct = round(total_pct_sum / len(enrolled), 1) if enrolled else 0.0

        summary_stats = {
            "Total Enrolled": str(len(enrolled)),
            "Class Average %": f"{avg_pct}%",
            "Below 75% Threshold": str(below_thresh),
        }

        timestamp_slug = int(datetime.now(timezone.utc).timestamp())
        file_name = f"class_attendance_{class_name.replace(' ', '_')}_{timestamp_slug}.pdf"
        file_path = os.path.join(STORAGE_DIR, file_name)

        PDFService.generate_pdf_report(
            report_title="Class Roster Attendance Report",
            subtitle=f"Class Attendance Summary & Student Roster for {class_name}",
            metadata=metadata,
            summary_stats=summary_stats,
            table_headers=headers,
            table_rows=rows,
            output_filepath=file_path,
        )

        report_id = cls._save_report_metadata(
            report_type="CLASS_ATTENDANCE",
            title=f"Class Report: {class_name}",
            generated_by=current_user["id"],
            file_name=file_name,
            file_path=file_path,
            class_id=class_id_str,
            subject_id=subject_id,
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "id": report_id,
            "report_type": "CLASS_ATTENDANCE",
            "title": f"Class Report: {class_name}",
            "generated_by": current_user["id"],
            "class_id": class_id_str,
            "file_name": file_name,
            "created_at": datetime.now(timezone.utc),
        }

    # --- SUBJECT ATTENDANCE REPORT ---
    @classmethod
    def generate_subject_report(
        cls,
        current_user: dict,
        class_id: str,
        subject_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        db = cls._get_db()
        try:
            sub_doc = db.subjects.find_one({"_id": ObjectId(subject_id)})
        except Exception:
            sub_doc = None

        if not sub_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found."
            )

        try:
            class_doc = db.classes.find_one({"_id": ObjectId(class_id)})
        except Exception:
            class_doc = None
        class_name = class_doc.get("name", "Class") if class_doc else "Class"

        sessions = list(db.attendance_sessions.find({"class_id": str(class_id), "subject_id": str(subject_id), "status": "CLOSED"}))
        s_ids = [str(s["_id"]) for s in sessions]

        try:
            enrolled = list(db.students.find({"$or": [{"class_id": str(class_id)}, {"class_id": ObjectId(class_id)}]}))
        except Exception:
            enrolled = list(db.students.find({"class_id": str(class_id)}))

        metadata = {
            "Subject Name": sub_doc.get("subject_name", "Subject"),
            "Subject Code": sub_doc.get("subject_code", "SUB"),
            "Class Section": class_name,
            "Total Closed Sessions": str(len(sessions)),
            "Date Generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

        headers = ["Roll Number", "Student Name", "Present", "Late", "Absent", "Subject Att. %"]
        rows = []
        total_pct_sum = 0.0

        for st in enrolled:
            st_id_str = str(st["_id"])
            user_doc = db.users.find_one({"_id": st.get("user_id")})
            st_name = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip() if user_doc else "Student"

            recs = list(db.attendance_records.find({"student_id": st_id_str, "session_id": {"$in": s_ids}})) if s_ids else []
            rec_map = {r["session_id"]: r["status"] for r in recs}

            p_cnt = 0
            l_cnt = 0
            a_cnt = 0

            for s_id in s_ids:
                val = rec_map.get(s_id, "ABSENT")
                if val == "PRESENT":
                    p_cnt += 1
                elif val == "LATE":
                    l_cnt += 1
                else:
                    a_cnt += 1

            elig = p_cnt + l_cnt + a_cnt
            sub_pct = round(((p_cnt + l_cnt) / elig) * 100.0, 1) if elig > 0 else 0.0
            total_pct_sum += sub_pct

            rows.append(
                [
                    st.get("roll_number", ""),
                    st_name,
                    str(p_cnt),
                    str(l_cnt),
                    str(a_cnt),
                    f"{sub_pct}%",
                ]
            )

        avg_sub_pct = round(total_pct_sum / len(enrolled), 1) if enrolled else 0.0

        summary_stats = {
            "Total Sessions": str(len(sessions)),
            "Enrolled Students": str(len(enrolled)),
            "Subject Average %": f"{avg_sub_pct}%",
        }

        timestamp_slug = int(datetime.now(timezone.utc).timestamp())
        file_name = f"subject_attendance_{sub_doc.get('subject_code', 'SUB')}_{timestamp_slug}.pdf"
        file_path = os.path.join(STORAGE_DIR, file_name)

        PDFService.generate_pdf_report(
            report_title="Subject Attendance Statistics Report",
            subtitle=f"Course Attendance Summary for {sub_doc.get('subject_name', '')} ({class_name})",
            metadata=metadata,
            summary_stats=summary_stats,
            table_headers=headers,
            table_rows=rows,
            output_filepath=file_path,
        )

        report_id = cls._save_report_metadata(
            report_type="SUBJECT_ATTENDANCE",
            title=f"Subject Report: {sub_doc.get('subject_code', '')}",
            generated_by=current_user["id"],
            file_name=file_name,
            file_path=file_path,
            class_id=str(class_id),
            subject_id=str(subject_id),
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "id": report_id,
            "report_type": "SUBJECT_ATTENDANCE",
            "title": f"Subject Report: {sub_doc.get('subject_code', '')}",
            "generated_by": current_user["id"],
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "file_name": file_name,
            "created_at": datetime.now(timezone.utc),
        }

    # --- ANALYTICS / RISK REPORT ---
    @classmethod
    def generate_analytics_report(
        cls,
        current_user: dict,
        student_id: Optional[str] = None,
        class_id: Optional[str] = None,
    ) -> dict:
        db = cls._get_db()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if student_id:
            # Single Student Analytics Report using Step 5 AnalyticsService
            st_data = AnalyticsService.get_student_analytics(student_id)
            metadata = {
                "Student Name": st_data["student_name"],
                "Roll Number": st_data["roll_number"],
                "Class": st_data["class_name"],
                "Date Generated": now_str,
            }
            summary_stats = {
                "Attendance %": f"{st_data['overall_attendance_percentage']}%",
                "Risk Score": f"{st_data['risk_score']} / 100",
                "Risk Level": st_data["risk_level"],
            }
            headers = ["Factor Category", "Details & Explanation"]
            rows = []
            for f in st_data.get("risk_factors", []):
                rows.append(["Contributing Factor", f])

            title = f"Predictive Risk Report: {st_data['student_name']}"
            file_prefix = f"risk_student_{st_data['roll_number']}"
        else:
            # Class / System Analytics Report
            risk_students = AnalyticsService.get_risk_students()
            metadata = {
                "Total Students Audited": str(len(risk_students)),
                "Scope": f"Class {class_id}" if class_id else "System-Wide Global Scope",
                "Date Generated": now_str,
            }
            crit_cnt = sum(1 for s in risk_students if s["risk_level"] == "CRITICAL")
            high_cnt = sum(1 for s in risk_students if s["risk_level"] == "HIGH")

            summary_stats = {
                "Total Audited": str(len(risk_students)),
                "Critical Risk": str(crit_cnt),
                "High Risk": str(high_cnt),
            }
            headers = ["Student Name", "Roll Number", "Class", "Attendance %", "Risk Score", "Risk Level", "Primary Factor"]
            rows = []
            for s in risk_students:
                rows.append(
                    [
                        s["student_name"],
                        s["roll_number"],
                        s["class_name"],
                        f"{s['attendance_percentage']}%",
                        str(s["risk_score"]),
                        s["risk_level"],
                        s["risk_factors"][0] if s.get("risk_factors") else "-",
                    ]
                )

            title = "System At-Risk Students Analytics Report"
            file_prefix = "system_risk_analytics"

        timestamp_slug = int(datetime.now(timezone.utc).timestamp())
        file_name = f"{file_prefix}_{timestamp_slug}.pdf"
        file_path = os.path.join(STORAGE_DIR, file_name)

        PDFService.generate_pdf_report(
            report_title=title,
            subtitle="Deterministic Risk Analysis & Predictive Student Performance Audit",
            metadata=metadata,
            summary_stats=summary_stats,
            table_headers=headers,
            table_rows=rows,
            output_filepath=file_path,
        )

        report_id = cls._save_report_metadata(
            report_type="ANALYTICS_RISK",
            title=title,
            generated_by=current_user["id"],
            file_name=file_name,
            file_path=file_path,
            student_id=student_id,
            class_id=class_id,
        )

        return {
            "id": report_id,
            "report_type": "ANALYTICS_RISK",
            "title": title,
            "generated_by": current_user["id"],
            "file_name": file_name,
            "created_at": datetime.now(timezone.utc),
        }
