import os
import sys
import io
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["MONGODB_URI"] = "mongomock://localhost"

from app.main import app
from app.db.mongo import db_manager
from app.core.security import hash_password
from app.services.audit_repository import AuditRepository

db_manager.connect()
db = db_manager.db

client = TestClient(app)


def run_step7_integration_tests():
    print("============================================================")
    print(" STEP 7 AUDIT TRAIL & SYSTEM MONITORING TEST SUITE")
    print("============================================================")

    # Clean database collections
    db.users.delete_many({})
    db.students.delete_many({})
    db.teachers.delete_many({})
    db.subjects.delete_many({})
    db.classes.delete_many({})
    db.face_embeddings.delete_many({})
    db.attendance_sessions.delete_many({})
    db.attendance_records.delete_many({})
    db.student_analytics.delete_many({})
    db.notifications.delete_many({})
    db.notification_preferences.delete_many({})
    db.generated_reports.delete_many({})
    db.audit_logs.delete_many({})

    # Ensure indexes
    db_manager.create_indexes()

    now = datetime.now(timezone.utc)

    # Setup Setup Entities via API / DB
    admin_user_id = db.users.insert_one(
        {
            "email": "admin@step7.edu",
            "password_hash": hash_password("AdminPass123!"),
            "role": "ADMIN",
            "first_name": "System",
            "last_name": "Admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    teacher_user_id = db.users.insert_one(
        {
            "email": "teacher@step7.edu",
            "password_hash": hash_password("TeacherPass123!"),
            "role": "TEACHER",
            "first_name": "Sarah",
            "last_name": "Connor",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    student_a_user_id = db.users.insert_one(
        {
            "email": "student_a@step7.edu",
            "password_hash": hash_password("StudentPass123!"),
            "role": "STUDENT",
            "first_name": "Alice",
            "last_name": "Smith",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    subject_id = db.subjects.insert_one(
        {
            "subject_code": "CS701",
            "subject_name": "Distributed Systems",
            "department": "Computer Science",
            "semester": 7,
            "credits": 4,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    teacher_id = db.teachers.insert_one(
        {
            "user_id": teacher_user_id,
            "employee_id": "EMP-701",
            "department": "Computer Science",
            "designation": "Professor",
            "assigned_subject_ids": [subject_id],
            "assigned_class_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    class_id = db.classes.insert_one(
        {
            "class_name": "BS-CS 7A",
            "department": "Computer Science",
            "semester": 7,
            "section": "A",
            "academic_year": "2025-2026",
            "class_teacher_id": teacher_id,
            "teacher_ids": [teacher_id],
            "subject_ids": [subject_id],
            "student_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    student_a_id = db.students.insert_one(
        {
            "user_id": student_a_user_id,
            "student_id": "STU-701",
            "roll_number": "23CS001",
            "department": "Computer Science",
            "semester": 7,
            "section": "A",
            "class_id": class_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    db.classes.update_one({"_id": class_id}, {"$set": {"student_ids": [student_a_id]}})

    # 1. Authentic API Logins & Audit Verification
    res = client.post("/api/auth/login", json={"email": "admin@step7.edu", "password": "AdminPass123!"})
    assert res.status_code == 200
    admin_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    res = client.post("/api/auth/login", json={"email": "teacher@step7.edu", "password": "TeacherPass123!"})
    assert res.status_code == 200
    teacher_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    res = client.post("/api/auth/login", json={"email": "student_a@step7.edu", "password": "StudentPass123!"})
    assert res.status_code == 200
    student_a_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    login_audit = db.audit_logs.find_one({"event_type": "AUTH_LOGIN"})
    assert login_audit is not None
    print("1. Real API Login & AUTH_LOGIN Event Generation: PASS")

    # 2. Failed Login Audit Verification
    res = client.post("/api/auth/login", json={"email": "student_a@step7.edu", "password": "WrongPassword!"})
    assert res.status_code == 401
    failed_log = db.audit_logs.find_one({"event_type": "AUTH_LOGIN_FAILED"})
    assert failed_log is not None
    assert failed_log["status"] == "FAILED"
    print("2. Real API Failed Login & AUTH_LOGIN_FAILED Audit Log: PASS")

    # 3. Role Guard Checks
    res = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/admin/audit-logs", headers=teacher_headers)
    assert res.status_code == 403

    res = client.get("/api/admin/audit-logs", headers=student_a_headers)
    assert res.status_code == 403
    print("3. Server-Side Role Authorization Guards (403 for non-admins): PASS")

    # 4. Academic Operations Real API Audit Triggers
    res = client.post("/api/subjects", json={"subject_code": "CS702", "subject_name": "Parallel Computing", "department": "Computer Science", "semester": 7, "credits": 3}, headers=admin_headers)
    assert res.status_code == 201
    assert db.audit_logs.find_one({"event_type": "SUBJECT_CREATED"}) is not None
    print("4. Real API Subject Creation Audit Event: PASS")

    # 5. Session & Attendance Real API Audit Triggers
    res = client.post("/api/attendance/sessions", json={"class_id": str(class_id), "subject_id": str(subject_id), "session_date": "2026-08-15"}, headers=teacher_headers)
    assert res.status_code == 201
    sess_id = res.json()["id"]
    assert db.audit_logs.find_one({"event_type": "ATTENDANCE_SESSION_CREATED"}) is not None

    res = client.post(f"/api/attendance/sessions/{sess_id}/manual", json={"student_id": str(student_a_id), "status": "PRESENT", "remarks": "On time"}, headers=teacher_headers)
    assert res.status_code == 200
    assert db.audit_logs.find_one({"event_type": "ATTENDANCE_MARKED_MANUAL"}) is not None

    res = client.patch(f"/api/attendance/sessions/{sess_id}/close", headers=teacher_headers)
    assert res.status_code == 200
    assert db.audit_logs.find_one({"event_type": "ATTENDANCE_SESSION_CLOSED"}) is not None
    print("5. Real API Session Creation, Attendance Marking, and Session Close Audit Triggers: PASS")

    # 6. Analytics Real API Audit Trigger
    res = client.get("/api/analytics/student/me", headers=student_a_headers)
    assert res.status_code == 200
    assert db.audit_logs.find_one({"event_type": "ANALYTICS_ACCESSED"}) is not None
    print("6. Real API Analytics Access Audit Event: PASS")

    # 7. Notifications & Report Real API Audit Triggers
    res = client.patch("/api/notifications/preferences", json={"low_attendance_enabled": True}, headers=student_a_headers)
    assert res.status_code == 200
    assert db.audit_logs.find_one({"event_type": "NOTIFICATION_PREFERENCES_UPDATED"}) is not None

    res = client.post("/api/reports/student", json={}, headers=student_a_headers)
    assert res.status_code == 200
    rep_id = res.json()["id"]

    res = client.get(f"/api/reports/{rep_id}", headers=student_a_headers)
    assert res.status_code == 200
    assert db.audit_logs.find_one({"event_type": "REPORT_DOWNLOADED"}) is not None
    print("7. Real API Notification Preferences & Report Generation/Download Audit Triggers: PASS")

    # 8. Security IDOR Event Verification
    # Student B login
    student_b_user_id = db.users.insert_one({"email": "student_b@step7.edu", "password_hash": hash_password("StudentPass123!"), "role": "STUDENT", "first_name": "Bob", "last_name": "Jones", "is_active": True, "created_at": now, "updated_at": now}).inserted_id
    res = client.post("/api/auth/login", json={"email": "student_b@step7.edu", "password": "StudentPass123!"})
    student_b_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Student B attempts downloading Student A's report -> 403 Forbidden & Security IDOR Audit
    res = client.get(f"/api/reports/{rep_id}", headers=student_b_headers)
    assert res.status_code == 403
    idor_event = db.audit_logs.find_one({"event_type": "IDOR_ATTEMPT"})
    assert idor_event is not None
    assert idor_event["severity"] == "CRITICAL"
    print("8. Real API Security IDOR Attempt Event (403 + CRITICAL Security Event): PASS")

    # 9. FAILURE-SAFE AUDITING MANDATORY TEST
    # Monkeypatch AuditRepository.create_audit_log to simulate DB audit failure
    orig_create = AuditRepository.create_audit_log
    AuditRepository.create_audit_log = lambda doc: (False, None)

    try:
        # Execute valid login during audit failure -> MUST STILL SUCCEED (HTTP 200)
        res = client.post("/api/auth/login", json={"email": "admin@step7.edu", "password": "AdminPass123!"})
        assert res.status_code == 200
        assert "access_token" in res.json()

        # Execute analytics access during audit failure -> MUST STILL SUCCEED (HTTP 200)
        res = client.get("/api/analytics/student/me", headers=student_a_headers)
        assert res.status_code == 200
        print("9. FAILURE-SAFE AUDITING TEST (Primary API operations succeed even if audit persistence fails): PASS")
    finally:
        AuditRepository.create_audit_log = orig_create

    # 10. Audit Payload Privacy Verification
    all_logs_docs = list(db.audit_logs.find({}))
    all_logs_str = str(all_logs_docs).lower()
    assert "password_hash" not in all_logs_str
    assert "embedding" not in all_logs_str
    assert "jwt" not in all_logs_str
    print("10. Privacy Guard (Zero passwords, JWTs, or biometric vectors in MongoDB audit_logs): PASS")

    # 11. Immutability Verification (No PUT/PATCH endpoint exists for audit logs)
    res = client.patch("/api/admin/audit-logs", json={"severity": "INFO"}, headers=admin_headers)
    assert res.status_code in (404, 405)
    print("11. Audit Immutability Guard (No endpoint exists to alter audit records): PASS")

    # 12. Retention Cutoff Hardening Test
    old_date = datetime.now(timezone.utc) - timedelta(days=400)
    recent_date = datetime.now(timezone.utc) - timedelta(days=10)

    db.audit_logs.insert_one({"timestamp": old_date, "action": "OLD_RETENTION_TEST", "event_type": "SYSTEM", "severity": "INFO", "message": "Old 400d event"})
    db.audit_logs.insert_one({"timestamp": recent_date, "action": "RECENT_RETENTION_TEST", "event_type": "SYSTEM", "severity": "INFO", "message": "Recent 10d event"})

    res = client.delete("/api/admin/audit-logs/retention?retention_days=365", headers=admin_headers)
    assert res.status_code == 200
    assert db.audit_logs.count_documents({"action": "OLD_RETENTION_TEST"}) == 0
    assert db.audit_logs.count_documents({"action": "RECENT_RETENTION_TEST"}) == 1
    print("12. Audit Retention Hardening (Only records older than 365d deleted; 10d record remains): PASS")

    # 13. System Health & Metrics Endpoints Verification
    res = client.get("/api/admin/system/health", headers=admin_headers)
    assert res.status_code == 200
    h_data = res.json()
    assert h_data["status"] == "ok"
    assert h_data["database"] == "connected"

    res = client.get("/api/admin/system/metrics", headers=admin_headers)
    assert res.status_code == 200
    m_data = res.json()
    assert m_data["total_users"] == 4
    assert m_data["audit_event_count"] >= 5
    print("13. System Health & System Metrics Endpoints: PASS")

    # 14. Immutability & Immutability Audit Guarantee
    recs_before = db.attendance_records.count_documents({})
    sess_before = db.attendance_sessions.count_documents({})
    client.get("/api/admin/audit-summary", headers=admin_headers)
    assert db.attendance_records.count_documents({}) == recs_before
    assert db.attendance_sessions.count_documents({}) == sess_before
    print("14. Immutability Guarantee (Zero attendance database mutations): PASS")

    # 15. Health Check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("15. System Health Check (/api/health): PASS")

    # 16. STRICT BOUNDARY
    collections = db.list_collection_names()
    assert "predictions" not in collections
    assert "sms_logs" not in collections
    print("16. STRICT BOUNDARY: Zero ML/SMS collections: PASS")

    print("\nALL STEP 7 AUDIT, MONITORING & PRIVACY TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_step7_integration_tests()
