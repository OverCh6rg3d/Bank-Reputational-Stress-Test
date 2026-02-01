from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel

from backend.models.schemas import (
    AgentArchetype,
    ExecutiveBriefing,
    Scenario,
    SeverityLevel,
    SignalCategory,
    SocialSignal,
    VelocityDataPoint,
    SignalCluster
)

# --- Request Models ---

class StartSimulationRequest(BaseModel):
    scenario_id: Optional[UUID] = None
    scenario_name: Optional[str] = None
    duration_hours: int = 24
    speed_multiplier: float = 1.0


class GenerateSignalsRequest(BaseModel):
    scenario_id: Optional[UUID] = None
    scenario_name: Optional[str] = None
    count_per_level: int = 15
    platform_distribution: Optional[Dict[str, float]] = None


class RunDebateRequest(BaseModel):
    finding: str
    confidence: float
    context: str
    max_turns: int = 3


class GovernanceDecisionRequest(BaseModel):
    incident_id: str  # Changed from UUID to str to allow "inc-001" demo IDs
    decision: str  # "APPROVE", "REJECT", "ESCALATE"
    reviewer_id: str
    notes: Optional[str] = None


class GenerateRecommendationsRequest(BaseModel):
    scenario_name: str
    velocity: float
    sentiment: float
    signal_count: int
    recent_signals: List[str] = []  # Content snippets from recent signals


# --- Response Models ---

class SimulationStateResponse(BaseModel):
    status: str  # "running", "paused", "idle", "completed"
    current_time: Optional[datetime] = None
    velocity_history: List[VelocityDataPoint] = []
    metrics: Dict[str, Any] = {}


class DebateResponse(BaseModel):
    debate_id: str
    transcript: List[Dict[str, Any]]
    final_consensus: str
    refined_confidence: float
    issues_raised: List[str]


class AnalysisResponse(BaseModel):
    cluster_id: UUID
    primary_cause: str
    confidence: float
    reasoning: str
    feature_importance: List[Dict[str, Any]]
