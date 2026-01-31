"""
LangGraph State Definition.

Defines the state object that flows through the workflow graph.
"""

from typing import Any, Optional, TypedDict
from uuid import UUID

from pydantic import BaseModel


class SimulationState(TypedDict, total=False):
    """
    State object for the simulation workflow.
    
    This state flows through each node in the LangGraph workflow,
    accumulating results from each processing stage.
    """
    
    # Input parameters
    scenario_id: Optional[UUID]
    scenario_name: Optional[str]
    signal_limit: int
    use_llm: bool
    
    # Loaded data
    scenario: Optional[dict]
    signals: list[dict]
    agents: list[dict]
    
    # Detection results
    clusters: list[dict]
    velocity_data: list[dict]
    anomalies_detected: bool
    
    # Causal analysis results
    causal_attributions: list[dict]
    root_causes: list[str]
    confidence_scores: dict[str, float]
    
    # Simulation results
    simulation_complete: bool
    voc_score: float
    predicted_peak_hour: float
    total_reach: int
    simulation_steps: list[dict]
    
    # Adversarial review results
    critique_passed: bool
    critique_issues: list[str]
    adjusted_confidence: float
    
    # Briefing results
    briefing: Optional[dict]
    recommended_actions: list[str]
    
    # Governance results
    governance_passed: bool
    governance_violations: list[str]
    requires_human_review: bool
    socratic_questions: list[str]
    
    # Processing metadata
    processing_errors: list[str]
    current_stage: str
    elapsed_time_seconds: float


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""
    
    scenario_name: Optional[str] = None
    scenario_id: Optional[UUID] = None
    signal_limit: int = 100
    use_llm: bool = True
    run_simulation: bool = True
    generate_briefing: bool = True
    
    class Config:
        arbitrary_types_allowed = True


def create_initial_state(config: WorkflowConfig) -> SimulationState:
    """
    Create initial state from configuration.
    
    Args:
        config: Workflow configuration
    
    Returns:
        Initial SimulationState
    """
    return SimulationState(
        scenario_id=config.scenario_id,
        scenario_name=config.scenario_name,
        signal_limit=config.signal_limit,
        use_llm=config.use_llm,
        
        # Initialize empty collections
        signals=[],
        agents=[],
        clusters=[],
        velocity_data=[],
        causal_attributions=[],
        root_causes=[],
        confidence_scores={},
        simulation_steps=[],
        critique_issues=[],
        recommended_actions=[],
        governance_violations=[],
        socratic_questions=[],
        processing_errors=[],
        
        # Initialize flags
        anomalies_detected=False,
        simulation_complete=False,
        critique_passed=True,
        governance_passed=True,
        requires_human_review=False,
        
        # Initialize metrics
        voc_score=0.0,
        predicted_peak_hour=0.0,
        total_reach=0,
        adjusted_confidence=0.0,
        elapsed_time_seconds=0.0,
        current_stage="initialized",
    )
