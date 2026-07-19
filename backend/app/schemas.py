from typing import Any

from pydantic import BaseModel, Field


class StudentLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class StudentLoginResponse(BaseModel):
    message: str
    user: dict[str, Any]


class TrustedQuestion(BaseModel):
    subject: str
    question: str
    student_answer: str = ""
    knowledge: list[str] = Field(default_factory=list)
    question_type: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PerceptionStage(BaseModel):
    stage: str = "perception"
    trusted_question: TrustedQuestion
    source: str = "qwen-vl"


class SkillRouting(BaseModel):
    skill: str
    reason: str


class ReasoningComment(BaseModel):
    kind: str
    status: str
    detail: str


class GradingStage(BaseModel):
    stage: str = "grading"
    routing: SkillRouting
    score: float = 0
    max_score: float = 100
    judgement: str = "pending"
    process_score: float | None = None
    result_score: float | None = None
    comments: list[ReasoningComment] = Field(default_factory=list)


class ErrorCause(BaseModel):
    kind: str
    evidence: str
    severity: str


class AbilityTag(BaseModel):
    kind: str
    level: str


class DiagnosisStage(BaseModel):
    stage: str = "diagnosis"
    error_causes: list[ErrorCause] = Field(default_factory=list)
    knowledge_points: list[str] = Field(default_factory=list)
    ability_tags: list[AbilityTag] = Field(default_factory=list)
    student_profile_delta: dict[str, Any] = Field(default_factory=dict)


class HomeworkStages(BaseModel):
    perception: PerceptionStage
    grading: GradingStage
    diagnosis: DiagnosisStage


class HomeworkAnalysisResponse(BaseModel):
    message: str
    subject: str
    filename: str
    model: str
    pipeline_version: str
    stages: HomeworkStages
