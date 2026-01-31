"""
Causal Attribution Engine - Root cause analysis with uncertainty quantification.

Determines WHY a signal cluster matters by analyzing:
1. Probability distribution over possible causes
2. Evidence quality and gaps
3. Adversarial validation of conclusions
"""

import logging
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..models.schemas import (
    CausalAttribution,
    SignalCluster,
    SeverityLevel,
)
from .llm_client import get_llm_client, SYSTEM_PROMPTS

logger = logging.getLogger(__name__)


class CauseDistribution(BaseModel):
    """Probability distribution over possible causes."""
    
    coordinated_attack: float = Field(default=0.0, ge=0, le=1)
    genuine_concern: float = Field(default=0.0, ge=0, le=1)
    service_issue: float = Field(default=0.0, ge=0, le=1)
    misinformation: float = Field(default=0.0, ge=0, le=1)
    random_noise: float = Field(default=0.0, ge=0, le=1)


class CausalEngine:
    """
    Performs root cause analysis on signal clusters.
    
    Uses LLM reasoning + adversarial validation to produce
    high-confidence causal attributions.
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.critic = AdversarialCritic()

    def analyze(
        self,
        cluster: SignalCluster,
        sample_content: list[str],
        supporting_facts: Optional[list[str]] = None,
    ) -> CausalAttribution:
        """
        Perform causal analysis on a signal cluster.
        
        Args:
            cluster: The detected signal cluster
            sample_content: Sample texts from signals in the cluster
            supporting_facts: Relevant facts from knowledge base
        """
        # Step 1: Initial causal analysis
        initial_result = self._initial_analysis(cluster, sample_content)
        
        # Step 2: Adversarial critique
        critique = self.critic.critique(
            prediction=initial_result.get("reasoning", ""),
            evidence=sample_content,
            cause_distribution=initial_result.get("probabilities", {}),
        )
        
        # Step 3: Adjust confidence based on critique
        final_confidence = initial_result.get("confidence", 0.75)
        if critique.get("major_flaws", False):
            final_confidence *= 0.7  # Reduce confidence if flaws found
        
        # Identify primary cause
        probs = initial_result.get("probabilities", {})
        primary_cause = max(probs, key=probs.get) if probs else "Unknown"
        
        # Identify evidence gaps
        gaps = critique.get("missing_evidence", [])
        if not gaps:
            gaps = ["Real-time verification not possible", "Historical pattern matching limited"]

        return CausalAttribution(
            cluster_id=cluster.cluster_id,
            cause_probabilities=probs,
            primary_cause=primary_cause,
            reasoning_chain=initial_result.get("reasoning", ""),
            adversarial_critique=critique.get("critique", ""),
            final_confidence=final_confidence,
            missing_evidence=gaps,
        )

    def _initial_analysis(
        self,
        cluster: SignalCluster,
        sample_content: list[str],
    ) -> dict:
        """Generate initial causal analysis using LLM."""
        
        content_text = "\n".join([f"- {c[:200]}..." for c in sample_content[:5]])
        
        prompt = f"""Analyze this cluster of social signals about Mashreq Bank and determine the root cause.

CLUSTER METADATA:
- Category: {cluster.primary_category.value}
- Severity: {cluster.detected_severity.value}
- Signal count: {len(cluster.signals)}
- Contains misinformation: {cluster.detected_misinformation}

SAMPLE CONTENT:
{content_text}

AI ANALYSIS SUMMARY:
{cluster.ai_summary}

Determine the probability distribution across these possible causes:
1. Coordinated Attack: Bot networks, competitor sabotage, organized FUD campaign
2. Genuine Concern: Real customer experiences, legitimate complaints
3. Service Issue: Actual technical problems or outages
4. Misinformation: False claims spreading organically (not coordinated)
5. Random Noise: Coincidental clustering of unrelated posts

Also explain your reasoning chain and confidence level.

Respond with JSON:
{{
    "probabilities": {{
        "Coordinated Attack": 0.XX,
        "Genuine Concern": 0.XX,
        "Service Issue": 0.XX,
        "Misinformation": 0.XX,
        "Random Noise": 0.XX
    }},
    "reasoning": "Step-by-step explanation of your analysis...",
    "confidence": 0.XX,
    "key_indicators": ["indicator1", "indicator2", ...]
}}"""

        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["causal_analyst"],
                temperature=0.3,
            )
            return result
        except Exception as e:
            logger.error(f"Causal analysis failed: {e}")
            return {
                "probabilities": {"Unknown": 1.0},
                "reasoning": "Analysis failed",
                "confidence": 0.3,
            }


class AdversarialCritic:
    """
    Devil's advocate AI that challenges predictions.
    
    Used to:
    1. Find logical gaps in reasoning
    2. Identify alternative explanations
    3. Spot missing evidence
    4. Reduce overconfidence
    """

    def __init__(self):
        self.llm = get_llm_client()

    def critique(
        self,
        prediction: str,
        evidence: list[str],
        cause_distribution: dict,
    ) -> dict:
        """
        Challenge a causal prediction and identify weaknesses.
        """
        evidence_text = "\n".join([f"- {e[:150]}..." for e in evidence[:3]])
        probs_text = "\n".join([f"- {k}: {v}" for k, v in cause_distribution.items()])

        prompt = f"""You are a devil's advocate. Challenge this risk analysis and find flaws.

PREDICTION:
{prediction}

PROBABILITY DISTRIBUTION:
{probs_text}

EVIDENCE USED:
{evidence_text}

Your job is to:
1. Find logical gaps in the reasoning
2. Suggest alternative explanations that weren't considered
3. Identify evidence that would be needed to confirm/deny the conclusion
4. Rate whether there are major flaws (true/false)

Be thorough but constructive. If the analysis is solid, acknowledge it.

Respond with JSON:
{{
    "critique": "Your critique of the analysis...",
    "alternative_explanations": ["alt1", "alt2", ...],
    "missing_evidence": ["evidence1", "evidence2", ...],
    "major_flaws": true/false,
    "suggested_confidence_adjustment": -0.XX to +0.XX
}}"""

        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["adversarial_critic"],
                temperature=0.5,
            )
            return result
        except Exception as e:
            logger.error(f"Adversarial critique failed: {e}")
            return {
                "critique": "Critique unavailable",
                "alternative_explanations": [],
                "missing_evidence": [],
                "major_flaws": False,
            }
