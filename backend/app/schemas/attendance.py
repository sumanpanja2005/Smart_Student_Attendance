from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class MarkingMethod(str, Enum):
    FACE = "FACE"
    MANUAL = "MANUAL"


class SessionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class AttendanceSessionCreate(BaseModel):
    class_id: str = Field(..., description="ID of the class/section")
    subject_id: str = Field(..., description="ID of the subject")
    session_date: Optional[str] = Field(
        None, description="Session date in YYYY-MM-DD format"
    )


class AttendanceSessionResponse(BaseModel):
    id: str
    class_id: str
    subject_id: str
    teacher_id: str
    session_date: str
    start_time: str
    end_time: Optional[str] = None
    status: str
    created_by: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    total_students: int = 0
    present_count: int = 0
    absent_count: int = 0
    late_count: int = 0
    excused_count: int = 0


class AttendanceRecordResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    class_id: str
    subject_id: str
    attendance_date: str
    status: str
    marked_by: str
    marking_method: str
    marked_at: datetime
    similarity: Optional[float] = None
    remarks: Optional[str] = None
    student_name: Optional[str] = None
    roll_number: Optional[str] = None


class FaceAttendanceResponse(BaseModel):
    success: bool
    recognized: bool
    attendance_marked: bool
    already_marked: bool = False
    student_id: Optional[str] = None
    similarity: Optional[float] = None
    status: Optional[str] = None
    message: str


class ManualAttendanceRequest(BaseModel):
    student_id: str
    status: AttendanceStatus
    remarks: Optional[str] = None


class BulkAttendanceItem(BaseModel):
    student_id: str
    status: AttendanceStatus
    remarks: Optional[str] = None


class BulkAttendanceRequest(BaseModel):
    records: List[BulkAttendanceItem]


class BulkAttendanceResponseItem(BaseModel):
    student_id: str
    success: bool
    already_marked: bool = False
    message: str


class BulkAttendanceResponse(BaseModel):
    session_id: str
    total_processed: int
    successful_count: int
    results: List[BulkAttendanceResponseItem]


class AttendanceUpdateRequest(BaseModel):
    status: Optional[AttendanceStatus] = None
    remarks: Optional[str] = None


class AttendanceSummaryResponse(BaseModel):
    total_sessions: int
    eligible_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float


class SubjectAttendanceSummary(BaseModel):
    subject_id: str
    subject_code: str
    subject_name: str
    total_sessions: int
    eligible_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float
