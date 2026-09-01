from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    subject_code: str = Field(..., description="Unique Subject Code (e.g. IT-501)")
    subject_name: str = Field(..., min_length=1)
    department: str = Field(...)
    semester: int = Field(..., ge=1, le=10)
    credits: int = Field(..., ge=1, le=10)
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=10)
    credits: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = None


class SubjectResponse(BaseModel):
    id: str
    subject_code: str
    subject_name: str
    department: str
    semester: int
    credits: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
