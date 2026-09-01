import logging
from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from app.api.deps import (
    get_current_user,
    require_role,
    require_admin,
    require_teacher,
)
from app.db.mongo import db_manager
from app.schemas.attendance import (
    AttendanceSessionCreate,
    AttendanceSessionResponse,
    AttendanceRecordResponse,
    FaceAttendanceResponse,
    ManualAttendanceRequest,
    BulkAttendanceRequest,
    BulkAttendanceResponse,
    AttendanceUpdateRequest,
    AttendanceSummaryResponse,
    SubjectAttendanceSummary,
)
from app.services.attendance_service import AttendanceService
from app.services.attendance_repository import AttendanceRepository

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])


def _get_students_by_class(class_id_val: str) -> List[dict]:
    db = db_manager.db
    try:
        obj_id = ObjectId(class_id_val)
        return list(db.students.find({"$or": [{"class_id": str(class_id_val)}, {"class_id": obj_id}]}))
    except Exception:
        return list(db.students.find({"class_id": str(class_id_val)}))


# --- SESSIONS ---
@router.post(
    "/sessions",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create attendance session",
)
def create_attendance_session(
    payload: AttendanceSessionCreate,
    current_user: dict = Depends(require_teacher),
):
    """
    Creates a new attendance session in OPEN state.
    Verifies class/subject existence and teacher assignment.
    """
    session = AttendanceService.create_session(
        current_user=current_user,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        session_date=payload.session_date,
    )
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_SESSION_CREATED",
        message=f"Created attendance session for class {payload.class_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        session_id=session.get("id"),
    )
    return session


@router.get(
    "/sessions",
    response_model=List[AttendanceSessionResponse],
    summary="List attendance sessions",
)
def list_attendance_sessions(
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    session_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Lists attendance sessions with optional filters.
    Students receive only sessions for their enrolled class.
    """
    filters = {}
    if class_id:
        filters["class_id"] = class_id
    if subject_id:
        filters["subject_id"] = subject_id
    if teacher_id:
        filters["teacher_id"] = teacher_id
    if session_date:
        filters["session_date"] = session_date
    if status:
        filters["status"] = status

    # Student restriction: enforce own class_id
    if current_user["role"] == "STUDENT":
        db = db_manager.db
        student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
        if student_doc and student_doc.get("class_id"):
            filters["class_id"] = str(student_doc["class_id"])
        else:
            return []

    raw_sessions = AttendanceRepository.list_sessions(filters)
    enriched = [AttendanceService._enrich_session_doc(s) for s in raw_sessions]
    return enriched


@router.get(
    "/sessions/{session_id}",
    response_model=AttendanceSessionResponse,
    summary="Get session details and metadata",
)
def get_attendance_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieves session metadata, class roster count, and status breakdown."""
    session = AttendanceRepository.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
        )

    # Student restriction check
    if current_user["role"] == "STUDENT":
        db = db_manager.db
        student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
        if not student_doc or str(student_doc.get("class_id")) != str(session["class_id"]):
            from app.services.security_audit_service import SecurityAuditService
            SecurityAuditService.log_idor_attempt(
                actor_user_id=current_user["id"],
                actor_role=current_user["role"],
                target_resource_type="ATTENDANCE_SESSION",
                target_resource_id=session_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this session.",
            )

    return AttendanceService._enrich_session_doc(session)


@router.patch(
    "/sessions/{session_id}/close",
    response_model=AttendanceSessionResponse,
    summary="Close attendance session",
)
def close_attendance_session(
    session_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Closes an OPEN attendance session (OPEN -> CLOSED)."""
    closed = AttendanceService.close_session(current_user, session_id)
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_SESSION_CLOSED",
        message=f"Closed attendance session {session_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        session_id=session_id,
    )
    return closed


@router.patch(
    "/sessions/{session_id}/cancel",
    response_model=AttendanceSessionResponse,
    summary="Cancel attendance session",
)
def cancel_attendance_session(
    session_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Cancels an OPEN attendance session (OPEN -> CANCELLED)."""
    cancelled = AttendanceService.cancel_session(current_user, session_id)
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_SESSION_CANCELLED",
        message=f"Cancelled attendance session {session_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        session_id=session_id,
    )
    return cancelled


# --- ATTENDANCE MARKING ---
@router.post(
    "/sessions/{session_id}/mark-face",
    response_model=FaceAttendanceResponse,
    summary="Mark face-recognition attendance",
)
async def mark_face_attendance(
    session_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_teacher),
):
    """
    Server-side face recognition attendance marking.
    Calls Step 3 face service internally, verifies class enrollment, checks duplicate attendance,
    and records PRESENT/FACE attendance.
    """
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    res = AttendanceService.mark_face_attendance(session_id, image_bytes)
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_MARKED_FACE",
        message=f"Marked face attendance in session {session_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        session_id=session_id,
    )
    return res


@router.post(
    "/sessions/{session_id}/manual",
    summary="Mark single manual attendance",
)
def mark_manual_attendance(
    session_id: str,
    payload: ManualAttendanceRequest,
    current_user: dict = Depends(require_teacher),
):
    """Single manual attendance marking for student in session."""
    res = AttendanceService.mark_manual_attendance(
        current_user=current_user,
        session_id=session_id,
        student_id=payload.student_id,
        att_status=payload.status.value,
        remarks=payload.remarks,
    )
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_MARKED_MANUAL",
        message=f"Marked manual attendance for student {payload.student_id} in session {session_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        session_id=session_id,
    )
    return res


@router.post(
    "/sessions/{session_id}/bulk",
    response_model=BulkAttendanceResponse,
    summary="Bulk manual attendance marking",
)
def bulk_manual_attendance(
    session_id: str,
    payload: BulkAttendanceRequest,
    current_user: dict = Depends(require_teacher),
):
    """
    Bulk manual attendance marking.
    Validates students against session class. Does NOT overwrite existing face records.
    """
    records_dict = [
        {"student_id": r.student_id, "status": r.status.value, "remarks": r.remarks}
        for r in payload.records
    ]
    res = AttendanceService.bulk_manual_attendance(
        current_user=current_user, session_id=session_id, records=records_dict
    )
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_MARKED_BULK",
        message=f"Marked bulk manual attendance for session {session_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
        session_id=session_id,
    )
    return res


@router.patch(
    "/records/{record_id}",
    response_model=AttendanceRecordResponse,
    summary="Correct attendance record",
)
def update_attendance_record(
    record_id: str,
    payload: AttendanceUpdateRequest,
    current_user: dict = Depends(require_teacher),
):
    """
    Explicit attendance correction endpoint.
    Modifies status/remarks even on CLOSED sessions for authorized users.
    """
    status_val = payload.status.value if payload.status else None
    res = AttendanceService.update_attendance_record(
        current_user=current_user,
        record_id=record_id,
        new_status=status_val,
        remarks=payload.remarks,
    )
    from app.services.audit_service import AuditService
    AuditService.log_attendance_event(
        event_type="ATTENDANCE_CORRECTED",
        message=f"Corrected attendance record {record_id}",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return res


# --- ATTENDANCE HISTORY & RECORDS ---
@router.get(
    "/student/me",
    response_model=List[AttendanceRecordResponse],
    summary="Get logged-in student's attendance history",
)
def get_my_attendance_history(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(require_role("STUDENT")),
):
    """Retrieves logged-in student's own attendance records history."""
    db = db_manager.db
    student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
    if not student_doc:
        return []

    student_id_str = str(student_doc["_id"])
    filters = {}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if subject_id:
        filters["subject_id"] = subject_id
    if status:
        filters["status"] = status

    records = AttendanceRepository.list_student_records(student_id_str, filters)
    return [AttendanceService._enrich_record_doc(r) for r in records]


@router.get(
    "/students/{student_id}",
    response_model=List[AttendanceRecordResponse],
    summary="Get student attendance history (Admin/Teacher)",
)
def get_student_attendance_history(
    student_id: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(require_teacher),
):
    """Retrieves attendance history for a specified student."""
    filters = {}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if subject_id:
        filters["subject_id"] = subject_id
    if status:
        filters["status"] = status

    records = AttendanceRepository.list_student_records(student_id, filters)
    return [AttendanceService._enrich_record_doc(r) for r in records]


@router.get(
    "/sessions/{session_id}/records",
    response_model=List[AttendanceRecordResponse],
    summary="Get attendance records for a session (Roster-Aware)",
)
def get_session_attendance_records(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Lists attendance records for a session.
    Roster-aware: includes enrolled students with marked records or derived status.
    """
    session = AttendanceRepository.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
        )

    # Student restriction check
    if current_user["role"] == "STUDENT":
        db = db_manager.db
        student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
        if not student_doc or str(student_doc.get("class_id")) != str(session["class_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view records for this session.",
            )

    db = db_manager.db
    enrolled_students = _get_students_by_class(session["class_id"])
    records = AttendanceRepository.list_session_records(session_id)
    record_by_student = {r["student_id"]: r for r in records}

    final_list = []
    for st in enrolled_students:
        st_id_str = str(st["_id"])
        st_user_id_str = str(st.get("user_id"))

        existing = record_by_student.get(st_id_str) or record_by_student.get(st_user_id_str)
        if existing:
            final_list.append(AttendanceService._enrich_record_doc(existing))
        else:
            # Derived NOT MARKED / ABSENT entry for roster view
            user_doc = db.users.find_one({"_id": st.get("user_id")})
            st_name = f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip() if user_doc else "Student"
            derived_status = "ABSENT" if session["status"] == "CLOSED" else "NOT MARKED"

            final_list.append(
                {
                    "id": f"unmarked_{st_id_str}",
                    "session_id": session_id,
                    "student_id": st_id_str,
                    "class_id": session["class_id"],
                    "subject_id": session["subject_id"],
                    "attendance_date": session["session_date"],
                    "status": derived_status,
                    "marked_by": session["teacher_id"],
                    "marking_method": "DERIVED",
                    "marked_at": session["created_at"],
                    "similarity": None,
                    "remarks": None,
                    "student_name": st_name,
                    "roll_number": st.get("roll_number", ""),
                }
            )

    return final_list


# --- ATTENDANCE SUMMARIES ---
@router.get(
    "/student/me/summary",
    response_model=AttendanceSummaryResponse,
    summary="Get logged-in student's overall attendance summary",
)
def get_my_attendance_summary(
    current_user: dict = Depends(require_role("STUDENT")),
):
    """
    Calculates overall attendance summary for logged-in student.
    Formula: (PRESENT + LATE) / (PRESENT + ABSENT + LATE) * 100.
    EXCUSED status excluded from denominator.
    """
    db = db_manager.db
    student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
    if not student_doc:
        return AttendanceSummaryResponse(
            total_sessions=0,
            eligible_sessions=0,
            present=0,
            absent=0,
            late=0,
            excused=0,
            attendance_percentage=0.0,
        )

    student_id_str = str(student_doc["_id"])
    return AttendanceRepository.calculate_student_summary(student_id_str)


@router.get(
    "/students/{student_id}/summary",
    response_model=AttendanceSummaryResponse,
    summary="Get student overall attendance summary (Admin/Teacher)",
)
def get_student_attendance_summary(
    student_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Calculates overall attendance summary for a specified student."""
    return AttendanceRepository.calculate_student_summary(student_id)


@router.get(
    "/student/me/summary/subjects",
    response_model=List[SubjectAttendanceSummary],
    summary="Get logged-in student's subject-wise attendance summary",
)
def get_my_subject_attendance_summary(
    current_user: dict = Depends(require_role("STUDENT")),
):
    """Calculates subject-wise attendance summary for logged-in student."""
    db = db_manager.db
    student_doc = db.students.find_one({"user_id": ObjectId(current_user["id"])})
    if not student_doc:
        return []

    student_id_str = str(student_doc["_id"])
    return AttendanceRepository.calculate_subject_summaries(student_id_str)


@router.get(
    "/students/{student_id}/summary/subjects",
    response_model=List[SubjectAttendanceSummary],
    summary="Get student subject-wise attendance summary (Admin/Teacher)",
)
def get_student_subject_attendance_summary(
    student_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Calculates subject-wise attendance summary for a specified student."""
    return AttendanceRepository.calculate_subject_summaries(student_id)
