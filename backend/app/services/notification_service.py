import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from app.db.mongo import db_manager
from app.services.notification_repository import NotificationRepository

logger = logging.getLogger("uvicorn.error")


class EmailService:
    """
    Clean email abstraction service.
    When SMTP is unconfigured or disabled, logs cleanly without throwing exceptions or breaking callers.
    """

    @classmethod
    def send_email(
        cls, recipient_email: str, subject: str, body: str, html_body: Optional[str] = None
    ) -> bool:
        try:
            logger.info(
                f"[EmailService Stub] Dispatched email to '{recipient_email}' | Subject: '{subject}'"
            )
            return True
        except Exception as exc:
            logger.error(f"[EmailService] Failed to send email: {exc}")
            return False


class NotificationService:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    @classmethod
    def send_notification(
        cls,
        recipient_user_id: str,
        notification_type: str,
        title: str,
        message: str,
        severity: str = "INFO",
        context_key: Optional[str] = None,
        related_student_id: Optional[str] = None,
        related_class_id: Optional[str] = None,
        related_subject_id: Optional[str] = None,
        related_session_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[dict], bool]:
        """
        Failure-safe notification creation handler.
        Verifies user notification preferences before creation.
        Returns (success: bool, doc: Optional[dict], is_duplicate: bool).
        """
        try:
            prefs = NotificationRepository.get_preferences(recipient_user_id)

            # Category preference checks
            if not prefs.get("in_app_enabled", True):
                return False, None, False

            if notification_type == "ATTENDANCE_LOW" and not prefs.get("low_attendance_enabled", True):
                return False, None, False

            if notification_type in ("RISK_HIGH", "RISK_CRITICAL") and not prefs.get("risk_alert_enabled", True):
                return False, None, False

            if notification_type == "REPORT_READY" and not prefs.get("report_notifications_enabled", True):
                return False, None, False

            # In-App Notification Creation
            notification_data = {
                "recipient_user_id": str(recipient_user_id),
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "severity": severity,
                "context_key": context_key,
                "related_student_id": related_student_id,
                "related_class_id": related_class_id,
                "related_subject_id": related_subject_id,
                "related_session_id": related_session_id,
            }
            success, doc, is_dup = NotificationRepository.create_notification(notification_data)

            # Optional Email Abstraction Dispatch
            if prefs.get("email_enabled", True) and not is_dup:
                db = cls._get_db()
                try:
                    user_doc = db.users.find_one({"_id": ObjectId(recipient_user_id)})
                    if user_doc and user_doc.get("email"):
                        EmailService.send_email(
                            recipient_email=user_doc["email"],
                            subject=f"[Smart Attendance Alert] {title}",
                            body=message,
                        )
                except Exception as exc:
                    logger.warning(f"Failed to fetch user email for notification dispatch: {exc}")

            return success, doc, is_dup
        except Exception as exc:
            logger.error(f"NotificationService error: {exc}")
            return False, None, False

    # --- AUTOMATIC ALERT TRIGGERS ---
    @classmethod
    def trigger_low_attendance_alert(cls, student_id: str, attendance_percentage: float) -> bool:
        """Triggered when student overall attendance percentage drops below 75%."""
        if attendance_percentage >= 75.0:
            return False

        db = cls._get_db()
        try:
            st_doc = db.students.find_one({"_id": ObjectId(student_id)})
        except Exception:
            st_doc = None

        if not st_doc:
            return False

        user_id_str = str(st_doc["user_id"])
        ym_key = datetime.now(timezone.utc).strftime("%Y-%m")
        context_key = f"{user_id_str}:ATTENDANCE_LOW:{ym_key}"

        title = "Low Attendance Warning"
        message = f"Your overall attendance has dropped to {attendance_percentage:.1f}%, which is below the required 75.0% threshold."

        cls.send_notification(
            recipient_user_id=user_id_str,
            notification_type="ATTENDANCE_LOW",
            title=title,
            message=message,
            severity="WARNING",
            context_key=context_key,
            related_student_id=str(student_id),
        )
        return True

    @classmethod
    def trigger_critical_risk_alert(
        cls, student_id: str, risk_score: float, risk_level: str, risk_factors: List[str]
    ) -> bool:
        """Triggered when student risk level becomes CRITICAL."""
        return cls.trigger_high_risk_alert(student_id, risk_score, risk_level, risk_factors)

    @classmethod
    def trigger_high_risk_alert(
        cls, student_id: str, risk_score: float, risk_level: str, risk_factors: List[str]
    ) -> bool:
        """Triggered when student risk level becomes HIGH or CRITICAL."""
        if risk_level not in ("HIGH", "CRITICAL"):
            return False

        db = cls._get_db()
        try:
            st_doc = db.students.find_one({"_id": ObjectId(student_id)})
        except Exception:
            st_doc = None

        if not st_doc:
            return False

        user_id_str = str(st_doc["user_id"])
        ym_key = datetime.now(timezone.utc).strftime("%Y-%m")
        context_key = f"{user_id_str}:RISK_{risk_level}:{ym_key}"

        severity = "CRITICAL" if risk_level == "CRITICAL" else "HIGH"
        title = f"{risk_level} Attendance Risk Alert"
        factor_str = risk_factors[0] if risk_factors else "Attendance score requires immediate review."
        message = f"Your academic attendance risk profile has reached {risk_level} level (Score: {risk_score}/100). {factor_str}"

        cls.send_notification(
            recipient_user_id=user_id_str,
            notification_type=f"RISK_{risk_level}",
            title=title,
            message=message,
            severity=severity,
            context_key=context_key,
            related_student_id=str(student_id),
        )

        # Notify Class Teacher if available
        try:
            class_doc = db.classes.find_one({"_id": ObjectId(st_doc.get("class_id"))})
            if class_doc:
                t_profile = db.teachers.find_one({"_id": ObjectId(class_doc.get("class_teacher_id"))})
                if t_profile:
                    t_user_id_str = str(t_profile["user_id"])
                    user_doc = db.users.find_one({"_id": st_doc["user_id"]})
                    st_name = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip() if user_doc else "Student"
                    t_context_key = f"{t_user_id_str}:TEACHER_RISK_{risk_level}:{student_id}:{ym_key}"

                    cls.send_notification(
                        recipient_user_id=t_user_id_str,
                        notification_type=f"RISK_{risk_level}",
                        title=f"Class Student Risk Alert: {st_name}",
                        message=f"Student {st_name} ({st_doc.get('roll_number', '')}) has reached {risk_level} risk level ({risk_score}/100).",
                        severity=severity,
                        context_key=t_context_key,
                        related_student_id=str(student_id),
                        related_class_id=str(st_doc.get("class_id")),
                    )
        except Exception as exc:
            logger.warning(f"Failed to send teacher risk alert: {exc}")

        return True

    @classmethod
    def trigger_session_closed_notifications(cls, session_id: str) -> bool:
        """Triggered when an attendance session is closed by teacher."""
        db = cls._get_db()
        try:
            session_doc = db.attendance_sessions.find_one({"_id": ObjectId(session_id)})
            if not session_doc:
                return False

            class_id = str(session_doc["class_id"])
            try:
                enrolled_students = list(db.students.find({"$or": [{"class_id": class_id}, {"class_id": ObjectId(class_id)}]}))
            except Exception:
                enrolled_students = list(db.students.find({"class_id": class_id}))

            for st in enrolled_students:
                u_id_str = str(st["user_id"])
                context_key = f"{u_id_str}:ATTENDANCE_SESSION:{session_id}"
                cls.send_notification(
                    recipient_user_id=u_id_str,
                    notification_type="ATTENDANCE_SESSION",
                    title="Attendance Session Finalized",
                    message=f"Attendance records for session on {session_doc.get('session_date', '')} have been finalized.",
                    severity="INFO",
                    context_key=context_key,
                    related_session_id=str(session_id),
                    related_class_id=class_id,
                )
            return True
        except Exception as exc:
            logger.error(f"Failed to trigger session closed notifications: {exc}")
            return False

    @classmethod
    def trigger_report_ready_notification(
        cls, user_id: str, report_type: str, file_name: str, report_id: str
    ) -> bool:
        """Triggered when PDF report generation completes."""
        context_key = f"{user_id}:REPORT_READY:{report_id}"
        cls.send_notification(
            recipient_user_id=str(user_id),
            notification_type="REPORT_READY",
            title="PDF Attendance Report Generated",
            message=f"Your {report_type.replace('_', ' ').title()} PDF report ({file_name}) is ready for download.",
            severity="INFO",
            context_key=context_key,
        )
        return True
