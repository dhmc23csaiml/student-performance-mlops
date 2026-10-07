"""
Pydantic Request and Response Schemas for FastAPI Inference Microservice.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class StudentFeatures(BaseModel):
    student_id: Optional[str] = Field(default="STU_TEST", description="Student ID")
    age: int = Field(default=18, ge=15, le=30, description="Age of student")
    studytime: int = Field(default=2, ge=1, le=4, description="Weekly study time (1: <2h, 2: 2-5h, 3: 5-10h, 4: >10h)")
    failures: int = Field(default=0, ge=0, le=4, description="Past class failures")
    attendance_percentage: float = Field(default=85.0, ge=0.0, le=100.0, description="Overall attendance percentage")
    average_internal_marks: float = Field(default=68.5, ge=0.0, le=100.0, description="Average continuous assessment score")
    assignment_completion_rate: float = Field(default=90.0, ge=0.0, le=100.0, description="Rate of submitted assignments")
    avg_weekly_learning_hours: float = Field(default=8.5, ge=0.0, le=50.0, description="Weekly hours on LMS")
    previous_score_trend: float = Field(default=65.0, ge=0.0, le=100.0, description="Previous semester marks trend")
    gender: str = Field(default="M", description="Gender (M/F)")
    address: str = Field(default="U", description="Address (U=Urban, R=Rural)")
    famsize: str = Field(default="GT3", description="Family size (LE3/GT3)")
    Pstatus: str = Field(default="T", description="Parent cohabitation status (T=Together, A=Apart)")
    schoolsup: str = Field(default="no", description="Extra educational support (yes/no)")
    famsup: str = Field(default="yes", description="Family educational support (yes/no)")
    paid: str = Field(default="no", description="Extra paid classes (yes/no)")
    activities: str = Field(default="yes", description="Extracurricular activities (yes/no)")
    internet: str = Field(default="yes", description="Internet access at home (yes/no)")


class PredictionResponse(BaseModel):
    student_id: str
    dropout_risk_prediction: int = Field(..., description="0 = Safe / Low Risk, 1 = High Dropout Risk")
    risk_probability: float = Field(..., description="Calculated dropout probability (0.0 to 1.0)")
    risk_category: str = Field(..., description="High Risk (Intervention Required) or Low Risk (On Track)")
    primary_risk_triggers: List[str] = Field(..., description="Identified drivers of risk")
    model_version: str
    inference_latency_ms: float


class BatchPredictionRequest(BaseModel):
    students: List[StudentFeatures]


class BatchPredictionResponse(BaseModel):
    total_processed: int
    predictions: List[PredictionResponse]
