from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class FaceRegisterResponse(BaseModel):
    success: bool = True
    message: str = Field(default="Face sample registered successfully")
    student_id: str
    samples_registered: int


class FaceRecognitionResponse(BaseModel):
    recognized: bool
    student_id: Optional[str] = None
    student: Optional[Dict[str, Any]] = None
    similarity: float = Field(
        description="Cosine similarity score between face embedding and registered embeddings (0.0 to 1.0)",
        example=0.87,
    )
    message: str


class FaceStatusResponse(BaseModel):
    registered: bool
    sample_count: int
    model_name: str = "buffalo_s"
    updated_at: Optional[datetime] = None
