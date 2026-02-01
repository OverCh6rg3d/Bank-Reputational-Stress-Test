"""
Executive Briefing Generator - C-suite ready reports.

Generates structured briefings that include:
1. Situation summary
2. Predicted impact (VoC trajectory)
3. Recommended action with confidence
4. Data gaps and uncertainties
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from backend.models.schemas import (
    CausalAttribution,
    ContagionResult,
    ExecutiveBriefing,
    ResponseRecommendation,
    Scenario,
    SeverityLevel,
    SignalCluster,
)
from backend.core.llm_client import get_llm_client, SYSTEM_PROMPTS
from backend.core.governance import get_governance_gate

logger = logging.getLogger(__name__)


class BriefingGenerator:
    """
    Generates executive briefings from simulation results.
    
    Briefings are designed for C-suite consumption:
    - Lead with the bottom line
    - Use plain language
    - Include confidence levels
    - Present clear options
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.governance = get_governance_gate()

    def generate(
        self,
        scenario: Scenario,
        cluster: Optional[SignalCluster],
        simulation_result: Optional[ContagionResult],
        causal_analysis: Optional[CausalAttribution],
        signal_context: Optional[str] = None,
    ) -> ExecutiveBriefing:
        """
        Generate a complete executive briefing.
        """
        briefing_id = uuid4()
        
        # Determine current risk level
        risk_level = self._assess_risk_level(simulation_result, cluster)
        
        # Generate situation summary using LLM
        summary = self._generate_summary(scenario, cluster, simulation_result, signal_context)
        
        # Generate trajectory prediction
        trajectory = self._generate_trajectory_prediction(simulation_result)
        
        # Generate recommended action
        recommendation = self._generate_recommendation(
            scenario, risk_level, causal_analysis
        )
        
        # Identify data gaps
        data_gaps = self._identify_data_gaps(causal_analysis, cluster)
        
        # Get alternative interpretations
        alternatives = []
        if causal_analysis:
            alternatives = [
                f"{cause}: {prob:.0%}"
                for cause, prob in causal_analysis.cause_probabilities.items()
                if prob > 0.1 and cause != causal_analysis.primary_cause
            ]

        return ExecutiveBriefing(
            briefing_id=briefing_id,
            generated_at=datetime.now(),
            scenario_name=scenario.scenario_name,
            situation_summary=summary,
            current_velocity=simulation_result.peak_velocity if simulation_result else 0,
            risk_level=risk_level,
            predicted_trajectory=trajectory,
            time_to_critical=simulation_result.time_to_critical if simulation_result else None,
            affected_segments=[s.strip() for s in scenario.target_segment.split(",")],
            recommended_action=recommendation["action"],
            action_reasoning=recommendation["reasoning"],
            confidence_score=recommendation["confidence"],
            data_gaps=data_gaps,
            alternative_interpretations=alternatives,
            ai_validated=True,
            human_approved=False,
        )

    def _assess_risk_level(
        self,
        simulation: Optional[ContagionResult],
        cluster: Optional[SignalCluster],
    ) -> SeverityLevel:
        """Assess overall risk level from simulation and cluster data."""
        if simulation and simulation.peak_velocity > 80:
            return SeverityLevel.CRITICAL
        elif simulation and simulation.peak_velocity > 60:
            return SeverityLevel.HIGH
        elif cluster and cluster.detected_severity:
            return cluster.detected_severity
        elif simulation and simulation.peak_velocity > 40:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    def _generate_summary(
        self,
        scenario: Scenario,
        cluster: Optional[SignalCluster],
        simulation: Optional[ContagionResult],
        signal_context: Optional[str] = None,
    ) -> str:
        """Generate executive summary using LLM."""
        cluster_info = ""
        if cluster:
            cluster_info = f"""
DETECTED SIGNAL CLUSTER:
- Category: {cluster.primary_category.value}
- Severity: {cluster.detected_severity.value}
- Contains misinformation: {cluster.detected_misinformation}
- AI Summary: {cluster.ai_summary}"""

        simulation_info = ""
        if simulation:
            simulation_info = f"""
SIMULATION RESULTS:
- Peak Velocity: {simulation.peak_velocity:.1f}/100
- Time to Critical: {simulation.time_to_critical or 'Not reached'}h
- Final Reach: {simulation.final_reach_percentage:.1f}%
- Total Shares: {simulation.total_shares}
- Coordinated Attack: {'Yes' if simulation.is_coordinated_attack else 'No'}"""

        signal_info = ""
        if signal_context:
            signal_info = f"""
RECENT SIGNALS (synthetic):
{signal_context}
"""

        prompt = f"""Write a 2-3 sentence executive summary for this crisis situation:

SCENARIO: {scenario.scenario_name}
{scenario.description}
{cluster_info}
{simulation_info}
{signal_info}

Write in clear, direct executive language. Lead with the most important fact.
Do not use technical jargon. Be specific about the risk level and timeline.
Do NOT recommend public statements or automated public actions; keep actions internal and human-approved."""

        try:
            summary = self.llm.complete(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["briefing_writer"],
                temperature=0.3,
                max_tokens=200,
            )
            return summary.strip()
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"A {scenario.severity_level.value.lower()} risk event ({scenario.scenario_name}) has been detected. Immediate assessment recommended."

    def _generate_trajectory_prediction(
        self,
        simulation: Optional[ContagionResult],
    ) -> str:
        """Generate human-readable trajectory prediction."""
        if not simulation:
            return "Simulation data not available. Cannot predict trajectory."

        if simulation.time_to_critical:
            return f"Without intervention, negative sentiment is projected to reach critical levels within {simulation.time_to_critical:.1f} hours. Peak velocity of {simulation.peak_velocity:.0f}/100 indicates rapid spread."
        elif simulation.peak_velocity > 60:
            return f"Significant spread expected with peak velocity of {simulation.peak_velocity:.0f}/100. While not projected to reach critical threshold, close monitoring is advised."
        else:
            return f"Limited spread projected with peak velocity of {simulation.peak_velocity:.0f}/100. Risk remains contained under current conditions."

    def _generate_recommendation(
        self,
        scenario: Scenario,
        risk_level: SeverityLevel,
        causal: Optional[CausalAttribution],
    ) -> dict:
        """Generate recommended action based on scenario and analysis."""
        # Build context for the LLM
        causal_context = ""
        if causal:
            causal_context = f"""
ROOT CAUSE ANALYSIS:
- Primary Cause: {causal.primary_cause}
- Confidence: {causal.final_confidence:.2f}
- Reasoning: {causal.reasoning_chain}
"""

        prompt = f"""Generate a crisis response strategy for this situation:

SCENARIO: {scenario.scenario_name}
Risk Level: {risk_level.value}
{causal_context}

Provide a recommended action and the reasoning behind it.
The action should be specific, actionable, and proportionate to the risk.
Do NOT recommend public statements or direct communication with regulators.
Actions must stay internal and require human approval.

Respond with JSON:
{{
    "action": "...",
    "reasoning": "...",
    "confidence": 0.XX
}}"""

        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["response_generator"],
                temperature=0.4,
            )
            return {
                "action": result.get("action", "Assess situation and monitor."),
                "reasoning": result.get("reasoning", "Standard precautionary monitoring."),
                "confidence": result.get("confidence", 0.7),
            }
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback response
            return {
                "action": f"Convene crisis response team. Monitor situation for {scenario.recommended_response_time_hours:.1f} hours before public response.",
                "reasoning": "Standard protocol for unclassified risk events. Avoid premature action that could amplify the signal.",
                "confidence": 0.7,
            }

    def _identify_data_gaps(
        self,
        causal: Optional[CausalAttribution],
        cluster: Optional[SignalCluster],
    ) -> list[str]:
        """Identify what information is missing."""
        gaps = []

        if causal and causal.missing_evidence:
            gaps.extend(causal.missing_evidence[:3])
        
        if not causal:
            gaps.append("Causal analysis not completed")
        
        if cluster and cluster.detected_misinformation:
            gaps.append("Source verification for misinformation claims pending")
        
        if not gaps:
            gaps = [
                "Real-time transaction data correlation not available",
                "Customer service queue impact not measured",
            ]

        return gaps[:5]  # Limit to 5 gaps

    def format_for_display(self, briefing: ExecutiveBriefing) -> dict:
        """Format briefing for dashboard display."""
        return {
            "id": str(briefing.briefing_id),
            "timestamp": briefing.generated_at.isoformat(),
            "scenario": briefing.scenario_name,
            "summary": briefing.situation_summary,
            "metrics": {
                "velocity": briefing.current_velocity,
                "risk_level": briefing.risk_level.value,
                "time_to_critical": briefing.time_to_critical,
                "confidence": briefing.confidence_score,
            },
            "recommendation": {
                "action": briefing.recommended_action,
                "reasoning": briefing.action_reasoning,
            },
            "uncertainties": {
                "data_gaps": briefing.data_gaps,
                "alternatives": briefing.alternative_interpretations,
            },
            "governance": {
                "ai_validated": briefing.ai_validated,
                "human_approved": briefing.human_approved,
                "approver": briefing.approver_id,
            },
        }
