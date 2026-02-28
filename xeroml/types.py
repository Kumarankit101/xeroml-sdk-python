"""XeroML SDK types — mirrors the API Pydantic models exactly."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LatentStates(BaseModel):
    goal_intent: str
    action_readiness: str = Field(pattern=r"^(exploring|deciding|executing)$")
    ambiguity_level: str = Field(pattern=r"^(clear|partial|conflicting)$")
    risk_sensitivity: str = Field(pattern=r"^(low|medium|high)$")
    intent_scope: str = Field(pattern=r"^(single|compound|multi_step)$")


class IntentMeta(BaseModel):
    source: str = "user_input"
    confidence: float = Field(ge=0.0, le=1.0)
    negotiation_history: list[str] = []
    latent_states: LatentStates


class SubGoal(BaseModel):
    id: str
    goal: str
    status: str = Field(
        default="pending",
        pattern=r"^(pending|active|done|blocked|abandoned|background)$",
    )
    priority: float = Field(ge=0.0, le=1.0)
    success_criteria: list[str] = []
    constraints: list[str] = []
    uncertainty: float = Field(ge=0.0, le=1.0, default=0.5)
    context_requirements: list[str] = []
    modality: str = "text"
    dependencies: list[str] = []
    children: list[SubGoal] = []


class IntentGraph(BaseModel):
    schema_version: str = "0.1.0"
    root_goal: str
    sub_goals: list[SubGoal]
    meta: IntentMeta


class ParseResponse(BaseModel):
    graph: IntentGraph
    session_id: str | None = None
    request_id: str
    latency_ms: int


class DriftReport(BaseModel):
    detected: bool
    drift_type: str | None = None
    severity: float | None = None
    description: str | None = None
    previous_goal: str | None = None
    current_goal: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    status: str
    turn_count: int
    created_at: str
    updated_at: str


class CreditInfo(BaseModel):
    used: int
    total: int
    remaining: int


class UsageMonth(BaseModel):
    month: str
    parse_calls: int
    drift_checks: int
    session_creates: int
    total_latency_ms: int = 0


class UsageInfo(BaseModel):
    credits: CreditInfo
    tier: str
    rate_limit: int
    usage: list[UsageMonth] = []
