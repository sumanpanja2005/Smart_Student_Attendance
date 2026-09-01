from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    STUDENT_ATTENDANCE = "STUDENT_ATTENDANCE"
    CLASS_ATTENDANCE = "CLASS_ATTENDANCE"
    SUBJECT_ATTENDANCE = "SUBJECT_ATTENDANCE"
    ANALYTICS_RISK = "ANALYTICS_RISK"


class StudentReportRequest(BaseModel):
    student_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    subject_id: Optional[str] = None


class ClassReportRequest(BaseModel):
    class_id: str
    subject_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SubjectReportRequest(BaseModel):
    class_id: str
    subject_id: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class ReportMetadataResponse(BaseModel):
    id: str
    report_type: ReportType
    title: str
    generated_by: str
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    subject_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    file_name: str
    created_at: datetime
