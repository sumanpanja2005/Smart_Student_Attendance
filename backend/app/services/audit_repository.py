import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from app.db.mongo import db_manager

logger = logging.getLogger("uvicorn.error")


class AuditRepository:
    @staticmethod
    def _get_db():
        if db_manager.db is None:
            db_manager.connect()
        return db_manager.db

    @classmethod
    def create_audit_log(cls, doc: dict) -> Tuple[bool, Optional[dict]]:
        """
        Inserts an audit log document. Failure-safe (never raises exception).
        """
        db = cls._get_db()
        now = datetime.now(timezone.utc)
        record = {
            "timestamp": doc.get("timestamp") or now,
            "actor_user_id": str(doc["actor_user_id"]) if doc.get("actor_user_id") else None,
            "actor_role": doc.get("actor_role"),
            "action": doc.get("action", "ACTION"),
            "event_type": doc.get("event_type", "SYSTEM"),
            "resource_type": doc.get("resource_type", "SYSTEM"),
            "resource_id": str(doc["resource_id"]) if doc.get("resource_id") else None,
            "severity": doc.get("severity", "INFO"),
            "status": doc.get("status", "SUCCESS"),
            "message": doc.get("message", ""),
            "ip_address": doc.get("ip_address"),
            "user_agent": doc.get("user_agent"),
            "metadata": doc.get("metadata") or {},
        }
        try:
            res = db.audit_logs.insert_one(record)
            record["id"] = str(res.inserted_id)
            return True, record
        except Exception as exc:
            logger.error(f"Failed to write audit log entry: {exc}")
            return False, None

    @classmethod
    def get_audit_log(cls, audit_id: str) -> Optional[dict]:
        db = cls._get_db()
        try:
            doc = db.audit_logs.find_one({"_id": ObjectId(audit_id)})
            if doc:
                doc["id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    @classmethod
    def list_audit_logs(cls, filters: dict, page: int = 1, limit: int = 50) -> Tuple[List[dict], int]:
        db = cls._get_db()
        query = {}

        if filters.get("actor_user_id"):
            query["actor_user_id"] = str(filters["actor_user_id"])
        if filters.get("actor_role"):
            query["actor_role"] = filters["actor_role"]
        if filters.get("event_type"):
            query["event_type"] = filters["event_type"]
        if filters.get("action"):
            query["action"] = filters["action"]
        if filters.get("resource_type"):
            query["resource_type"] = filters["resource_type"]
        if filters.get("resource_id"):
            query["resource_id"] = str(filters["resource_id"])
        if filters.get("severity"):
            query["severity"] = filters["severity"]
        if filters.get("status"):
            query["status"] = filters["status"]

        if filters.get("start_date") or filters.get("end_date"):
            date_query = {}
            if filters.get("start_date"):
                try:
                    date_query["$gte"] = datetime.fromisoformat(filters["start_date"].replace("Z", "+00:00"))
                except Exception:
                    pass
            if filters.get("end_date"):
                try:
                    date_query["$lte"] = datetime.fromisoformat(filters["end_date"].replace("Z", "+00:00"))
                except Exception:
                    pass
            if date_query:
                query["timestamp"] = date_query

        total_count = db.audit_logs.count_documents(query)

        # Enforce maximum page size limit <= 100
        safe_limit = min(100, max(1, limit))
        safe_page = max(1, page)
        skip = (safe_page - 1) * safe_limit

        cursor = db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(safe_limit)
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(doc)

        return results, total_count

    @classmethod
    def get_audit_summary(cls) -> dict:
        db = cls._get_db()
        total_events = db.audit_logs.count_documents({})
        auth_events = db.audit_logs.count_documents({"event_type": {"$regex": "^AUTH_"}})
        att_events = db.audit_logs.count_documents({"event_type": {"$regex": "^ATTENDANCE_"}})
        sec_events = db.audit_logs.count_documents({"severity": {"$in": ["WARNING", "ERROR", "CRITICAL"]}})
        sys_events = db.audit_logs.count_documents({"event_type": {"$in": ["SYSTEM", "ADMIN_ACTION"]}})

        # Aggregate distributions
        ev_types = {}
        for doc in db.audit_logs.aggregate([{"$group": {"_id": "$event_type", "count": {"$sum": 1}}}]):
            if doc.get("_id"):
                ev_types[doc["_id"]] = doc["count"]

        sev_types = {}
        for doc in db.audit_logs.aggregate([{"$group": {"_id": "$severity", "count": {"$sum": 1}}}]):
            if doc.get("_id"):
                sev_types[doc["_id"]] = doc["count"]

        return {
            "total_audit_events": total_events,
            "auth_events_count": auth_events,
            "attendance_events_count": att_events,
            "security_events_count": sec_events,
            "system_events_count": sys_events,
            "event_type_distribution": ev_types,
            "severity_distribution": sev_types,
        }

    @classmethod
    def get_security_events(cls, limit: int = 50) -> List[dict]:
        db = cls._get_db()
        query = {
            "$or": [
                {"severity": {"$in": ["WARNING", "ERROR", "CRITICAL"]}},
                {"event_type": {"$in": ["AUTH_LOGIN_FAILED", "UNAUTHORIZED_ACCESS_ATTEMPT", "IDOR_ATTEMPT"]}},
            ]
        }
        cursor = db.audit_logs.find(query).sort("timestamp", -1).limit(min(100, limit))
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(doc)
        return results

    @classmethod
    def delete_old_audit_logs(cls, retention_days: int = 365) -> int:
        db = cls._get_db()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        res = db.audit_logs.delete_many({"timestamp": {"$lt": cutoff_date}})
        return res.deleted_count
