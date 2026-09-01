from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse


class StudentCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    student_id: str = Field(..., description="Unique Student Roll/Registration ID")
    roll_number: str = Field(...)
    department: str = Field(...)
    semester: int = Field(..., ge=1, le=10)
    section: str = Field(..., min_length=1, max_length=5)
    class_id: Optional[str] = None
    admission_year: int = Field(...)


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=10)
    section: Optional[str] = None
    class_id: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    id: str
    user_id: str
    student_id: str
    roll_number: str
    department: str
    semester: int
    section: str
    class_id: Optional[str] = None
    admission_year: int
    is_active: bool = True
    user: Optional[UserResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
