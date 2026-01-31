"""
Pydantic schemas for the Reputational Stress-Test Simulator.
These models define the structure of all data flowing through the system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class PlatformSource(str, Enum):
    X_STYLE = "X_Style"
    REDDIT_STYLE = "Reddit_Style"
    NEWS_PORTAL = "News_Portal"
    LINKEDIN_STYLE = "LinkedIn_Style"


class MediaType(str, Enum):
    NONE = "None"
    IMAGE = "Image"
    VIDEO_LINK = "Video_Link"


class SignalCategory(str, Enum):
    FRAUD_RUMOR = "Fraud_Rumor"
    SERVICE_OUTAGE = "Service_Outage"
    COMPETITOR_NEWS = "Competitor_News"
    POSITIVE_NEUTRAL = "Positive_Neutral"
    IRRELEVANT = "Irrelevant"


class DemographicSegment(str, Enum):
    GEN_Z = "GenZ"
    MILLENNIAL = "Millennial"
    SME_OWNER = "SME_Owner"
    HNI = "HNI"  # High Net Worth Individual
    VULNERABLE = "Vulnerable"
    ALL = "All"


class AgentAction(str, Enum):
    IGNORE = "IGNORE"
    LIKE = "LIKE"
    SHARE = "SHARE"
    COMMENT = "COMMENT"
    REPORT = "REPORT"


class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    POSITIVE = "Positive"


class IncidentStatus(str, Enum):
    ACTIVE = "Active"
    MITIGATED = "Mitigated"
    FALSE_POSITIVE = "False_Positive"
    PENDING_REVIEW = "Pending_Review"


class HumanAction(str, Enum):
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PENDING_REVIEW = "Pending_Review"


# =============================================================================
# Core Domain Models
# =============================================================================

class SocialSignal(BaseModel):
    """A single post/article from the synthetic social stream."""
    
    signal_id: UUID
    timestamp: datetime
    platform_source: PlatformSource
    author_id: Optional[UUID] = None
    content_text: str
    parent_id: Optional[UUID] = None
    thread_id: UUID
    media_type: MediaType = MediaType.NONE
    language: str = "en"
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    
    # Ground truth (hidden from AI during inference, used for evaluation)
    gt_category: SignalCategory
    gt_sentiment: float = Field(ge=-1.0, le=1.0)
    gt_is_misinformation: bool = False
    gt_virality_potential: int = Field(ge=0, le=100)

    class Config:
        from_attributes = True


class AgentArchetype(BaseModel):
    """A synthetic customer persona for the contagion simulation."""
    
    agent_id: UUID
    archetype_name: str
    demographic_segment: str  # Can be comma-separated for multiple segments
    financial_literacy: int = Field(ge=1, le=10)
    brand_loyalty: int = Field(ge=0, le=100)
    skepticism_score: int = Field(ge=1, le=10)
    network_influence: int = Field(ge=1, le=100)
    activity_frequency: float = Field(gt=0)  # Posts per day
    preferred_platform: PlatformSource
    core_values: list[str] = Field(default_factory=list)
    persona_description: str = ""
    behavioral_pattern: str = ""

    class Config:
        from_attributes = True


class KnowledgeFact(BaseModel):
    """Official bank facts for RAG-based fact-checking."""
    
    kb_id: UUID
    topic_area: str  # e.g., "Security", "Fees", "Products"
    fact_statement: str
    public_url: str
    last_updated: datetime
    keywords: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class Scenario(BaseModel):
    """Pre-configured crisis scenario for demo/testing."""
    
    scenario_id: UUID
    created_at: datetime
    scenario_name: str
    description: str
    trigger_category: SignalCategory
    target_segment: str  # e.g., "All", "GenZ,Millennial"
    simulation_duration_hours: int = 24
    severity_level: SeverityLevel
    expected_velocity_peak: int = Field(ge=0, le=100)
    recommended_response_time_hours: float
    key_narratives: list[str] = Field(default_factory=list)
    monitoring_keywords: list[str] = Field(default_factory=list)
    potential_impact: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


# =============================================================================
# Simulation Models
# =============================================================================

class SimulationStep(BaseModel):
    """A single step in the agent-based simulation."""
    
    simulation_id: UUID
    step_number: int
    step_time: datetime
    agent_id: UUID
    interacting_with_signal: UUID
    action_taken: AgentAction
    reasoning_trace: str  # LLM explanation
    emotional_state_after: str  # e.g., "Fear", "Anger", "Neutral"
    virality_velocity: float = Field(ge=0)


class VelocityDataPoint(BaseModel):
    """Single data point for velocity chart."""
    
    time: str  # Formatted time string
    hour: int  # Hours from T=0
    velocity: float
    active_sharers: int = 0
    cumulative_reach: int = 0


class ContagionResult(BaseModel):
    """Final result of a contagion simulation run."""
    
    simulation_id: UUID
    scenario_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_hours: int
    
    # Key metrics
    peak_velocity: float
    time_to_critical: Optional[float] = None  # Hours until VoC > 80
    final_reach_percentage: float  # % of population exposed
    
    # Time series
    velocity_trajectory: list[VelocityDataPoint] = Field(default_factory=list)
    
    # Agent summary
    total_shares: int = 0
    total_comments: int = 0
    total_reports: int = 0
    
    # Classification result
    is_coordinated_attack: bool = False
    attack_confidence: float = 0.0


# =============================================================================
# AI Analysis Models
# =============================================================================

class SignalCluster(BaseModel):
    """A cluster of related signals detected by the system."""
    
    cluster_id: UUID
    signals: list[UUID]  # signal_ids in this cluster
    primary_category: SignalCategory
    detected_severity: SeverityLevel
    confidence_score: float = Field(ge=0, le=1.0)
    
    # AI analysis
    ai_summary: str
    key_themes: list[str] = Field(default_factory=list)
    detected_misinformation: bool = False
    supporting_facts: list[str] = Field(default_factory=list)  # From knowledge base


class CausalAttribution(BaseModel):
    """Root cause analysis result."""
    
    cluster_id: UUID
    
    # Probability distribution over causes
    cause_probabilities: dict[str, float]  # e.g., {"Coordinated Attack": 0.8, "Genuine Concern": 0.15}
    primary_cause: str
    
    # Reasoning
    reasoning_chain: str
    adversarial_critique: str
    final_confidence: float = Field(ge=0, le=1.0)
    
    # Data gaps
    missing_evidence: list[str] = Field(default_factory=list)


class ResponseRecommendation(BaseModel):
    """AI-generated response strategy."""
    
    recommendation_id: UUID
    cluster_id: UUID
    
    # Recommended action
    action_summary: str
    detailed_steps: list[str] = Field(default_factory=list)
    
    # Justification
    reasoning: str
    expected_impact: str
    
    # Confidence & uncertainty
    confidence_score: float = Field(ge=0, le=1.0)
    uncertainty_factors: list[str] = Field(default_factory=list)
    
    # Governance
    requires_human_approval: bool = True
    socratic_questions: list[str] = Field(default_factory=list)


# =============================================================================
# Governance Models
# =============================================================================

class DetectedIncident(BaseModel):
    """A detected incident with governance tracking."""
    
    incident_id: UUID
    related_scenario_id: UUID
    detected_severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.PENDING_REVIEW
    confidence_score: float = Field(ge=0, le=1.0)
    
    # AI analysis
    ai_analysis: str
    proposed_response: str
    
    # Human decision
    human_action: HumanAction = HumanAction.PENDING_REVIEW
    human_notes: str = ""


class AuditLogEntry(BaseModel):
    """Immutable audit log entry for compliance."""
    
    timestamp: datetime
    action_type: str  # e.g., "PREDICTION", "APPROVAL", "REJECTION"
    actor: str  # "AI" or user ID
    target_id: UUID
    details: dict = Field(default_factory=dict)
    confidence_at_time: Optional[float] = None


# =============================================================================
# Executive Briefing Models
# =============================================================================

class ExecutiveBriefing(BaseModel):
    """C-suite ready briefing document."""
    
    briefing_id: UUID
    generated_at: datetime
    scenario_name: str
    
    # Summary section
    situation_summary: str
    current_velocity: float
    risk_level: SeverityLevel
    
    # Prediction section
    predicted_trajectory: str
    time_to_critical: Optional[float] = None
    affected_segments: list[str] = Field(default_factory=list)
    
    # Recommendation
    recommended_action: str
    action_reasoning: str
    confidence_score: float
    
    # Uncertainty
    data_gaps: list[str] = Field(default_factory=list)
    alternative_interpretations: list[str] = Field(default_factory=list)
    
    # Governance trail
    ai_validated: bool = False
    human_approved: bool = False
    approver_id: Optional[str] = None


# =============================================================================
# API Request/Response Models
# =============================================================================

class SimulationStartRequest(BaseModel):
    """Request to start a new simulation."""
    
    scenario_id: UUID
    duration_hours: int = 24
    speed_multiplier: float = 1.0  # 1x, 2x, 4x


class SimulationStatusResponse(BaseModel):
    """Real-time simulation status update."""
    
    simulation_id: UUID
    status: str  # "running", "paused", "completed"
    current_hour: int
    
    # Metrics
    velocity: float
    confidence: float
    alerts: int
    
    # Latest data point for chart
    latest_point: VelocityDataPoint
    
    # AI insight (if available)
    current_insight: Optional[str] = None


class GovernanceDecisionRequest(BaseModel):
    """Request to approve/reject an AI recommendation."""
    
    incident_id: UUID
    decision: HumanAction
    notes: str = ""
    reviewer_id: str = "unknown"
