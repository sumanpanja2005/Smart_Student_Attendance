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

db_manager.connect()
db = db_manager.db

client = TestClient(app)


def run_step4_integration_tests():
    print("============================================================")
    print(" STEP 4 INTEGRATION & ACCESSIBILITY TEST SUITE")
    print("============================================================")

    # Clean collections
    db.users.delete_many({})
    db.students.delete_many({})
    db.teachers.delete_many({})
    db.subjects.delete_many({})
    db.classes.delete_many({})
    db.face_embeddings.delete_many({})
    db.attendance_sessions.delete_many({})
    db.attendance_records.delete_many({})

    # Ensure indexes
    db_manager.create_indexes()

    now = datetime.now(timezone.utc)

    # 1. Setup Admin User
    admin_user_id = db.users.insert_one(
        {
            "email": "admin@step4.edu",
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
            "email": "teacher1@step4.edu",
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
            "email": "teacher2@step4.edu",
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

    # Subject 2 for multi-subject test
    subject2_id = db.subjects.insert_one(
        {
            "subject_code": "CS502",
            "subject_name": "Web Technology",
            "department": "Information Technology",
            "semester": 5,
            "credits": 3,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 5. Setup Teacher Profiles
    teacher1_id = db.teachers.insert_one(
        {
            "user_id": teacher1_user_id,
            "employee_id": "EMP-101",
            "department": "Information Technology",
            "designation": "Assistant Professor",
            "assigned_subject_ids": [subject_id, subject2_id],
            "assigned_class_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    teacher2_id = db.teachers.insert_one(
        {
            "user_id": teacher2_user_id,
            "employee_id": "EMP-102",
            "department": "Computer Science",
            "designation": "Lecturer",
            "assigned_subject_ids": [],
            "assigned_class_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 6. Setup Class/Section 1 (Class A)
    class_id = db.classes.insert_one(
        {
            "name": "BS-IT 5A",
            "department": "Information Technology",
            "semester": 5,
            "section": "A",
            "academic_year": "2025-2026",
            "class_teacher_id": teacher1_id,
            "teacher_ids": [teacher1_id],
            "subject_ids": [subject_id, subject2_id],
            "student_ids": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # Update Teacher 1 assigned classes
    db.teachers.update_one(
        {"_id": teacher1_id}, {"$set": {"assigned_class_ids": [class_id]}}
    )

    # Class 2 (Class B) for non-enrolled tests
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

    # 7. Setup Student A (Enrolled in Class A)
    student_a_user_id = db.users.insert_one(
        {
            "email": "student_a@step4.edu",
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
            "student_id": "STU-A101",
            "roll_number": "21IT001",
            "department": "Information Technology",
            "semester": 5,
            "section": "A",
            "class_id": class_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 8. Setup Student B (Enrolled in Class A)
    student_b_user_id = db.users.insert_one(
        {
            "email": "student_b@step4.edu",
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
            "student_id": "STU-B102",
            "roll_number": "21IT002",
            "department": "Information Technology",
            "semester": 5,
            "section": "A",
            "class_id": class_id,
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 9. Setup Student C (Enrolled in Class B)
    student_c_user_id = db.users.insert_one(
        {
            "email": "student_c@step4.edu",
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
            "student_id": "STU-C103",
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

    # Update class student_ids
    db.classes.update_one(
        {"_id": class_id}, {"$set": {"student_ids": [student_a_id, student_b_id]}}
    )
    db.classes.update_one(
        {"_id": class_b_id}, {"$set": {"student_ids": [student_c_id]}}
    )

    # 10. Perform Logins & Get JWT Tokens
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@step4.edu", "password": "AdminPass123!"},
    )
    assert res.status_code == 200
    admin_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("1. Admin Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "teacher1@step4.edu", "password": "TeacherPass123!"},
    )
    assert res.status_code == 200
    teacher1_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("2. Teacher 1 (Assigned) Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "teacher2@step4.edu", "password": "TeacherPass123!"},
    )
    assert res.status_code == 200
    teacher2_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("3. Teacher 2 (Unassigned) Login: PASS")

    res = client.post(
        "/api/auth/login",
        json={"email": "student_a@step4.edu", "password": "StudentPass123!"},
    )
    assert res.status_code == 200
    student_a_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    print("4. Student A Login: PASS")

    # 11. Register Face Profile for Student A using Step 3 Face API
    fixtures_dir = os.path.join(backend_dir, "tests", "fixtures")
    img_a1_path = os.path.join(fixtures_dir, "person_a_1.jpg")
    img_b1_path = os.path.join(fixtures_dir, "person_b_1.jpg")

    with open(img_a1_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=admin_headers,
            data={"student_id": str(student_a_id)},
            files={"file": ("person_a_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200, f"Register Student A face failed: {res.text}"
    print("5. Register Student A Face Profile (Step 3 Integration): PASS")

    # Register Face Profile for Student C (Class B)
    old_thresh = settings.FACE_MATCH_THRESHOLD
    settings.FACE_MATCH_THRESHOLD = 0.95

    with open(img_b1_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=admin_headers,
            data={"student_id": str(student_c_id)},
            files={"file": ("person_b_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200, f"Register Student C face failed: {res.text}"
    settings.FACE_MATCH_THRESHOLD = old_thresh
    print("6. Register Student C Face Profile: PASS")

    # 12. Attendance Session Creation Authorization Tests
    # Assigned Teacher creates session for Class A -> PASS
    res = client.post(
        "/api/attendance/sessions",
        headers=teacher1_headers,
        json={"class_id": str(class_id), "subject_id": str(subject_id)},
    )
    assert res.status_code == 201, f"Session creation failed: {res.text}"
    session1 = res.json()
    session1_id = session1["id"]
    assert session1["status"] == "OPEN"
    print("7. Authorized Teacher Session Creation (OPEN): PASS")

    # Unassigned Teacher (Teacher 2) attempts creating session for Class A -> 403 Forbidden
    res = client.post(
        "/api/attendance/sessions",
        headers=teacher2_headers,
        json={"class_id": str(class_id), "subject_id": str(subject_id)},
    )
    assert res.status_code == 403
    print("8. Unassigned Teacher Session Creation -> 403 Forbidden: PASS")

    # Student A attempts creating session -> 403 Forbidden
    res = client.post(
        "/api/attendance/sessions",
        headers=student_a_headers,
        json={"class_id": str(class_id), "subject_id": str(subject_id)},
    )
    assert res.status_code == 403
    print("9. Student Session Creation -> 403 Forbidden: PASS")

    # 13. Face Recognition Attendance Marking (Enrolled Student A)
    with open(img_a1_path, "rb") as f:
        res = client.post(
            f"/api/attendance/sessions/{session1_id}/mark-face",
            headers=teacher1_headers,
            files={"file": ("frame.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    face_res = res.json()
    assert face_res["success"] == True
    assert face_res["recognized"] == True
    assert face_res["attendance_marked"] == True
    assert face_res["student_id"] == str(student_a_id)
    assert face_res["status"] == "PRESENT"
    assert face_res["similarity"] >= 0.50
    print("10. Face Recognition Attendance Marking (PRESENT/FACE): PASS")

    # 14. Idempotent Duplicate Face Attendance Attempt
    with open(img_a1_path, "rb") as f:
        res = client.post(
            f"/api/attendance/sessions/{session1_id}/mark-face",
            headers=teacher1_headers,
            files={"file": ("frame.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    dup_res = res.json()
    assert dup_res["success"] == True
    assert dup_res["recognized"] == True
    assert dup_res["attendance_marked"] == False
    assert dup_res["already_marked"] == True
    print("11. Duplicate Face Attendance Attempt -> Idempotent already_marked: PASS")

    # 15. Cross-Class Face Attendance Rejection (Student C in Class B attempting attendance for Class A session)
    with open(img_b1_path, "rb") as f:
        res = client.post(
            f"/api/attendance/sessions/{session1_id}/mark-face",
            headers=teacher1_headers,
            files={"file": ("frame.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    cross_res = res.json()
    assert cross_res["success"] == False
    assert cross_res["recognized"] == True
    assert cross_res["attendance_marked"] == False
    assert "not enrolled in this class" in cross_res["message"]
    print("12. Cross-Class Face Attendance Rejection (Not Enrolled): PASS")

    # 16. Unknown Face Attendance Rejection
    import cv2
    import numpy as np

    img_unk = np.ones((640, 640, 3), dtype=np.uint8) * 30
    cv2.ellipse(img_unk, (320, 280), (130, 170), 0, 0, 360, (50, 80, 100), -1)
    _, unk_bytes = cv2.imencode(".jpg", img_unk)

    res = client.post(
        f"/api/attendance/sessions/{session1_id}/mark-face",
        headers=teacher1_headers,
        files={"file": ("unknown.jpg", unk_bytes.tobytes(), "image/jpeg")},
    )
    assert res.status_code == 200
    unk_res = res.json()
    assert unk_res["success"] == False
    assert unk_res["recognized"] == False
    assert unk_res["attendance_marked"] == False
    print("13. Unknown Face Attendance Rejection: PASS")

    # 17. Single Manual Attendance Marking (Student B -> LATE)
    res = client.post(
        f"/api/attendance/sessions/{session1_id}/manual",
        headers=teacher1_headers,
        json={"student_id": str(student_b_id), "status": "LATE", "remarks": "Traffic delay"},
    )
    assert res.status_code == 200
    assert res.json()["success"] == True
    print("14. Single Manual Attendance Marking (LATE/MANUAL): PASS")

    # 18. Bulk Manual Attendance Marking (Protection against overwriting existing FACE/MANUAL records)
    res = client.post(
        f"/api/attendance/sessions/{session1_id}/bulk",
        headers=teacher1_headers,
        json={
            "records": [
                {"student_id": str(student_a_id), "status": "ABSENT"},
                {"student_id": str(student_b_id), "status": "ABSENT"},
            ]
        },
    )
    assert res.status_code == 200
    bulk_res = res.json()
    assert bulk_res["total_processed"] == 2
    assert bulk_res["successful_count"] == 0  # Both already exist, none overwritten!
    assert bulk_res["results"][0]["already_marked"] == True
    print("15. Bulk Manual Marking Does NOT Overwrite Existing Records: PASS")

    # 19. Session Roster-Aware Record Listing
    res = client.get(
        f"/api/attendance/sessions/{session1_id}/records",
        headers=teacher1_headers,
    )
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) == 2  # Student A and Student B
    print("16. Session Roster-Aware Record Listing: PASS")

    # 20. Session Closing Lifecycle (OPEN -> CLOSED)
    res = client.patch(
        f"/api/attendance/sessions/{session1_id}/close",
        headers=teacher1_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CLOSED"
    print("17. Close Session (OPEN -> CLOSED): PASS")

    # Closed Session Rejects Normal Attendance Marking
    with open(img_a1_path, "rb") as f:
        res = client.post(
            f"/api/attendance/sessions/{session1_id}/mark-face",
            headers=teacher1_headers,
            files={"file": ("frame.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    assert res.json()["attendance_marked"] == False

    res = client.post(
        f"/api/attendance/sessions/{session1_id}/manual",
        headers=teacher1_headers,
        json={"student_id": str(student_b_id), "status": "PRESENT"},
    )
    assert res.status_code == 400
    print("18. Closed Session Rejects Normal Face & Manual Marking: PASS")

    # Invalid Transition Test (CLOSED -> OPEN -> 400 Bad Request)
    res = client.patch(
        f"/api/attendance/sessions/{session1_id}/close",
        headers=teacher1_headers,
    )
    assert res.status_code == 400
    print("19. Invalid Session Lifecycle Transition Rejected: PASS")

    # 21. Explicit Attendance Record Correction Endpoint (Works on CLOSED sessions)
    # Find Student A's record ID
    st_a_rec = [r for r in recs if r["student_id"] == str(student_a_id)][0]
    rec_id = st_a_rec["id"]

    res = client.patch(
        f"/api/attendance/records/{rec_id}",
        headers=teacher1_headers,
        json={"status": "EXCUSED", "remarks": "Medical leave approved"},
    )
    assert res.status_code == 200
    updated_rec = res.json()
    assert updated_rec["status"] == "EXCUSED"
    assert updated_rec["marking_method"] == "MANUAL"
    assert updated_rec["similarity"] is not None  # Preserves original similarity for audit!
    print("20. Explicit Attendance Correction on CLOSED Session (EXCUSED): PASS")

    # 22. Create Second Session & Test Cancellation Lifecycle (OPEN -> CANCELLED)
    res = client.post(
        "/api/attendance/sessions",
        headers=teacher1_headers,
        json={"class_id": str(class_id), "subject_id": str(subject_id)},
    )
    assert res.status_code == 201
    session2_id = res.json()["id"]

    res = client.patch(
        f"/api/attendance/sessions/{session2_id}/cancel",
        headers=teacher1_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"
    print("21. Cancel Session (OPEN -> CANCELLED): PASS")

    # 23. Create Third Session & Close it without marking Student B (Derived Absence Test)
    res = client.post(
        "/api/attendance/sessions",
        headers=teacher1_headers,
        json={"class_id": str(class_id), "subject_id": str(subject_id)},
    )
    assert res.status_code == 201
    session3_id = res.json()["id"]

    # Mark Student A PRESENT in Session 3
    with open(img_a1_path, "rb") as f:
        client.post(
            f"/api/attendance/sessions/{session3_id}/mark-face",
            headers=teacher1_headers,
            files={"file": ("frame.jpg", f, "image/jpeg")},
        )
    # Student B has NO record in Session 3

    # Close Session 3
    client.patch(
        f"/api/attendance/sessions/{session3_id}/close",
        headers=teacher1_headers,
    )
    print("22. Derived Absence Setup (Session 3 Closed): PASS")

    # 24. Student Attendance History & Privacy Check
    res = client.get("/api/attendance/student/me", headers=student_a_headers)
    assert res.status_code == 200
    my_history = res.json()
    assert len(my_history) >= 1
    print("23. Logged-In Student Attendance History (/student/me): PASS")

    # Student A attempts accessing Student B history -> 403 Forbidden
    res = client.get(
        f"/api/attendance/students/{str(student_b_id)}",
        headers=student_a_headers,
    )
    assert res.status_code == 403
    print("24. Student Accessing Another Student History -> 403 Forbidden: PASS")

    # 25. Student Summary Calculation & Explicit Percentage Rule Verification
    # Student B in Session 1: LATE. In Session 3 (Closed): Derived ABSENT.
    # Total closed sessions for Class A = 2 (Session 1 & Session 3; Session 2 was CANCELLED and excluded!).
    # Student B: PRESENT=0, LATE=1, ABSENT=1, EXCUSED=0.
    # Eligible sessions = 0 + 1 + 1 = 2.
    # Percentage = (0 + 1) / 2 * 100 = 50.0%.
    res = client.get(
        f"/api/attendance/students/{str(student_b_id)}/summary",
        headers=teacher1_headers,
    )
    assert res.status_code == 200
    sum_b = res.json()
    assert sum_b["total_sessions"] == 2
    assert sum_b["eligible_sessions"] == 2
    assert sum_b["present"] == 0
    assert sum_b["late"] == 1
    assert sum_b["absent"] == 1
    assert sum_b["excused"] == 0
    assert sum_b["attendance_percentage"] == 50.0
    print("25. Explicit Percentage Rule & Derived Absence Verification (50.0%): PASS")

    # Student A Summary Verification
    # Session 1: EXCUSED (excluded from denominator!). Session 3: PRESENT.
    # Total closed sessions = 2.
    # Student A: PRESENT=1, LATE=0, ABSENT=0, EXCUSED=1.
    # Eligible sessions = 1 + 0 + 0 = 1.
    # Percentage = (1 + 0) / 1 * 100 = 100.0%. (EXCUSED correctly excluded!).
    res = client.get(
        f"/api/attendance/students/{str(student_a_id)}/summary",
        headers=teacher1_headers,
    )
    assert res.status_code == 200
    sum_a = res.json()
    assert sum_a["total_sessions"] == 2
    assert sum_a["eligible_sessions"] == 1
    assert sum_a["excused"] == 1
    assert sum_a["present"] == 1
    assert sum_a["attendance_percentage"] == 100.0
    print("26. EXCUSED Excluded From Denominator Rule (100.0%): PASS")

    # 26. Subject-Wise Attendance Summary
    res = client.get(
        f"/api/attendance/students/{str(student_a_id)}/summary/subjects",
        headers=teacher1_headers,
    )
    assert res.status_code == 200
    sub_sums = res.json()
    assert len(sub_sums) >= 1
    assert sub_sums[0]["subject_code"] == "CS501"
    print("27. Subject-Wise Attendance Summary: PASS")

    # 27. Health Endpoint Verification
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["database"] == "connected"
    assert res.json()["face_model"] == "ready"
    print("28. Health Check (/api/health with face_model status): PASS")

    # 28. STRICT SCOPE BOUNDARY: Zero ML/Prediction/SMS code created
    collections = db.list_collection_names()
    assert "predictions" not in collections
    assert "ml_models" not in collections
    print("29. STRICT BOUNDARY: Zero ML/Prediction collections: PASS")

    print("\nALL STEP 4 INTEGRATION & SECURITY TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_step4_integration_tests()
