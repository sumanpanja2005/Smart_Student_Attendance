import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.db.mongo import db_manager

logger = logging.getLogger("uvicorn.error")


class AnalyticsRepository:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    @classmethod
    def save_student_analytics(cls, analytics_data: dict) -> str:
        """Caches calculated student analytics document."""
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        doc = {
            "student_id": str(analytics_data["student_id"]),
            "overall_attendance_percentage": float(analytics_data["overall_attendance_percentage"]),
            "present_count": int(analytics_data["present_count"]),
            "absent_count": int(analytics_data["absent_count"]),
            "late_count": int(analytics_data["late_count"]),
            "excused_count": int(analytics_data["excused_count"]),
            "eligible_session_count": int(analytics_data["eligible_session_count"]),
            "risk_level": analytics_data["risk_level"],
            "risk_score": float(analytics_data["risk_score"]),
            "risk_factors": analytics_data.get("risk_factors", []),
            "subject_summaries": analytics_data.get("subject_summaries", []),
            "calculated_at": now,
        }
        res = db.student_analytics.insert_one(doc)
        return str(res.inserted_id)

    @classmethod
    def get_cached_student_analytics(cls, student_id: str) -> Optional[dict]:
        """Retrieves the latest cached analytics document for a student."""
        db = cls._get_db()
        doc = db.student_analytics.find_one(
            {"student_id": str(student_id)},
            sort=[("calculated_at", -1)],
        )
        if doc:
            doc["id"] = str(doc["_id"])
        return doc
