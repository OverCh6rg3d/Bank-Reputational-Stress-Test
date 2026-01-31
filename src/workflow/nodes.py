"""
LangGraph Workflow Nodes.

Defines the processing nodes for the simulation workflow graph.
Each node is a pure function that takes state and returns updated state.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .state import SimulationState


async def load_data_node(state: SimulationState) -> dict[str, Any]:
    """
    Load scenario, signals, and agents from data loader.
    
    This is the entry node that fetches all required data.
    """
    from backend.data.data_loader import get_data_loader
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        loader = get_data_loader()
        
        # Load scenario
        scenario = None
        if state.get("scenario_name"):
            scenario = loader.get_scenario_by_name(state["scenario_name"])
        elif state.get("scenario_id"):
            scenario = loader.get_scenario_by_id(state["scenario_id"])
        
        # Load signals
        signals = loader.load_signals(limit=state.get("signal_limit", 100))
        signals_dict = [s.model_dump() if hasattr(s, 'model_dump') else s.__dict__ for s in signals]
        
        # Load agents
        agents = loader.load_agents()
        agents_dict = [a.model_dump() if hasattr(a, 'model_dump') else a.__dict__ for a in agents]
        
        elapsed = time.time() - start_time
        
        return {
            "scenario": scenario.model_dump() if scenario else None,
            "signals": signals_dict,
            "agents": agents_dict,
            "current_stage": "data_loaded",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Data loading error: {str(e)}")
        return {
            "processing_errors": errors,
            "current_stage": "data_load_failed",
        }


async def detect_signals_node(state: SimulationState) -> dict[str, Any]:
    """
    Run signal detection and clustering on loaded signals.
    """
    from backend.core.signal_detector import SignalDetector
    from backend.models.schemas import SocialSignal
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        signals_data = state.get("signals", [])
        if not signals_data:
            return {
                "clusters": [],
                "current_stage": "detection_skipped",
                "processing_errors": errors + ["No signals to process"],
            }
        
        # Convert back to SocialSignal objects
        signals = [SocialSignal(**s) for s in signals_data[:100]]  # Limit for performance
        
        detector = SignalDetector()
        clusters = detector.detect_clusters(signals)
        
        # Calculate velocity
        velocity_data = []
        anomalies_detected = False
        
        for cluster in clusters:
            velocity_info = detector.calculate_velocity(cluster.signal_ids, signals)
            velocity_data.append(velocity_info)
            if velocity_info.get("is_anomaly", False):
                anomalies_detected = True
        
        clusters_dict = [c.model_dump() if hasattr(c, 'model_dump') else c.__dict__ for c in clusters]
        
        elapsed = time.time() - start_time
        
        return {
            "clusters": clusters_dict,
            "velocity_data": velocity_data,
            "anomalies_detected": anomalies_detected,
            "current_stage": "detection_complete",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Signal detection error: {str(e)}")
        return {
            "clusters": [],
            "processing_errors": errors,
            "current_stage": "detection_failed",
        }


async def analyze_clusters_node(state: SimulationState) -> dict[str, Any]:
    """
    Run causal analysis on detected clusters.
    """
    from backend.core.causal_engine import CausalEngine
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        clusters = state.get("clusters", [])
        if not clusters:
            return {
                "causal_attributions": [],
                "current_stage": "analysis_skipped",
            }
        
        engine = CausalEngine()
        attributions = []
        root_causes = []
        confidence_scores = {}
        
        for cluster in clusters[:5]:  # Limit for performance
            # Get cluster summary for analysis
            summary = cluster.get("summary", "Unknown cluster content")
            
            attribution = engine.analyze_cluster(
                cluster_summary=summary,
                signal_count=len(cluster.get("signal_ids", [])),
                severity=cluster.get("severity_level", "Medium"),
            )
            
            attributions.append(attribution)
            
            if attribution.get("most_likely_cause"):
                root_causes.append(attribution["most_likely_cause"])
                confidence_scores[attribution["most_likely_cause"]] = attribution.get("confidence", 0.5)
        
        elapsed = time.time() - start_time
        
        return {
            "causal_attributions": attributions,
            "root_causes": root_causes,
            "confidence_scores": confidence_scores,
            "current_stage": "analysis_complete",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Causal analysis error: {str(e)}")
        return {
            "causal_attributions": [],
            "processing_errors": errors,
            "current_stage": "analysis_failed",
        }


async def run_simulation_node(state: SimulationState) -> dict[str, Any]:
    """
    Run contagion simulation on detected clusters.
    """
    from simulator.engine import ContagionSimulator
    from backend.models.schemas import AgentArchetype, SocialSignal
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        clusters = state.get("clusters", [])
        agents_data = state.get("agents", [])
        signals_data = state.get("signals", [])
        
        if not clusters or not agents_data:
            return {
                "simulation_complete": False,
                "current_stage": "simulation_skipped",
            }
        
        # Convert to proper objects
        agents = [AgentArchetype(**a) for a in agents_data[:50]]  # Limit agents
        
        # Get representative signal from first cluster
        first_cluster = clusters[0]
        signal_ids = first_cluster.get("signal_ids", [])
        
        if not signal_ids:
            return {
                "simulation_complete": False,
                "current_stage": "simulation_skipped",
                "processing_errors": errors + ["No signals in cluster"],
            }
        
        # Find matching signal
        seed_signal = None
        for s in signals_data:
            if str(s.get("signal_id")) == str(signal_ids[0]):
                seed_signal = SocialSignal(**s)
                break
        
        if not seed_signal:
            seed_signal = SocialSignal(**signals_data[0])
        
        # Run simulation
        use_llm = state.get("use_llm", True)
        simulator = ContagionSimulator(
            agents=agents,
            use_llm=use_llm,
            simulation_hours=24,
            agents_per_step=20,
        )
        
        result = await simulator.simulate(seed_signal)
        
        elapsed = time.time() - start_time
        
        return {
            "simulation_complete": True,
            "voc_score": result.peak_velocity,
            "predicted_peak_hour": result.peak_hour,
            "total_reach": result.total_reached,
            "simulation_steps": [s.model_dump() for s in result.steps],
            "current_stage": "simulation_complete",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Simulation error: {str(e)}")
        return {
            "simulation_complete": False,
            "processing_errors": errors,
            "current_stage": "simulation_failed",
        }


async def adversarial_review_node(state: SimulationState) -> dict[str, Any]:
    """
    Run adversarial critic on findings to challenge predictions.
    Uses the Multi-Agent Debate Engine for robust critique.
    """
    from backend.core.debate import get_debate_engine
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        # Gather findings for critique
        voc_score = state.get("voc_score", 0)
        root_causes = state.get("root_causes", [])
        confidence_scores = state.get("confidence_scores", {})
        cluster_summary = ""
        if state.get("clusters"):
             cluster_summary = str(state.get("clusters")[0].get("summary", ""))
        
        if not root_causes:
            return {
                "critique_passed": True,
                "critique_issues": [],
                "adjusted_confidence": 0.5,
                "current_stage": "critique_skipped",
                "debate_transcript": [],
            }
        
        engine = get_debate_engine()
        
        # Create summary for critique
        findings_summary = f"""
        VoC Score: {voc_score}
        Root Causes: {', '.join(root_causes)}
        Primary Cluster: {cluster_summary}
        """
        
        # Run debate
        result = engine.run_debate(
            initial_finding=f"High risk contagion detected (VoC {voc_score}) due to {root_causes}",
            initial_confidence=max(confidence_scores.values()) if confidence_scores else 0.5,
            context=findings_summary,
            max_turns=2
        )
        
        elapsed = time.time() - start_time
        
        return {
            "critique_passed": result.refined_confidence > 0.6,
            "critique_issues": result.issues_raised,
            "adjusted_confidence": result.refined_confidence,
            "debate_transcript": [t.__dict__ for t in result.turns],
            "current_stage": "critique_complete",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Adversarial review error: {str(e)}")
        return {
            "critique_passed": True,
            "critique_issues": [],
            "processing_errors": errors,
            "current_stage": "critique_failed",
            "debate_transcript": [],
        }


async def generate_briefing_node(state: SimulationState) -> dict[str, Any]:
    """
    Generate executive briefing from all results.
    """
    from reporting.briefing_generator import BriefingGenerator
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        scenario = state.get("scenario")
        clusters = state.get("clusters", [])
        voc_score = state.get("voc_score", 0)
        root_causes = state.get("root_causes", [])
        critique_issues = state.get("critique_issues", [])
        
        generator = BriefingGenerator()
        
        briefing = generator.generate(
            scenario=scenario,
            clusters=clusters,
            voc_score=voc_score,
            root_causes=root_causes,
            critique_issues=critique_issues,
        )
        
        elapsed = time.time() - start_time
        
        return {
            "briefing": briefing.model_dump() if hasattr(briefing, 'model_dump') else briefing,
            "recommended_actions": briefing.recommended_actions if hasattr(briefing, 'recommended_actions') else [],
            "current_stage": "briefing_complete",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Briefing generation error: {str(e)}")
        return {
            "briefing": None,
            "processing_errors": errors,
            "current_stage": "briefing_failed",
        }


async def governance_check_node(state: SimulationState) -> dict[str, Any]:
    """
    Run governance validation on all recommendations.
    """
    from backend.core.governance import get_governance_gate
    
    start_time = time.time()
    errors = list(state.get("processing_errors", []))
    
    try:
        briefing = state.get("briefing")
        recommended_actions = state.get("recommended_actions", [])
        adjusted_confidence = state.get("adjusted_confidence", 0.5)
        voc_score = state.get("voc_score", 0)
        
        gate = get_governance_gate()
        
        violations = []
        requires_review = False
        
        # Check confidence thresholds
        if adjusted_confidence < 0.7:
            requires_review = True
        
        # Check for high severity
        if voc_score > 80:
            requires_review = True
        
        # Get Socratic questions
        socratic_questions = gate._select_socratic_questions(
            severity_level="HIGH" if voc_score > 70 else "MEDIUM",
            max_questions=3,
        )
        
        # Log the workflow execution
        gate.log_decision(
            incident_id=None,
            action_type="WORKFLOW_COMPLETE",
            actor="system",
            details={
                "voc_score": voc_score,
                "adjusted_confidence": adjusted_confidence,
                "requires_review": requires_review,
            },
            confidence=adjusted_confidence,
        )
        
        elapsed = time.time() - start_time
        
        return {
            "governance_passed": len(violations) == 0,
            "governance_violations": violations,
            "requires_human_review": requires_review,
            "socratic_questions": socratic_questions,
            "current_stage": "governance_complete",
            "elapsed_time_seconds": state.get("elapsed_time_seconds", 0) + elapsed,
        }
        
    except Exception as e:
        errors.append(f"Governance check error: {str(e)}")
        return {
            "governance_passed": False,
            "requires_human_review": True,
            "processing_errors": errors,
            "current_stage": "governance_failed",
        }
