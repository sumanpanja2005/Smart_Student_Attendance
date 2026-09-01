from pydantic import BaseModel, Field
from typing import Literal


class HealthResponse(BaseModel):
    status: str = Field(default="ok", example="ok")
    message: str = Field(
        default="Smart Attendance API is running",
        example="Smart Attendance API is running",
    )
    database: Literal["connected", "disconnected", "not_configured"] = Field(
        description="MongoDB connection state", example="connected"
    )
