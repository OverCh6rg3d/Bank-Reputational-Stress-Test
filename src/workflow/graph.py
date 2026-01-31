"""
LangGraph Workflow Graph.

Defines the StateGraph with nodes and edges for the simulation workflow.
"""

import sys
from pathlib import Path
from typing import Any, Literal, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import END, StateGraph

from .state import SimulationState, WorkflowConfig, create_initial_state
from .nodes import (
    load_data_node,
    detect_signals_node,
    analyze_clusters_node,
    run_simulation_node,
    adversarial_review_node,
    generate_briefing_node,
    governance_check_node,
)


def should_run_simulation(state: SimulationState) -> Literal["simulate", "skip_simulation"]:
    """
    Conditional edge: decide whether to run simulation.
    
    Skip if no clusters detected or anomalies_detected is False.
    """
    clusters = state.get("clusters", [])
    anomalies = state.get("anomalies_detected", False)
    
    if clusters and anomalies:
        return "simulate"
    return "skip_simulation"


def should_generate_briefing(state: SimulationState) -> Literal["brief", "skip_briefing"]:
    """
    Conditional edge: decide whether to generate briefing.
    
    Skip if no meaningful results to report.
    """
    has_clusters = len(state.get("clusters", [])) > 0
    has_simulation = state.get("simulation_complete", False)
    
    if has_clusters or has_simulation:
        return "brief"
    return "skip_briefing"


def has_critical_errors(state: SimulationState) -> Literal["continue", "abort"]:
    """
    Conditional edge: check for critical errors.
    
    Abort if too many errors accumulated.
    """
    errors = state.get("processing_errors", [])
    
    if len(errors) > 3:
        return "abort"
    return "continue"


def create_workflow() -> StateGraph:
    """
    Create the simulation workflow StateGraph.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with SimulationState
    workflow = StateGraph(SimulationState)
    
    # Add nodes
    workflow.add_node("load_data", load_data_node)
    workflow.add_node("detect_signals", detect_signals_node)
    workflow.add_node("analyze_clusters", analyze_clusters_node)
    workflow.add_node("run_simulation", run_simulation_node)
    workflow.add_node("adversarial_review", adversarial_review_node)
    workflow.add_node("generate_briefing", generate_briefing_node)
    workflow.add_node("governance_check", governance_check_node)
    
    # Set entry point
    workflow.set_entry_point("load_data")
    
    # Add edges (linear flow with conditionals)
    workflow.add_edge("load_data", "detect_signals")
    workflow.add_edge("detect_signals", "analyze_clusters")
    
    # Conditional: run simulation or skip
    workflow.add_conditional_edges(
        "analyze_clusters",
        should_run_simulation,
        {
            "simulate": "run_simulation",
            "skip_simulation": "adversarial_review",
        }
    )
    
    workflow.add_edge("run_simulation", "adversarial_review")
    
    # Conditional: generate briefing or skip
    workflow.add_conditional_edges(
        "adversarial_review",
        should_generate_briefing,
        {
            "brief": "generate_briefing",
            "skip_briefing": "governance_check",
        }
    )
    
    workflow.add_edge("generate_briefing", "governance_check")
    workflow.add_edge("governance_check", END)
    
    return workflow.compile()


async def run_workflow(
    scenario_name: Optional[str] = None,
    scenario_id: Optional[str] = None,
    signal_limit: int = 100,
    use_llm: bool = False,
) -> SimulationState:
    """
    Run the complete simulation workflow.
    
    Args:
        scenario_name: Name of scenario to analyze
        scenario_id: ID of scenario to analyze
        signal_limit: Max signals to process
        use_llm: Whether to use LLM for agent decisions
    
    Returns:
        Final SimulationState with all results
    """
    from uuid import UUID
    
    # Create config
    config = WorkflowConfig(
        scenario_name=scenario_name,
        scenario_id=UUID(scenario_id) if scenario_id else None,
        signal_limit=signal_limit,
        use_llm=use_llm,
    )
    
    # Create initial state
    initial_state = create_initial_state(config)
    
    # Create and run workflow
    app = create_workflow()
    final_state = await app.ainvoke(initial_state)
    
    return final_state


def get_workflow_summary(state: SimulationState) -> dict[str, Any]:
    """
    Extract a summary from the final workflow state.
    
    Args:
        state: Final SimulationState
    
    Returns:
        Summary dict suitable for API response
    """
    return {
        "status": "complete" if state.get("current_stage") == "governance_complete" else "partial",
        "current_stage": state.get("current_stage", "unknown"),
        "clusters_detected": len(state.get("clusters", [])),
        "simulation_complete": state.get("simulation_complete", False),
        "voc_score": state.get("voc_score", 0),
        "total_reach": state.get("total_reach", 0),
        "requires_human_review": state.get("requires_human_review", False),
        "socratic_questions": state.get("socratic_questions", []),
        "errors": state.get("processing_errors", []),
        "elapsed_seconds": state.get("elapsed_time_seconds", 0),
    }
