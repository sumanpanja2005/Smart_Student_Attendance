import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self._status: str = "not_configured"
        self._last_connect_attempt: float = 0.0

    def connect(self) -> str:
        """
        Initializes MongoDB client connection and tests ping.
        Supports standard MongoDB URIs and mongomock:// for local development tests.
        Returns database status: 'connected', 'disconnected', or 'not_configured'.
        """
        import time

        uri = settings.MONGODB_URI
        if not uri or not uri.strip() or "<username>" in uri:
            self._status = "not_configured"
            return self._status

        now = time.time()
        # Rate-limit connection retries to at most once every 5 seconds
        if self._status == "disconnected" and (now - self._last_connect_attempt) < 5.0:
            return self._status

        self._last_connect_attempt = now

        # Support mongomock for local offline testing
        if uri.startswith("mongomock://"):
            try:
                import mongomock
                self.client = mongomock.MongoClient()
                self.client.server_info = lambda: {
                    "version": "4.4.0",
                    "versionArray": [4, 4, 0],
                    "ok": 1.0,
                }
                self.db = self.client[settings.MONGODB_DATABASE]
                self._status = "connected"
                logger.info("Connected to local mongomock database.")
                self.create_indexes()
                return self._status
            except Exception as exc:
                logger.error(f"mongomock initialization error: {exc}")
                self._status = "disconnected"
                return self._status

        try:
            # Set short timeout (3000ms) to ensure startup and health checks remain fast
            self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            # Verify connection with ping
            self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DATABASE]
            self._status = "connected"
            logger.info("Successfully connected to MongoDB Atlas.")

            # Create unique & compound indexes
            self.create_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as exc:
            self.client = None
            self.db = None
            self._status = "disconnected"
            logger.error(f"MongoDB connection failed: {exc}")
        except Exception as exc:
            self.client = None
            self.db = None
            self._status = "disconnected"
            logger.error(f"Unexpected error during MongoDB connection: {exc}")

        return self._status

    def create_indexes(self):
        """Creates unique & compound indexes for all collections."""
        if self.db is None:
            return
        try:
            self.db.users.create_index("email", unique=True)
            self.db.students.create_index("student_id", unique=True)
            self.db.students.create_index("user_id", unique=True)
            self.db.teachers.create_index("employee_id", unique=True)
            self.db.teachers.create_index("user_id", unique=True)
            self.db.subjects.create_index("subject_code", unique=True)

            # Face Embeddings Index
            self.db.face_embeddings.create_index([("student_id", 1), ("is_active", 1)])

            # Attendance Sessions Indexes
            self.db.attendance_sessions.create_index(
                [("class_id", 1), ("subject_id", 1), ("status", 1)]
            )
            self.db.attendance_sessions.create_index(
                [("teacher_id", 1), ("session_date", 1)]
            )

            # Mandatory Unique Compound Index on Attendance Records: (session_id, student_id)
            self.db.attendance_records.create_index(
                [("session_id", 1), ("student_id", 1)], unique=True
            )

            # Additional Attendance Query Indexes
            self.db.attendance_records.create_index(
                [("student_id", 1), ("attendance_date", 1)]
            )
            self.db.attendance_records.create_index(
                [("class_id", 1), ("subject_id", 1)]
            )

            # Step 5 Analytics Indexes
            self.db.student_analytics.create_index("student_id")
            self.db.student_analytics.create_index([("student_id", 1), ("calculated_at", -1)])
            self.db.student_analytics.create_index("risk_level")
            self.db.student_analytics.create_index("calculated_at")

            # Step 6 Notification & Preferences Indexes
            self.db.notifications.create_index("recipient_user_id")
            self.db.notifications.create_index([("recipient_user_id", 1), ("is_read", 1)])
            self.db.notifications.create_index([("recipient_user_id", 1), ("created_at", -1)])
            self.db.notifications.create_index("context_key", unique=True, sparse=True)
            self.db.notification_preferences.create_index("user_id", unique=True)
            self.db.generated_reports.create_index("generated_by")
            self.db.generated_reports.create_index("created_at")

            # Step 7 Audit Logs Indexes
            self.db.audit_logs.create_index("timestamp")
            self.db.audit_logs.create_index("actor_user_id")
            self.db.audit_logs.create_index("actor_role")
            self.db.audit_logs.create_index("action")
            self.db.audit_logs.create_index("resource_type")
            self.db.audit_logs.create_index("resource_id")
            self.db.audit_logs.create_index("event_type")
            self.db.audit_logs.create_index("severity")

            # Compound Indexes for Common Admin Queries
            self.db.audit_logs.create_index([("actor_user_id", 1), ("timestamp", -1)])
            self.db.audit_logs.create_index([("resource_type", 1), ("resource_id", 1), ("timestamp", -1)])
            self.db.audit_logs.create_index([("event_type", 1), ("timestamp", -1)])

            logger.info("MongoDB collection indexes successfully created/verified.")
            self.seed_default_admin()
        except Exception as exc:
            logger.error(f"Failed to create database indexes: {exc}")

    def seed_default_admin(self):
        """Creates default admin account if no admin exists in database."""
        if self.db is None:
            return
        try:
            admin_count = self.db.users.count_documents({"role": "ADMIN"})
            if admin_count == 0:
                from datetime import datetime, timezone
                from app.core.security import hash_password
                now = datetime.now(timezone.utc)
                admin_doc = {
                    "email": "admin@smartattendance.com",
                    "password_hash": hash_password("AdminPass123!"),
                    "role": "ADMIN",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "phone": None,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
                self.db.users.insert_one(admin_doc)
                logger.info("Default Admin account created: admin@smartattendance.com")
        except Exception as exc:
            logger.error(f"Failed to seed default admin: {exc}")

    def close(self):
        """Gracefully close the MongoDB client on shutdown."""
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB client connection closed.")
            except Exception as exc:
                logger.error(f"Error closing MongoDB connection: {exc}")
            finally:
                self.client = None
                self.db = None

    def get_status(self) -> str:
        """
        Returns dynamic database health state ('connected', 'disconnected', 'not_configured').
        """
        uri = settings.MONGODB_URI
        if not uri or not uri.strip() or "<username>" in uri:
            return "not_configured"

        if self.client is None:
            return self.connect()

        if uri.startswith("mongomock://"):
            return "connected"

        try:
            self.client.admin.command("ping")
            self._status = "connected"
        except Exception as exc:
            logger.error(f"MongoDB health ping failed: {exc}")
            self._status = "disconnected"

        return self._status


db_manager = DatabaseManager()
