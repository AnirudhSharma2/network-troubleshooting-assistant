"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime


# ── Auth Schemas ──────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    role: Optional[str] = None
    full_name: Optional[str] = None


# ── Analysis Schemas ──────────────────────────────────────────

class AnalysisRequest(BaseModel):
    title: str = Field(default="Untitled Analysis", max_length=200)
    input_text: str = Field(..., min_length=10)
    input_type: str = Field(default="cli_output")


class IssueDetail(BaseModel):
    rule: str
    failure_type: str
    device: str
    interface: str
    severity: str  # critical | high | medium | low
    detail: str
    fix_command: Optional[str] = None


class ScoreBreakdown(BaseModel):
    total_score: float
    routing_score: float
    interface_score: float
    vlan_score: float
    ip_score: float
    deductions: list[dict[str, Any]]


class ParsedSummary(BaseModel):
    hostname: str
    device_count: int = 1
    device_names: list[str] = Field(default_factory=list)
    interface_count: int = 0
    route_count: int = 0
    vlan_count: int = 0
    router_process_count: int = 0


class EvidenceCommandCheck(BaseModel):
    key: str
    label: str
    detected: bool
    weight: int
    why: str
    recommendation: str


class MissingCommandRecommendation(BaseModel):
    command: str
    reason: str


class EvidenceReport(BaseModel):
    summary: str
    overall_score: float
    confidence: str
    device_count: int
    command_checks: list[EvidenceCommandCheck]
    missing_commands: list[MissingCommandRecommendation]
    notes: list[str] = Field(default_factory=list)


class FixPlanItem(BaseModel):
    priority: int
    title: str
    summary: str
    failure_type: str
    severity: str
    issue_count: int
    devices: list[str]
    issue_refs: list[str]
    commands: list[str]


class AnalysisResponse(BaseModel):
    id: int
    user_id: int
    title: str
    input_type: str
    issues: list[IssueDetail]
    health_score: float
    score_breakdown: Optional[ScoreBreakdown] = None
    parsed_summary: Optional[ParsedSummary] = None
    evidence: Optional[EvidenceReport] = None
    fix_plan: list[FixPlanItem] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    engine_mode: str = "deterministic_copilot"
    explanation: str
    fix_commands: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    id: int
    title: str
    health_score: Optional[float] = None
    issue_count: int = 0
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Scenario Schemas ──────────────────────────────────────────

class ScenarioGenerateRequest(BaseModel):
    scenario_type: str = Field(..., pattern="^(routing|vlan|interface|ip|mixed)$")
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class ScenarioResponse(BaseModel):
    id: int
    title: str
    scenario_type: str
    difficulty: str
    description: str
    network_config: Optional[str] = None
    expected_issues: Optional[list[dict[str, Any]]] = None
    instructions: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Dashboard Schemas ─────────────────────────────────────────

class DashboardResponse(BaseModel):
    total_analyses: int
    average_health_score: float
    recent_analyses: list[AnalysisSummary]
    error_summary: dict[str, int]  # {failure_type: count}
    health_trend: list[dict[str, Any]]  # [{date, score}]


# ── Admin Schemas ─────────────────────────────────────────────

class AdminAnalytics(BaseModel):
    total_users: int
    total_analyses: int
    average_score: float
    users_by_role: dict[str, int]
    recent_activity: list[dict[str, Any]]
