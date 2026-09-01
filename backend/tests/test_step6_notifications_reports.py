import os
import sys
import io
from datetime import datetime, timezone
from bson import ObjectId
from fastapi.testclient import TestClient
import pypdf

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["MONGODB_URI"] = "mongomock://localhost"

from app.main import app
from app.db.mongo import db_manager
from app.core.config import settings
from app.core.security import hash_password
from app.services.notification_service import NotificationService, EmailService
from app.services.report_service import ReportService
from app.services.notification_repository import NotificationRepository

db_manager.connect()
db = db_manager.db

client = TestClient(app)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Helper utility using pypdf to extract raw text content from PDF bytes."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def run_step6_integration_tests():
    print("============================================================")
    print(" STEP 6 NOTIFICATION, REPORTING & HARDENING TEST SUITE")
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

    # Ensure indexes
    db_manager.create_indexes()

    now = datetime.now(timezone.utc)

    # 1. Setup Admin User
    admin_user_id = db.users.insert_one(
        {
            "email": "admin@step6.edu",
            "password_hash": hash_password("AdminPass123!"),
            "role": "ADMIN",
            "first_name": "System",
            "last_name": "Admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 2. Setup Teacher 1 (Assigned) User & Profile
    teacher1_user_id = db.users.insert_one(
        {
            "email": "teacher1@step6.edu",
            "password_hash": hash_password("TeacherPass123!"),
            "role": "TEACHER",
            "first_name": "Sarah",
            "last_name": "Connor",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 3. Setup Teacher 2 (Unassigned) User & Profile
    teacher2_user_id = db.users.insert_one(
        {
            "email": "teacher2@step6.edu",
            "password_hash": hash_password("TeacherPass123!"),
            "role": "TEACHER",
            "first_name": "John",
            "last_name": "Smith",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 4. Setup Subject
    subject_id = db.subjects.insert_one(
        {
            "subject_code": "CS601",
            "subject_name": "Cloud Architecture",
            "department": "Computer Science",
            "semester": 6,
            "credits": 4,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 5. Setup Teacher Profiles
    teacher1_id = db.teachers.insert_one(
        {
            "user_id": teacher1_user_id,
            "employee_id": "EMP-601",
            "department": "Computer Science",
            "designation": "Associate Professor",
            "assigned_subject_ids": [subject_id],
            "assigned_class_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    teacher2_id = db.teachers.insert_one(
        {
            "user_id": teacher2_user_id,
            "employee_id": "EMP-602",
            "department": "Computer Science",
            "designation": "Lecturer",
            "assigned_subject_ids": [],
            "assigned_class_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 6. Setup Class A (Assigned to Teacher 1)
    class_a_id = db.classes.insert_one(
        {
            "name": "BS-CS 6A",
            "department": "Computer Science",
            "semester": 6,
            "section": "A",
            "academic_year": "2025-2026",
            "class_teacher_id": teacher1_id,
            "teacher_ids": [teacher1_id],
            "subject_ids": [subject_id],
            "student_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    db.teachers.update_one(
        {"_id": teacher1_id}, {"$set": {"assigned_class_ids": [class_a_id]}}
    )

    # 7. Setup Student A (Enrolled in Class A)
    student_a_user_id = db.users.insert_one(
        {
            "email": "student_a@step6.edu",
            "password_hash": hash_password("StudentPass123!"),
            "role": "STUDENT",
            "first_name": "Alice",
            "last_name": "Smith",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    student_a_id = db.students.insert_one(
        {
            "user_id": student_a_user_id,
            "student_id": "STU-601",
            "roll_number": "22CS001",
            "department": "Computer Science",
            "semester": 6,
            "section": "A",
            "class_id": class_a_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 8. Setup Student B (Enrolled in Class A - Absent Record)
    student_b_user_id = db.users.insert_one(
        {
            "email": "student_b@step6.edu",
            "password_hash": hash_password("StudentPass123!"),
            "role": "STUDENT",
            "first_name": "Bob",
            "last_name": "Jones",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    student_b_id = db.students.insert_one(
        {
            "user_id": student_b_user_id,
            "student_id": "STU-602",
            "roll_number": "22CS002",
            "department": "Computer Science",
            "semester": 6,
            "section": "A",
            "class_id": class_a_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 9. Setup Student C (Unrelated Class Student)
    student_c_user_id = db.users.insert_one(
        {
            "email": "student_c@step6.edu",
            "password_hash": hash_password("StudentPass123!"),
            "role": "STUDENT",
            "first_name": "Charlie",
            "last_name": "Brown",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    student_c_id = db.students.insert_one(
        {
            "user_id": student_c_user_id,
            "student_id": "STU-603",
            "roll_number": "22CS003",
            "department": "Computer Science",
            "semester": 6,
            "section": "B",
            "class_id": ObjectId(),
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 10. Attendance Setup
    sess1_id = db.attendance_sessions.insert_one(
        {
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "teacher_id": str(teacher1_id),
            "session_date": "2026-08-10",
            "start_time": "09:00:00",
            "status": "CLOSED",
            "created_by": str(teacher1_user_id),
            "created_at": now,
        }
    ).inserted_id

    db.attendance_records.insert_one(
        {
            "session_id": str(sess1_id),
            "student_id": str(student_a_id),
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "attendance_date": "2026-08-10",
            "status": "PRESENT",
            "marked_by": str(teacher1_id),
            "marking_method": "FACE",
            "marked_at": now,
        }
    )

    db.attendance_records.insert_one(
        {
            "session_id": str(sess1_id),
            "student_id": str(student_b_id),
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "attendance_date": "2026-08-10",
            "status": "ABSENT",
            "marked_by": str(teacher1_id),
            "marking_method": "MANUAL",
            "marked_at": now,
        }
    )

    # --- 1. AUTHENTICATION & ROLES ---
    res = client.post("/api/auth/login", json={"email": "admin@step6.edu", "password": "AdminPass123!"})
    assert res.status_code == 200
    admin_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("1. Admin Login: PASS")

    res = client.post("/api/auth/login", json={"email": "teacher1@step6.edu", "password": "TeacherPass123!"})
    assert res.status_code == 200
    teacher1_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("2. Teacher 1 Login: PASS")

    res = client.post("/api/auth/login", json={"email": "teacher2@step6.edu", "password": "TeacherPass123!"})
    assert res.status_code == 200
    teacher2_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("3. Teacher 2 Login: PASS")

    res = client.post("/api/auth/login", json={"email": "student_a@step6.edu", "password": "StudentPass123!"})
    assert res.status_code == 200
    student_a_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("4. Student A Login: PASS")

    res = client.post("/api/auth/login", json={"email": "student_b@step6.edu", "password": "StudentPass123!"})
    assert res.status_code == 200
    student_b_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("5. Student B Login: PASS")

    # --- 2. NOTIFICATION ISOLATION & PRIVACY ---
    succ, doc, _ = NotificationService.send_notification(
        recipient_user_id=str(student_a_user_id),
        notification_type="SYSTEM",
        title="Student A Confidential Notice",
        message="System onboarding test message for Student A.",
        severity="INFO",
        context_key=f"{student_a_user_id}:SYSTEM:init",
    )
    assert succ is True
    notif_id_a = doc["id"]

    # Student A can retrieve own notification
    res = client.get("/api/notifications", headers=student_a_headers)
    assert res.status_code == 200
    a_notifs = res.json()["notifications"]
    assert any(n["id"] == notif_id_a for n in a_notifs)
    print("6. Student A Accesses Own Notifications: PASS")

    # Student B cannot see Student A's notification
    res = client.get("/api/notifications", headers=student_b_headers)
    assert res.status_code == 200
    b_notifs = res.json()["notifications"]
    assert not any(n["id"] == notif_id_a for n in b_notifs)
    print("7. Privacy Isolation (Student B cannot see Student A's notification): PASS")

    # Teacher 2 cannot see Teacher 1's notifications
    succ_t, doc_t, _ = NotificationService.send_notification(
        recipient_user_id=str(teacher1_user_id),
        notification_type="SYSTEM",
        title="Teacher 1 Alert",
        message="Faculty meeting alert.",
    )
    res = client.get("/api/notifications", headers=teacher2_headers)
    assert res.status_code == 200
    t2_ids = [n["id"] for n in res.json()["notifications"]]
    assert doc_t["id"] not in t2_ids
    print("8. Teacher Isolation (Teacher 2 cannot see Teacher 1's notifications): PASS")

    # --- 3. NOTIFICATION CRUD ---
    # List notifications
    res = client.get("/api/notifications", headers=student_a_headers)
    assert res.status_code == 200
    assert res.json()["unread_count"] >= 1

    # Unread count
    res = client.get("/api/notifications/unread-count", headers=student_a_headers)
    assert res.status_code == 200
    assert res.json()["unread_count"] >= 1

    # Mark one read
    res = client.patch(f"/api/notifications/{notif_id_a}/read", headers=student_a_headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Mark all read
    res = client.patch("/api/notifications/read-all", headers=student_a_headers)
    assert res.status_code == 200

    # Delete notification
    res = client.delete(f"/api/notifications/{notif_id_a}", headers=student_a_headers)
    assert res.status_code == 200
    # Deleted notification cannot be retrieved
    res = client.get("/api/notifications", headers=student_a_headers)
    assert not any(n["id"] == notif_id_a for n in res.json()["notifications"])
    print("9. Notification CRUD Operations (List, Read, Mark-All, Delete): PASS")

    # --- 4. PREFERENCES & ENFORCEMENT SUPPRESSION ---
    # Get preferences
    res = client.get("/api/notifications/preferences", headers=student_a_headers)
    assert res.status_code == 200
    assert res.json()["low_attendance_enabled"] is True

    # Disable low attendance alert preference for Student A
    res = client.patch(
        "/api/notifications/preferences",
        json={"low_attendance_enabled": False},
        headers=student_a_headers,
    )
    assert res.status_code == 200
    assert res.json()["low_attendance_enabled"] is False

    # Trigger low attendance alert while disabled -> verify NO notification created
    NotificationService.trigger_low_attendance_alert(str(student_a_id), 60.0)
    res = client.get("/api/notifications", headers=student_a_headers)
    assert not any(n["notification_type"] == "ATTENDANCE_LOW" for n in res.json()["notifications"])
    print("10. Preference Enforcement Suppression (Disabled Low-Attendance Alert Suppressed): PASS")

    # Re-enable low attendance alert preference
    client.patch("/api/notifications/preferences", json={"low_attendance_enabled": True}, headers=student_a_headers)

    # Disable risk alerts for Student A
    client.patch("/api/notifications/preferences", json={"risk_alert_enabled": False}, headers=student_a_headers)
    NotificationService.trigger_high_risk_alert(str(student_a_id), 80.0, "CRITICAL", ["Attendance 50%"])
    res = client.get("/api/notifications", headers=student_a_headers)
    assert not any(n["notification_type"] in ("RISK_HIGH", "RISK_CRITICAL") for n in res.json()["notifications"])
    print("11. Preference Enforcement Suppression (Disabled Risk Alert Suppressed): PASS")

    # Re-enable risk alerts for Student A
    client.patch("/api/notifications/preferences", json={"risk_alert_enabled": True}, headers=student_a_headers)

    # --- 5. AUTOMATIC ALERT TRIGGERS ---
    # Low Attendance Alert Trigger
    NotificationService.trigger_low_attendance_alert(str(student_b_id), 65.0)
    # High Risk Alert Trigger
    NotificationService.trigger_high_risk_alert(str(student_b_id), 68.0, "HIGH", ["Overall attendance 65%"])
    # Critical Risk Alert Trigger
    NotificationService.trigger_critical_risk_alert(str(student_b_id), 85.0, "CRITICAL", ["Critical attendance shortage"])

    res = client.get("/api/notifications", headers=student_b_headers)
    assert res.status_code == 200
    b_types = [n["notification_type"] for n in res.json()["notifications"]]
    assert "ATTENDANCE_LOW" in b_types
    assert "RISK_HIGH" in b_types or "RISK_CRITICAL" in b_types
    print("12. Automatic Alert Triggers (ATTENDANCE_LOW, RISK_HIGH, RISK_CRITICAL): PASS")

    # Session Closed Trigger (only enrolled class students receive)
    sess_c_id = db.attendance_sessions.insert_one(
        {
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "teacher_id": str(teacher1_id),
            "session_date": "2026-08-11",
            "start_time": "10:00:00",
            "status": "CLOSED",
            "created_by": str(teacher1_user_id),
            "created_at": now,
        }
    ).inserted_id

    NotificationService.trigger_session_closed_notifications(str(sess_c_id))

    # Enrolled Student A receives session notification
    res_a = client.get("/api/notifications", headers=student_a_headers)
    a_types = [n["notification_type"] for n in res_a.json()["notifications"]]
    assert "ATTENDANCE_SESSION" in a_types

    # Unrelated Student C does NOT receive session notification
    res_c = client.get("/api/notifications", headers={"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': 'student_c@step6.edu', 'password': 'StudentPass123!'}).json()['access_token']}"})
    c_types = [n["notification_type"] for n in res_c.json()["notifications"]]
    assert "ATTENDANCE_SESSION" not in c_types
    print("13. Session Closed Trigger (Roster-Restricted Delivery to Enrolled Students Only): PASS")

    # --- 6. IDEMPOTENCY & DUPLICATE PREVENTION ---
    succ1, doc1, is_dup1 = NotificationService.send_notification(
        recipient_user_id=str(student_a_user_id),
        notification_type="SYSTEM",
        title="Idempotency Test",
        message="Message 1",
        context_key="key_idempotent_999",
    )
    assert is_dup1 is False

    succ2, doc2, is_dup2 = NotificationService.send_notification(
        recipient_user_id=str(student_a_user_id),
        notification_type="SYSTEM",
        title="Idempotency Test",
        message="Message 1",
        context_key="key_idempotent_999",
    )
    assert is_dup2 is True
    assert db.notifications.count_documents({"context_key": "key_idempotent_999"}) == 1
    print("14. Idempotent Duplicate Notification Prevention (context_key uniqueness): PASS")

    # --- 7. EMAIL SERVICE GRACEFUL FAILURE ---
    email_res = EmailService.send_email(
        recipient_email="unconfigured@step6.edu",
        subject="Test",
        body="Test body",
    )
    assert email_res is True
    print("15. Email Service Graceful Failure Abstraction (Zero runtime exceptions): PASS")

    # --- 8. PDF REPORT GENERATION & SECURITY ---
    # Student generates own report
    res = client.post("/api/reports/student", json={}, headers=student_a_headers)
    assert res.status_code == 200
    st_report_meta = res.json()
    st_report_id = st_report_meta["id"]

    # Teacher 1 generates class and subject report
    res = client.post("/api/reports/class", json={"class_id": str(class_a_id)}, headers=teacher1_headers)
    assert res.status_code == 200
    cls_report_id = res.json()["id"]

    res = client.post("/api/reports/subject", json={"class_id": str(class_a_id), "subject_id": str(subject_id)}, headers=teacher1_headers)
    assert res.status_code == 200

    # Teacher 2 (Unassigned) attempts generating class report -> 403 Forbidden
    res = client.post("/api/reports/class", json={"class_id": str(class_a_id)}, headers=teacher2_headers)
    assert res.status_code == 403

    # Admin generates analytics report
    res = client.post("/api/reports/analytics", json={}, headers=admin_headers)
    assert res.status_code == 200
    admin_report_id = res.json()["id"]
    print("16. PDF Report Generation & Role Authorization: PASS")

    # Secure Download Endpoint
    res = client.get(f"/api/reports/{st_report_id}", headers=student_a_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    st_pdf_bytes = res.content

    # Unauthorized download attempt (Student A attempting to download Admin report) -> 403 Forbidden
    res = client.get(f"/api/reports/{admin_report_id}", headers=student_a_headers)
    assert res.status_code == 403

    # Invalid report ID -> 404 Not Found
    res = client.get("/api/reports/507f1f77bcf86cd799439011", headers=student_a_headers)
    assert res.status_code == 404
    print("17. Secure PDF Download & IDOR Protection: PASS")

    # --- 9. PDF CONTENT VERIFICATION USING PYPDF ---
    pdf_text = extract_pdf_text(st_pdf_bytes)
    assert "Student Academic Attendance Report" in pdf_text
    assert "Alice Smith" in pdf_text
    assert "22CS001" in pdf_text
    assert "Computer Science" in pdf_text
    assert "50.0%" in pdf_text
    print("18. PDF Content Text Inspection via pypdf (Title, Name, Roll No, Percentage verified): PASS")

    # PDF Content Inspection for Analytics Risk Report
    res = client.get(f"/api/reports/{admin_report_id}", headers=admin_headers)
    assert res.status_code == 200
    analytics_pdf_text = extract_pdf_text(res.content)
    assert "Risk" in analytics_pdf_text or "Analytics" in analytics_pdf_text
    print("19. PDF Content Text Inspection for Analytics/Risk Report: PASS")

    # Empty Dataset Report Generation (Student C has zero attendance sessions)
    res = client.post("/api/reports/student", json={}, headers={"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': 'student_c@step6.edu', 'password': 'StudentPass123!'}).json()['access_token']}"})
    assert res.status_code == 200
    c_rep_id = res.json()["id"]
    res = client.get(f"/api/reports/{c_rep_id}", headers={"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': 'student_c@step6.edu', 'password': 'StudentPass123!'}).json()['access_token']}"})
    assert res.status_code == 200
    assert len(res.content) > 500
    print("20. Empty Dataset PDF Generation (Clean PDF stream without server errors): PASS")

    # --- 10. PRIVACY GUARD & READ-ONLY IMMUTABILITY ---
    pdf_string = pdf_text.lower()
    assert "password" not in pdf_string
    assert "jwt" not in pdf_string
    assert "embedding" not in pdf_string
    print("21. Privacy Guard (Zero password/JWT/biometric exposure in PDFs): PASS")

    # Read-Only Guarantee: Compare attendance database state before vs after report operations
    recs_count_before = db.attendance_records.count_documents({})
    sess_count_before = db.attendance_sessions.count_documents({})

    ReportService.generate_student_report(current_user={"id": str(admin_user_id), "role": "ADMIN"}, student_id=str(student_a_id))
    ReportService.generate_class_report(current_user={"id": str(admin_user_id), "role": "ADMIN"}, class_id=str(class_a_id))
    ReportService.generate_subject_report(current_user={"id": str(admin_user_id), "role": "ADMIN"}, class_id=str(class_a_id), subject_id=str(subject_id))

    assert db.attendance_records.count_documents({}) == recs_count_before
    assert db.attendance_sessions.count_documents({}) == sess_count_before
    print("22. Read-Only Immutability Guarantee (Zero attendance database mutations): PASS")

    # --- 11. HEALTH CHECK ---
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["database"] == "connected"
    print("23. Health Check (/api/health): PASS")

    # --- 12. STRICT BOUNDARY ---
    collections = db.list_collection_names()
    assert "predictions" not in collections
    assert "sms_logs" not in collections
    print("24. STRICT BOUNDARY: Zero ML/SMS collections: PASS")

    print("\nALL STEP 6 INTEGRATION, SECURITY, PRIVACY & PDF HARDENING TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_step6_integration_tests()
