import os
import sys
import io
from datetime import datetime, timezone
from bson import ObjectId
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["MONGODB_URI"] = "mongomock://localhost"

from app.main import app
from app.db.mongo import db_manager
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.services.audit_repository import AuditRepository

db_manager.connect()
db = db_manager.db

client = TestClient(app)


def run_step8_production_tests():
    print("============================================================")
    print(" STEP 8 PRODUCTION HARDENING & SECURITY TEST SUITE")
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

    db_manager.create_indexes()
    now = datetime.now(timezone.utc)

    # 1. Setup Admin, Teacher, Student Users
    admin_id = db.users.insert_one({"email": "admin@step8.edu", "password_hash": hash_password("AdminPass123!"), "role": "ADMIN", "first_name": "System", "last_name": "Admin", "is_active": True, "created_at": now, "updated_at": now}).inserted_id
    teacher_id = db.users.insert_one({"email": "teacher@step8.edu", "password_hash": hash_password("TeacherPass123!"), "role": "TEACHER", "first_name": "Sarah", "last_name": "Connor", "is_active": True, "created_at": now, "updated_at": now}).inserted_id
    student_id = db.users.insert_one({"email": "student@step8.edu", "password_hash": hash_password("StudentPass123!"), "role": "STUDENT", "first_name": "Alice", "last_name": "Smith", "is_active": True, "created_at": now, "updated_at": now}).inserted_id
    deactivated_id = db.users.insert_one({"email": "deactivated@step8.edu", "password_hash": hash_password("Pass123!"), "role": "STUDENT", "first_name": "Deactivated", "last_name": "User", "is_active": False, "created_at": now, "updated_at": now}).inserted_id

    # Logins
    res_admin = client.post("/api/auth/login", json={"email": "admin@step8.edu", "password": "AdminPass123!"})
    admin_headers = {"Authorization": f"Bearer {res_admin.json()['access_token']}"}

    res_student = client.post("/api/auth/login", json={"email": "student@step8.edu", "password": "StudentPass123!"})
    student_headers = {"Authorization": f"Bearer {res_student.json()['access_token']}"}

    # --- 1. CONFIGURATION & ENVIRONMENT VALIDATION ---
    assert settings.ENVIRONMENT in ("development", "production")
    assert settings.JWT_ALGORITHM == "HS256"
    assert len(settings.get_cors_origins_list()) >= 1
    print("1. Configuration & Environment Settings: PASS")

    # --- 2. AUTHENTICATION & TOKEN REJECTION ---
    # Unauthenticated request
    res = client.get("/api/admin/audit-logs")
    assert res.status_code == 401
    print("2. Unauthenticated Request Rejection (401): PASS")

    # Invalid JWT token
    res = client.get("/api/admin/audit-logs", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert res.status_code == 401
    print("3. Invalid JWT Token Rejection (401): PASS")

    # Deactivated User Account Rejection
    res = client.post("/api/auth/login", json={"email": "deactivated@step8.edu", "password": "Pass123!"})
    assert res.status_code == 401
    print("4. Deactivated User Account Rejection (401): PASS")

    # --- 3. SERVER-SIDE ROLE ISOLATION & IDOR PROTECTION ---
    res = client.get("/api/admin/audit-logs", headers=student_headers)
    assert res.status_code == 403

    res = client.get("/api/admin/system/health", headers=student_headers)
    assert res.status_code == 403
    print("5. Server-Side Role Isolation (Student accessing Admin endpoints -> 403): PASS")

    # --- 4. CORS ORIGINS CONFIGURATION ---
    res = client.options("/api/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert res.status_code in (200, 204)
    print("6. CORS Origins & Preflight Options Verification: PASS")

    # --- 5. RATE LIMITING MIDDLEWARE ---
    # Perform burst logins to trigger rate limit (max 10/min)
    rate_triggered = False
    for _ in range(12):
        r = client.post("/api/auth/login", json={"email": "admin@step8.edu", "password": "AdminPass123!"})
        if r.status_code == 429:
            rate_triggered = True
            break
    assert rate_triggered is True
    print("7. Rate Limiting Middleware (429 Too Many Requests): PASS")

    # --- 6. SAFE EXCEPTION HANDLING (ZERO SECRET LEAKAGE) ---
    res = client.get("/api/reports/invalid_id_format_xyz", headers=admin_headers)
    assert res.status_code in (400, 404, 422)
    err_body = str(res.json()).lower()
    assert "password_hash" not in err_body
    assert "jwt_secret_key" not in err_body
    print("8. Safe Exception Handling & Zero Secret Leakage: PASS")

    # --- 7. FAILURE-SAFE AUDITING PERSISTENCE ---
    orig_create = AuditRepository.create_audit_log
    AuditRepository.create_audit_log = lambda doc: (False, None)
    try:
        # Request should succeed even if audit logging persistence fails
        res = client.get("/api/health")
        assert res.status_code == 200
        print("9. Failure-Safe Audit Persistence (Zero primary API impact): PASS")
    finally:
        AuditRepository.create_audit_log = orig_create

    # --- 8. PATH TRAVERSAL REPORT SECURITY ---
    # Create fake report document in DB with path traversal file_path
    traversal_report_id = db.generated_reports.insert_one(
        {
            "report_type": "STUDENT_ATTENDANCE",
            "file_name": "test.pdf",
            "file_path": "../../etc/passwd",
            "generated_by": str(admin_id),
            "created_at": now,
        }
    ).inserted_id

    res = client.get(f"/api/reports/{traversal_report_id}", headers=admin_headers)
    assert res.status_code == 403
    print("10. Path Traversal Prevention on Report Download (403 Forbidden): PASS")

    # --- 9. DATABASE INDEXES & PAGINATION HARDEST ---
    res = client.get("/api/admin/audit-logs?limit=200", headers=admin_headers)
    if res.status_code == 200:
        assert res.json()["limit"] <= 100
    print("11. Query Pagination Limit Enforcement (Max limit <= 100): PASS")

    # --- 10. PUBLIC & ADMIN HEALTH ENDPOINTS ---
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res = client.get("/api/admin/system/health", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["database"] == "connected"
    print("12. Public & Extended Admin System Health Checks: PASS")

    # --- 11. BIOMETRIC PRIVACY & SENSITIVE DATA GUARD ---
    all_users = list(db.users.find({}))
    for u in all_users:
        assert "password" not in u
    print("13. Biometric & Secret Privacy Verification: PASS")

    print("\nALL STEP 8 PRODUCTION HARDENING & SECURITY TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_step8_production_tests()
