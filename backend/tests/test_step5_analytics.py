import os
import sys
import unittest
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
from app.core.security import hash_password
from app.services.analytics_service import AnalyticsService

db_manager.connect()
db = db_manager.db

client = TestClient(app)


def run_step5_integration_tests():
    print("============================================================")
    print(" STEP 5 ANALYTICS & PREDICTIVE RISK INTEGRATION TEST SUITE")
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

    # Ensure indexes
    db_manager.create_indexes()

    now = datetime.now(timezone.utc)

    # 1. Setup Admin User
    admin_user_id = db.users.insert_one(
        {
            "email": "admin@step5.edu",
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
            "email": "teacher1@step5.edu",
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
            "email": "teacher2@step5.edu",
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
            "subject_code": "CS501",
            "subject_name": "Database Systems",
            "department": "Information Technology",
            "semester": 5,
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
            "employee_id": "EMP-501",
            "department": "Information Technology",
            "designation": "Assistant Professor",
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
            "employee_id": "EMP-502",
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
            "name": "BS-IT 5A",
            "department": "Information Technology",
            "semester": 5,
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

    # Setup Class B (Assigned to Teacher 2)
    class_b_id = db.classes.insert_one(
        {
            "name": "BS-IT 5B",
            "department": "Information Technology",
            "semester": 5,
            "section": "B",
            "academic_year": "2025-2026",
            "class_teacher_id": teacher2_id,
            "teacher_ids": [teacher2_id],
            "subject_ids": [subject_id],
            "student_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    db.teachers.update_one(
        {"_id": teacher2_id}, {"$set": {"assigned_class_ids": [class_b_id]}}
    )

    # 7. Setup Student A (Enrolled in Class A - Good Attendance)
    student_a_user_id = db.users.insert_one(
        {
            "email": "student_a@step5.edu",
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
            "student_id": "STU-501",
            "roll_number": "21IT001",
            "department": "Information Technology",
            "semester": 5,
            "section": "A",
            "class_id": class_a_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 8. Setup Student B (Enrolled in Class A - High Risk / Frequent Absences)
    student_b_user_id = db.users.insert_one(
        {
            "email": "student_b@step5.edu",
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
            "student_id": "STU-502",
            "roll_number": "21IT002",
            "department": "Information Technology",
            "semester": 5,
            "section": "A",
            "class_id": class_a_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 9. Setup Student C (Enrolled in Class B)
    student_c_user_id = db.users.insert_one(
        {
            "email": "student_c@step5.edu",
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
            "student_id": "STU-503",
            "roll_number": "21IT003",
            "department": "Information Technology",
            "semester": 5,
            "section": "B",
            "class_id": class_b_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 10. Populate Attendance Sessions & Records
    sess1_id = db.attendance_sessions.insert_one(
        {
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "teacher_id": str(teacher1_id),
            "session_date": "2026-08-01",
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
            "attendance_date": "2026-08-01",
            "status": "PRESENT",
            "marked_by": str(teacher1_id),
            "marking_method": "FACE",
            "similarity": 0.92,
            "marked_at": now,
        }
    )

    db.attendance_records.insert_one(
        {
            "session_id": str(sess1_id),
            "student_id": str(student_b_id),
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "attendance_date": "2026-08-01",
            "status": "ABSENT",
            "marked_by": str(teacher1_id),
            "marking_method": "MANUAL",
            "marked_at": now,
        }
    )

    sess2_id = db.attendance_sessions.insert_one(
        {
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "teacher_id": str(teacher1_id),
            "session_date": "2026-08-02",
            "start_time": "09:00:00",
            "status": "CLOSED",
            "created_by": str(teacher1_user_id),
            "created_at": now,
        }
    ).inserted_id

    db.attendance_records.insert_one(
        {
            "session_id": str(sess2_id),
            "student_id": str(student_a_id),
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "attendance_date": "2026-08-02",
            "status": "LATE",
            "marked_by": str(teacher1_id),
            "marking_method": "MANUAL",
            "marked_at": now,
        }
    )

    db.attendance_records.insert_one(
        {
            "session_id": str(sess2_id),
            "student_id": str(student_b_id),
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "attendance_date": "2026-08-02",
            "status": "ABSENT",
            "marked_by": str(teacher1_id),
            "marking_method": "MANUAL",
            "marked_at": now,
        }
    )

    sess3_id = db.attendance_sessions.insert_one(
        {
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "teacher_id": str(teacher1_id),
            "session_date": "2026-08-03",
            "start_time": "09:00:00",
            "status": "CLOSED",
            "created_by": str(teacher1_user_id),
            "created_at": now,
        }
    ).inserted_id

    db.attendance_records.insert_one(
        {
            "session_id": str(sess3_id),
            "student_id": str(student_a_id),
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "attendance_date": "2026-08-03",
            "status": "EXCUSED",
            "marked_by": str(teacher1_id),
            "marking_method": "MANUAL",
            "marked_at": now,
        }
    )

    sess4_id = db.attendance_sessions.insert_one(
        {
            "class_id": str(class_a_id),
            "subject_id": str(subject_id),
            "teacher_id": str(teacher1_id),
            "session_date": "2026-08-04",
            "start_time": "09:00:00",
            "status": "CANCELLED",
            "created_by": str(teacher1_user_id),
            "created_at": now,
        }
    ).inserted_id

    # 11. Perform Logins & Get JWT Tokens
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@step5.edu", "password": "AdminPass123!"},
    )
    assert res.status_code == 200
    admin_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("1. Admin Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "teacher1@step5.edu", "password": "TeacherPass123!"},
    )
    assert res.status_code == 200
    teacher1_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("2. Teacher 1 (Assigned) Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "teacher2@step5.edu", "password": "TeacherPass123!"},
    )
    assert res.status_code == 200
    teacher2_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("3. Teacher 2 (Unassigned) Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "student_a@step5.edu", "password": "StudentPass123!"},
    )
    assert res.status_code == 200
    student_a_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("4. Student A Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "student_b@step5.edu", "password": "StudentPass123!"},
    )
    assert res.status_code == 200
    student_b_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("5. Student B Login: PASS")

    # 12. Student Self Analytics (/api/analytics/student/me)
    res = client.get("/api/analytics/student/me", headers=student_a_headers)
    assert res.status_code == 200, f"Get my analytics failed: {res.text}"
    st_a_analytics = res.json()
    assert st_a_analytics["overall_attendance_percentage"] == 100.0
    assert st_a_analytics["present_count"] == 1
    assert st_a_analytics["late_count"] == 1
    assert st_a_analytics["excused_count"] == 1
    assert st_a_analytics["eligible_session_count"] == 2
    assert st_a_analytics["risk_level"] == "LOW"
    print("6. Student Self Analytics (/api/analytics/student/me): PASS")

    # 13. Student Self Trend Analysis (/api/analytics/student/me/trend)
    res = client.get("/api/analytics/student/me/trend?period_type=daily", headers=student_a_headers)
    assert res.status_code == 200
    trend_res = res.json()
    assert trend_res["period_type"] == "daily"
    assert len(trend_res["points"]) >= 1
    print("7. Student Self Trend Analysis: PASS")

    # 14. Student Self Subject Analytics (/api/analytics/student/me/subjects)
    res = client.get("/api/analytics/student/me/subjects", headers=student_a_headers)
    assert res.status_code == 200
    sub_analytics = res.json()
    assert len(sub_analytics) >= 1
    assert sub_analytics[0]["subject_code"] == "CS501"
    print("8. Student Self Subject Analytics: PASS")

    # 15. Student Privacy & Access Restriction Check
    res = client.get(f"/api/analytics/students/{str(student_b_id)}", headers=student_a_headers)
    assert res.status_code == 403
    print("9. Student Accessing Another Student Analytics -> 403 Forbidden: PASS")

    # 16. Teacher Access & Authorization Checks
    res = client.get(f"/api/analytics/students/{str(student_a_id)}", headers=teacher1_headers)
    assert res.status_code == 200
    assert res.json()["student_id"] == str(student_a_id)
    print("10. Teacher 1 Accesses Assigned Student Analytics: PASS")

    res = client.get(f"/api/analytics/students/{str(student_a_id)}", headers=teacher2_headers)
    assert res.status_code == 403
    print("11. Unassigned Teacher Accessing Student Analytics -> 403 Forbidden: PASS")

    res = client.get(f"/api/analytics/classes/{str(class_a_id)}", headers=teacher1_headers)
    assert res.status_code == 200
    cls_a_data = res.json()
    assert cls_a_data["total_students"] == 2
    print("12. Teacher 1 Accesses Assigned Class A Analytics: PASS")

    res = client.get(f"/api/analytics/classes/{str(class_a_id)}", headers=teacher2_headers)
    assert res.status_code == 403
    print("13. Unassigned Teacher Accessing Class A Analytics -> 403 Forbidden: PASS")

    res = client.get(f"/api/analytics/classes/{str(class_a_id)}/subjects/{str(subject_id)}", headers=teacher1_headers)
    assert res.status_code == 200
    assert res.json()["subject_code"] == "CS501"
    print("14. Teacher 1 Accesses Subject Analytics: PASS")

    # 17. Admin System-Wide Access Check
    res = client.get(f"/api/analytics/students/{str(student_a_id)}", headers=admin_headers)
    assert res.status_code == 200
    res = client.get(f"/api/analytics/classes/{str(class_a_id)}", headers=admin_headers)
    assert res.status_code == 200
    res = client.get(f"/api/analytics/classes/{str(class_b_id)}", headers=admin_headers)
    assert res.status_code == 200
    print("15. Admin System-Wide Analytics Access: PASS")

    # 18. Student B High-Risk & Derived Absence Verification
    res = client.get(f"/api/analytics/students/{str(student_b_id)}", headers=admin_headers)
    assert res.status_code == 200
    st_b_analytics = res.json()
    assert st_b_analytics["overall_attendance_percentage"] == 0.0
    assert st_b_analytics["absent_count"] == 3
    assert st_b_analytics["risk_level"] in ("HIGH", "CRITICAL")
    assert len(st_b_analytics["risk_factors"]) >= 1
    print("16. Student B High-Risk & Derived Absence Verification (0.0% / CRITICAL): PASS")

    # 19. At-Risk Students List Endpoint (/api/analytics/risk-students)
    res = client.get("/api/analytics/risk-students?risk_level=CRITICAL", headers=admin_headers)
    assert res.status_code == 200
    risk_list = res.json()
    assert len(risk_list) >= 1
    assert risk_list[0]["student_id"] == str(student_b_id)
    assert risk_list[0]["risk_level"] == "CRITICAL"
    print("17. At-Risk Students Filter (risk_level=CRITICAL): PASS")

    # 20. Teacher At-Risk List Restriction Check
    res = client.get("/api/analytics/risk-students", headers=teacher1_headers)
    assert res.status_code == 200
    t1_risk_list = res.json()
    st_ids = [s["student_id"] for s in t1_risk_list]
    assert str(student_c_id) not in st_ids
    print("18. Teacher Risk-Student List Restricted to Assigned Class: PASS")

    # 21. Role-Aware Dashboard Analytics (/api/analytics/dashboard)
    res = client.get("/api/analytics/dashboard", headers=admin_headers)
    assert res.status_code == 200
    dash_admin = res.json()
    assert dash_admin["total_students"] == 3
    assert len(dash_admin["top_at_risk_students"]) >= 1
    print("19. Admin Dashboard Analytics: PASS")

    res = client.get("/api/analytics/dashboard", headers=teacher1_headers)
    assert res.status_code == 200
    dash_t1 = res.json()
    assert dash_t1["total_students"] == 2
    print("20. Teacher Dashboard Analytics: PASS")

    res = client.get("/api/analytics/dashboard", headers=student_a_headers)
    assert res.status_code == 200
    dash_st = res.json()
    assert dash_st["overall_average_percentage"] == 100.0
    print("21. Student Dashboard Analytics: PASS")

    # 22. Privacy Check: Payload does not expose sensitive fields
    payload_str = str(st_a_analytics)
    assert "password" not in payload_str
    assert "jwt" not in payload_str
    assert "embedding" not in payload_str
    print("22. Privacy Guard (Zero password/JWT/biometric exposure): PASS")

    # 23. EDGE CASE VERIFICATIONS (Explicitly required by Section 13 audit prompt)
    # Edge Case 1: Student C has NO attendance records at all -> eligible_sessions = 0, percentage = 0.0, LOW risk
    st_c_analytics = AnalyticsService.get_student_analytics(str(student_c_id))
    assert st_c_analytics["eligible_session_count"] == 0
    assert st_c_analytics["overall_attendance_percentage"] == 0.0
    assert st_c_analytics["risk_level"] == "LOW"
    assert "No completed academic attendance sessions" in st_c_analytics["risk_factors"][0]
    print("23. Edge Case: Student with zero attendance sessions (0.0% / LOW): PASS")

    # Edge Case 2: Only EXCUSED student test
    score, level, factors = AnalyticsService.compute_student_risk(
        {"attendance_percentage": 0.0, "eligible_sessions": 0, "present": 0, "absent": 0, "late": 0, "excused": 3},
        [], []
    )
    assert score == 0.0
    assert level == "LOW"
    print("24. Edge Case: Student with only EXCUSED sessions (0.0 score / LOW): PASS")

    # Edge Case 3: Invalid Student / Class / Subject IDs return 404
    res = client.get("/api/analytics/students/507f1f77bcf86cd799439011", headers=admin_headers)
    assert res.status_code == 404
    res = client.get("/api/analytics/classes/507f1f77bcf86cd799439011", headers=admin_headers)
    assert res.status_code == 404
    print("25. Edge Case: Invalid Student/Class IDs return 404 Not Found: PASS")

    # 24. Health API Check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["database"] == "connected"
    print("26. Health Check (/api/health): PASS")

    # 25. STRICT BOUNDARY: Zero ML/SMS/Telegram code
    collections = db.list_collection_names()
    assert "predictions" not in collections
    assert "sms_logs" not in collections
    print("27. STRICT BOUNDARY: Zero ML/SMS collections: PASS")

    print("\nALL STEP 5 INTEGRATION, SECURITY & EDGE CASE TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_step5_integration_tests()
