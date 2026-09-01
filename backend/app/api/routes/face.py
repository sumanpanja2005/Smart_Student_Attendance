import logging
from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.db.mongo import db_manager
from app.schemas.face import (
    FaceRegisterResponse,
    FaceRecognitionResponse,
    FaceStatusResponse,
)
from app.services.face_service import (
    decode_image_bytes,
    detect_and_extract_face,
    validate_face_quality,
    compute_cosine_similarity,
    check_cross_student_duplicate,
)
from app.services.face_repository import FaceRepository

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/face", tags=["Face Recognition"])


@router.post("/register", response_model=FaceRegisterResponse)
async def register_face_sample(
    student_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Registers a face embedding sample for a student.
    Enforces Admin or Self student permission, single face detection, quality validation,
    and cross-student duplicate face prevention.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )

    # 1. Verify student exists
    if not ObjectId.is_valid(student_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student ID format"
        )

    student = db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found"
        )

    # 2. Authorization Enforcement
    user_role = current_user.get("role")
    if user_role == "ADMIN":
        pass  # Admin can register any student
    elif user_role == "STUDENT":
        # Student can ONLY register their own face profile
        if str(student.get("user_id")) != str(current_user.get("_id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are only authorized to register your own face profile.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers and unauthorized roles cannot register student face profiles.",
        )

    # 3. File validation
    image_bytes = await file.read()
    max_bytes = settings.FACE_MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image file exceeds maximum limit of {settings.FACE_MAX_UPLOAD_SIZE_MB}MB.",
        )

    img = decode_image_bytes(image_bytes)
    if img is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file or unsupported format.",
        )

    # 4. Face Detection & Single Face Enforcement
    faces, engine_used = detect_and_extract_face(img)

    if len(faces) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in the uploaded image. Please center your face clearly.",
        )
    if len(faces) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple faces detected. Please ensure only one person is visible in the frame.",
        )

    face = faces[0]
    det_score = face["det_score"]
    bbox = face["bbox"]

    # 5. Quality Validation
    is_valid_quality, quality_msg = validate_face_quality(img, bbox, det_score)
    if not is_valid_quality:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=quality_msg
        )

    # 6. Embedding Extraction & Normalization
    normalized_vec = face["embedding"]

    # 7. Cross-Student Duplicate Face Prevention
    is_duplicate, _ = check_cross_student_duplicate(normalized_vec, student_id)
    if is_duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This face appears to already be registered.",
        )

    # 8. Save Embedding to Database
    existing_samples = FaceRepository.get_student_embeddings(student_id)
    sample_index = len(existing_samples) + 1

    FaceRepository.save_embedding(
        student_id=student_id,
        embedding=normalized_vec,
        model_name=engine_used,
        sample_index=sample_index,
    )

    logger.info(
        f"Registered face sample {sample_index} for student {student_id} ({student.get('student_id')})"
    )

    from app.services.audit_service import AuditService
    AuditService.log_face_event(
        event_type="FACE_REGISTERED",
        message=f"Registered face sample {sample_index} for student {student_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        student_id=student_id,
    )

    return FaceRegisterResponse(
        success=True,
        message="Face sample registered successfully",
        student_id=student_id,
        samples_registered=sample_index,
    )


@router.post("/recognize", response_model=FaceRecognitionResponse)
async def recognize_face(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Recognizes a student face from an uploaded image frame.
    Returns recognized student ID and cosine similarity match score, or unknown face response.
    STRICT: NO attendance database operations are performed.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )

    image_bytes = await file.read()
    img = decode_image_bytes(image_bytes)
    if img is None:
        return FaceRecognitionResponse(
            recognized=False,
            student_id=None,
            similarity=0.0,
            message="Invalid or corrupted image frame.",
        )

    faces, engine_used = detect_and_extract_face(img)

    if len(faces) == 0:
        return FaceRecognitionResponse(
            recognized=False,
            student_id=None,
            similarity=0.0,
            message="No face detected in image frame.",
        )

    if len(faces) > 1:
        return FaceRecognitionResponse(
            recognized=False,
            student_id=None,
            similarity=0.0,
            message="Multiple faces detected. Please ensure only one person is visible.",
        )

    face = faces[0]
    normalized_vec = face["embedding"]

    # Search active registered embeddings
    all_embeddings = FaceRepository.get_all_active_embeddings()
    if not all_embeddings:
        return FaceRecognitionResponse(
            recognized=False,
            student_id=None,
            similarity=0.0,
            message="No registered student face profiles exist in the system.",
        )

    best_match_student_id = None
    highest_similarity = 0.0

    for record in all_embeddings:
        registered_vec = record.get("embedding", [])
        if not registered_vec:
            continue
        sim = compute_cosine_similarity(normalized_vec, registered_vec)
        if sim > highest_similarity:
            highest_similarity = sim
            best_match_student_id = record.get("student_id")

    # Evaluate against configurable threshold
    if (
        best_match_student_id
        and highest_similarity >= settings.FACE_MATCH_THRESHOLD
    ):
        student = db.students.find_one({"_id": ObjectId(best_match_student_id)})
        student_data = None

        if student:
            user = db.users.find_one({"_id": student.get("user_id")})
            student_data = {
                "id": str(student["_id"]),
                "student_id": student.get("student_id"),
                "roll_number": student.get("roll_number"),
                "department": student.get("department"),
                "first_name": user.get("first_name") if user else "",
                "last_name": user.get("last_name") if user else "",
            }

        from app.services.audit_service import AuditService
        AuditService.log_face_event(
            event_type="FACE_RECOGNITION_ATTEMPT",
            message=f"Recognized face for student {best_match_student_id} (similarity: {highest_similarity:.4f})",
            actor_user_id=current_user["id"],
            actor_role=current_user["role"],
            student_id=str(best_match_student_id),
        )

        return FaceRecognitionResponse(
            recognized=True,
            student_id=str(best_match_student_id),
            student=student_data,
            similarity=round(float(highest_similarity), 4),
            message="Face recognized successfully",
        )

    from app.services.audit_service import AuditService
    AuditService.log_face_event(
        event_type="FACE_RECOGNITION_ATTEMPT",
        message=f"Unrecognized face attempt (highest similarity: {highest_similarity:.4f})",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        status="FAILED",
        severity="WARNING",
    )

    return FaceRecognitionResponse(
        recognized=False,
        student_id=None,
        similarity=round(float(highest_similarity), 4),
        message="Unknown face: no registered student matched this face.",
    )


@router.get("/student/{student_id}", response_model=FaceStatusResponse)
async def get_student_face_status(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves safe face registration metadata for a student.
    Never exposes raw embedding vectors.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )

    if not ObjectId.is_valid(student_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student ID format"
        )

    student = db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found"
        )

    user_role = current_user.get("role")
    if user_role == "ADMIN":
        pass
    elif user_role == "STUDENT":
        if str(student.get("user_id")) != str(current_user.get("_id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are only authorized to view your own face status.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized role to inspect student face status.",
        )

    samples = FaceRepository.get_student_embeddings(student_id)
    sample_count = len(samples)
    last_updated = samples[-1].get("updated_at") if samples else None
    model_name = samples[-1].get("model_name", "buffalo_s") if samples else "buffalo_s"

    return FaceStatusResponse(
        registered=sample_count > 0,
        sample_count=sample_count,
        model_name=model_name,
        updated_at=last_updated,
    )


@router.delete("/student/{student_id}")
async def deactivate_student_face(
    student_id: str,
    current_user: dict = Depends(require_admin),
):
    """
    Admin-only deactivation of face embeddings for a student.
    """
    if not ObjectId.is_valid(student_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student ID format"
        )

    modified_count = FaceRepository.deactivate_student_embeddings(student_id)
    return {
        "success": True,
        "message": f"Deactivated {modified_count} face embedding sample(s) for student.",
        "student_id": student_id,
        "deactivated_count": modified_count,
    }
