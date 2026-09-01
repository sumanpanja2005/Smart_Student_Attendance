from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.student import StudentResponse
from app.schemas.teacher import TeacherResponse
from app.schemas.subject import SubjectResponse


class ClassCreate(BaseModel):
    class_name: str = Field(..., description="e.g., B.Tech IT-3A")
    department: str = Field(...)
    semester: int = Field(..., ge=1, le=10)
    section: str = Field(..., min_length=1, max_length=5)
    academic_year: str = Field(..., description="e.g., 2025-2026")


class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=10)
    section: Optional[str] = None
    academic_year: Optional[str] = None


class ClassResponse(BaseModel):
    id: str
    class_name: str
    department: str
    semester: int
    section: str
    academic_year: str
    student_ids: List[str] = Field(default_factory=list)
    teacher_ids: List[str] = Field(default_factory=list)
    subject_ids: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ClassDetailResponse(ClassResponse):
    students: List[StudentResponse] = Field(default_factory=list)
    teachers: List[TeacherResponse] = Field(default_factory=list)
    subjects: List[SubjectResponse] = Field(default_factory=list)
