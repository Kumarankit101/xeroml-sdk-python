"""XeroML SDK types — mirrors the API Pydantic models (v3 / 0.3.0)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Constraint(BaseModel):
    text: str
    source: Literal["stated", "assumed"] = "stated"
    turn: int = 1


class SuccessCriterion(BaseModel):
    text: str
    source: Literal["stated", "assumed"] = "stated"
    turn: int = 1


class Unknown(BaseModel):
    question: str
    impact: Literal["high", "medium", "low"] = "medium"


class Goal(BaseModel):
    id: str
    objective: str
    status: Literal["pending", "active", "done", "blocked", "abandoned"] = "pending"
    depends_on: list[str] = []
    constraints: list[Constraint] = []
    success_criteria: list[SuccessCriterion] = []
    unknowns: list[Unknown] = []
    outcome: str | None = None


class HistoryEntry(BaseModel):
    turn: int
    type: Literal["created", "refinement", "correction", "pivot", "goal_added", "goal_done"]
    detail: str


class IntentContext(BaseModel):
    motivation: str | None = None
    background: str | None = None


class IntentGraph(BaseModel):
    v: str = "0.3.0"
    directive: str
    objective: str
    type: Literal["build", "fix", "explain", "explore", "decide", "action"]
    confidence: float = Field(ge=0.0, le=1.0)
    phase: Literal["clarifying", "planning", "executing", "done"] = "clarifying"
    urgency: Literal["low", "normal", "high", "critical"] = "normal"
    context: IntentContext = IntentContext()
    constraints: list[Constraint] = []
    rejected: list[str] = []
    implicit: list[str] = []
    success_criteria: list[SuccessCriterion] = []
    unknowns: list[Unknown] = []
    goals: list[Goal] = []
    history: list[HistoryEntry] = []


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


class GraphTurn(BaseModel):
    turn_number: int
    graph: IntentGraph
    root_goal: str
    confidence: float
    sub_goal_count: int
    provider: str
    latency_ms: int
    created_at: str


class DriftEvent(BaseModel):
    turn_number: int
    drift_type: str
    severity: float
    description: str
    previous_goal: str | None = None
    current_goal: str | None = None
    created_at: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    status: str
    turn_count: int
    current_graph: IntentGraph | None = None
    graphs: list[GraphTurn] = []
    drift_events: list[DriftEvent] = []
