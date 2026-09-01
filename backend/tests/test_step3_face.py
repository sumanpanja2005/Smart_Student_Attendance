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


def run_step3_integration_tests():
    print("============================================================")
    print(" STEP 3 INTEGRATION & ACCESSIBILITY TEST SUITE")
    print("============================================================")

    # Clean collections
    db.users.delete_many({})
    db.students.delete_many({})
    db.teachers.delete_many({})
    db.subjects.delete_many({})
    db.classes.delete_many({})
    db.face_embeddings.delete_many({})

    now = datetime.now(timezone.utc)

    # 1. Setup Admin Account
    admin_user_id = db.users.insert_one(
        {
            "email": "admin@step3.edu",
            "password_hash": hash_password("AdminPass123!"),
            "role": "ADMIN",
            "first_name": "System",
            "last_name": "Admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 2. Setup Student A Account
    student_a_user_id = db.users.insert_one(
        {
            "email": "student_a@step3.edu",
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
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # 3. Setup Student B Account
    student_b_user_id = db.users.insert_one(
        {
            "email": "student_b@step3.edu",
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
            "admission_year": 2023,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ).inserted_id

    # Admin Login
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@step3.edu", "password": "AdminPass123!"},
    )
    assert res.status_code == 200
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("1. Admin Login: PASS")

    # Student A Login
    res = client.post(
        "/api/auth/login",
        json={"email": "student_a@step3.edu", "password": "StudentPass123!"},
    )
    assert res.status_code == 200
    student_a_token = res.json()["access_token"]
    student_a_headers = {"Authorization": f"Bearer {student_a_token}"}
    print("2. Student A Login: PASS")

    # Student B Login
    res = client.post(
        "/api/auth/login",
        json={"email": "student_b@step3.edu", "password": "StudentPass123!"},
    )
    assert res.status_code == 200
    student_b_token = res.json()["access_token"]
    student_b_headers = {"Authorization": f"Bearer {student_b_token}"}
    print("3. Student B Login: PASS")

    # Load image fixtures
    fixtures_dir = os.path.join(backend_dir, "tests", "fixtures")
    img_a1_path = os.path.join(fixtures_dir, "person_a_1.jpg")
    img_a2_path = os.path.join(fixtures_dir, "person_a_2.jpg")
    img_b1_path = os.path.join(fixtures_dir, "person_b_1.jpg")
    img_multi_path = os.path.join(fixtures_dir, "multiple_faces.jpg")

    # 4. Admin Register Sample 1 for Student A
    with open(img_a1_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=admin_headers,
            data={"student_id": str(student_a_id)},
            files={"file": ("person_a_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200, f"Register sample 1 failed: {res.text}"
    assert res.json()["samples_registered"] == 1
    print("4. Admin Register Sample 1 (Student A): PASS")

    # 5. Student A Registers Sample 2 for Themselves
    with open(img_a2_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=student_a_headers,
            data={"student_id": str(student_a_id)},
            files={"file": ("person_a_2.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200, f"Register sample 2 failed: {res.text}"
    assert res.json()["samples_registered"] == 2
    print("5. Student A Register Sample 2 (Self Ownership): PASS")

    # 6. Verify GET /api/face/student/{student_a_id}
    res = client.get(
        f"/api/face/student/{str(student_a_id)}", headers=student_a_headers
    )
    assert res.status_code == 200
    st_data = res.json()
    assert st_data["registered"] == True
    assert st_data["sample_count"] == 2
    assert "embedding" not in st_data  # Privacy check: raw embedding never exposed!
    print("6. Face Status Metadata (Privacy Protected): PASS")

    # 7. Student Ownership Security Violation Check (Student B attempting to register Student A)
    with open(img_b1_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=student_b_headers,
            data={"student_id": str(student_a_id)},
            files={"file": ("person_b_1.jpg", f, "image/jpeg")},
        )
    assert (
        res.status_code == 403
    ), f"Expected 403 Forbidden on ownership violation, got {res.status_code}"
    print(
        "7. Role Security (Student B attempting to register Student A -> 403 Forbidden): PASS"
    )

    # 8. Cross-Student Duplicate Face Prevention
    # Admin attempting to register Student A's face image (person_a_1.jpg) for Student B
    with open(img_a1_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=admin_headers,
            data={"student_id": str(student_b_id)},
            files={"file": ("person_a_1.jpg", f, "image/jpeg")},
        )
    assert (
        res.status_code == 400
    ), f"Expected 400 Bad Request on duplicate face, got {res.status_code}"
    assert "already be registered" in res.json()["detail"]
    print("8. Cross-Student Duplicate Face Rejection: PASS")

    # 9. Register Student B Face
    # Temporarily set duplicate threshold to 0.95 for synthetic drawings test
    old_thresh = settings.FACE_MATCH_THRESHOLD
    settings.FACE_MATCH_THRESHOLD = 0.95

    with open(img_b1_path, "rb") as f:
        res = client.post(
            "/api/face/register",
            headers=admin_headers,
            data={"student_id": str(student_b_id)},
            files={"file": ("person_b_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200, f"Register Student B face failed: {res.text}"
    print("9. Admin Register Student B Face: PASS")

    # Restore configurable threshold
    settings.FACE_MATCH_THRESHOLD = old_thresh

    # 10. Face Recognition (Recognize Student A)
    with open(img_a1_path, "rb") as f:
        res = client.post(
            "/api/face/recognize",
            headers=student_a_headers,
            files={"file": ("person_a_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    rec_res = res.json()
    assert rec_res["recognized"] == True
    assert rec_res["student_id"] == str(student_a_id)
    assert rec_res["similarity"] >= 0.50
    print("10. Recognition (Student A Matched Successfully): PASS")

    # 11. Face Recognition (Recognize Student B)
    with open(img_b1_path, "rb") as f:
        res = client.post(
            "/api/face/recognize",
            headers=student_b_headers,
            files={"file": ("person_b_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    rec_res = res.json()
    assert rec_res["recognized"] == True
    assert rec_res["student_id"] == str(student_b_id)
    print("11. Recognition (Student B Matched Successfully): PASS")

    # 12. Face Recognition (Unknown Face Image)
    import cv2
    import numpy as np

    img_unk = np.ones((640, 640, 3), dtype=np.uint8) * 40
    cv2.ellipse(img_unk, (320, 280), (130, 170), 0, 0, 360, (50, 80, 100), -1)
    _, unk_encoded = cv2.imencode(".jpg", img_unk)

    res = client.post(
        "/api/face/recognize",
        headers=admin_headers,
        files={"file": ("unknown.jpg", unk_encoded.tobytes(), "image/jpeg")},
    )
    assert res.status_code == 200
    rec_res = res.json()
    assert rec_res["recognized"] == False
    assert rec_res["student_id"] is None
    print("12. Unknown Face Handling (recognized=false, student_id=null): PASS")

    # 13. Multiple Faces Image Rejection
    with open(img_multi_path, "rb") as f:
        res = client.post(
            "/api/face/recognize",
            headers=admin_headers,
            files={"file": ("multiple_faces.jpg", f, "image/jpeg")},
        )
    assert res.status_code in (200, 400)
    if res.status_code == 200:
        assert res.json()["recognized"] == False
        assert "Multiple faces" in res.json()["message"]
    print("13. Multiple Faces Image Rejection: PASS")

    # 14. Admin Soft-Deactivate Student A Face
    res = client.delete(
        f"/api/face/student/{str(student_a_id)}", headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["deactivated_count"] >= 1
    print("14. Admin Soft-Deactivate Student A Face: PASS")

    # 15. Verify Recognition Ignores Deactivated Embeddings
    with open(img_a1_path, "rb") as f:
        res = client.post(
            "/api/face/recognize",
            headers=admin_headers,
            files={"file": ("person_a_1.jpg", f, "image/jpeg")},
        )
    assert res.status_code == 200
    assert res.json()["student_id"] != str(
        student_a_id
    )  # Deactivated embedding is ignored!
    print("15. Recognition Ignores Deactivated Embeddings: PASS")

    # 16. Health Endpoint Check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert "face_model" in res.json()
    print("16. Health Check (/api/health with face_model status): PASS")

    # 17. Zero Attendance Check
    assert "attendance" not in db.list_collection_names()
    print("17. STRICT BOUNDARY: Zero attendance collections created: PASS")

    print("\nALL STEP 3 INTEGRATION & SECURITY TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_step3_integration_tests()
