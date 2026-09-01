import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.db.mongo import db_manager

logger = logging.getLogger("uvicorn.error")


class NotificationRepository:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    # --- NOTIFICATIONS ---
    @classmethod
    def create_notification(cls, notification_data: dict) -> Tuple[bool, Optional[dict], bool]:
        """
        Creates a notification document.
        Catches DuplicateKeyError on unique context_key gracefully.
        Returns (success: bool, notification_doc: Optional[dict], is_duplicate: bool).
        """
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        doc = {
            "recipient_user_id": str(notification_data["recipient_user_id"]),
            "notification_type": notification_data["notification_type"],
            "title": notification_data["title"],
            "message": notification_data["message"],
            "severity": notification_data.get("severity", "INFO"),
            "is_read": False,
            "context_key": notification_data.get("context_key"),
            "created_at": now,
            "related_student_id": notification_data.get("related_student_id"),
            "related_class_id": notification_data.get("related_class_id"),
            "related_subject_id": notification_data.get("related_subject_id"),
            "related_session_id": notification_data.get("related_session_id"),
        }
        try:
            res = db.notifications.insert_one(doc)
            doc["id"] = str(res.inserted_id)
            return True, doc, False
        except DuplicateKeyError:
            # Context key duplicate caught gracefully
            existing = db.notifications.find_one({"context_key": notification_data.get("context_key")})
            if existing:
                existing["id"] = str(existing["_id"])
            return True, existing, True
        except Exception as exc:
            logger.error(f"Failed to create notification: {exc}")
            return False, None, False

    @classmethod
    def get_notification(cls, notification_id: str) -> Optional[dict]:
        db = cls._get_db()
        try:
            doc = db.notifications.find_one({"_id": ObjectId(notification_id)})
            if doc:
                doc["id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    @classmethod
    def list_notifications(cls, user_id: str, limit: int = 50) -> List[dict]:
        db = cls._get_db()
        cursor = db.notifications.find({"recipient_user_id": str(user_id)}).sort("created_at", -1).limit(limit)
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(doc)
        return results

    @classmethod
    def get_unread_count(cls, user_id: str) -> int:
        db = cls._get_db()
        return db.notifications.count_documents({"recipient_user_id": str(user_id), "is_read": False})

    @classmethod
    def mark_as_read(cls, notification_id: str, user_id: str) -> bool:
        db = cls._get_db()
        try:
            res = db.notifications.update_one(
                {"_id": ObjectId(notification_id), "recipient_user_id": str(user_id)},
                {"$set": {"is_read": True}},
            )
            return res.modified_count > 0
        except Exception:
            return False

    @classmethod
    def mark_all_as_read(cls, user_id: str) -> int:
        db = cls._get_db()
        res = db.notifications.update_many(
            {"recipient_user_id": str(user_id), "is_read": False},
            {"$set": {"is_read": True}},
        )
        return res.modified_count

    @classmethod
    def delete_notification(cls, notification_id: str, user_id: str) -> bool:
        db = cls._get_db()
        try:
            res = db.notifications.delete_one(
                {"_id": ObjectId(notification_id), "recipient_user_id": str(user_id)}
            )
            return res.deleted_count > 0
        except Exception:
            return False

    # --- PREFERENCES ---
    @classmethod
    def get_preferences(cls, user_id: str) -> dict:
        db = cls._get_db()
        pref = db.notification_preferences.find_one({"user_id": str(user_id)})
        if not pref:
            # Default preferences for user
            now = datetime.now(timezone.utc)
            default_pref = {
                "user_id": str(user_id),
                "in_app_enabled": True,
                "email_enabled": True,
                "low_attendance_enabled": True,
                "risk_alert_enabled": True,
                "report_notifications_enabled": True,
                "updated_at": now,
            }
            try:
                db.notification_preferences.insert_one(default_pref)
            except Exception:
                pass
            return default_pref

        pref["id"] = str(pref["_id"])
        return pref

    @classmethod
    def update_preferences(cls, user_id: str, update_fields: dict) -> dict:
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        set_doc = {"updated_at": now}

        for k, v in update_fields.items():
            if v is not None:
                set_doc[k] = v

        res = db.notification_preferences.find_one_and_update(
            {"user_id": str(user_id)},
            {"$set": set_doc},
            upsert=True,
            return_document=True,
        )
        if res:
            res["id"] = str(res["_id"])
        return res
