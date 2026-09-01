from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskFactor(BaseModel):
    factor: str
    severity: str
    description: str


class StudentRiskResponse(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    class_name: str
    attendance_percentage: float
    risk_score: float
    risk_level: RiskLevel
    risk_factors: List[str]


class AttendanceTrendPoint(BaseModel):
    period: str
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float


class AttendanceTrendResponse(BaseModel):
    period_type: str
    points: List[AttendanceTrendPoint]


class StudentAnalyticsResponse(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    class_name: str
    overall_attendance_percentage: float
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    eligible_session_count: int
    total_session_count: int
    risk_score: float
    risk_level: RiskLevel
    risk_factors: List[str]
    subject_summaries: List[dict]
    recent_trend: List[AttendanceTrendPoint]
    calculated_at: datetime


class ClassAnalyticsResponse(BaseModel):
    class_id: str
    class_name: str
    department: str
    total_students: int
    average_attendance_percentage: float
    students_below_threshold: int
    risk_distribution: Dict[str, int]
    subject_averages: List[dict]
    present_count: int
    absent_count: int
    late_count: int


class SubjectAnalyticsResponse(BaseModel):
    subject_id: str
    subject_code: str
    subject_name: str
    total_sessions: int
    average_attendance_percentage: float
    present_count: int
    absent_count: int
    late_count: int


class AnalyticsDashboardResponse(BaseModel):
    total_students: int
    overall_average_percentage: float
    risk_counts: Dict[str, int]
    recent_sessions_count: int
    top_at_risk_students: List[StudentRiskResponse]
