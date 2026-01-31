"""
Agent Brain - LLM-powered decision making for synthetic customer agents.

Each agent has a persona (archetype) that influences their behavior.
This module simulates how an agent would react to a social signal.
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from backend.models.schemas import (
    AgentAction,
    AgentArchetype,
    SocialSignal,
)
from backend.core.llm_client import get_llm_client, SYSTEM_PROMPTS

logger = logging.getLogger(__name__)


class AgentDecision(BaseModel):
    """The result of an agent's decision-making process."""
    
    agent_id: UUID
    signal_id: UUID
    action: AgentAction
    reasoning: str
    emotional_state: str
    share_probability: float  # 0-1
    reach_multiplier: float  # How many followers get exposed


class AgentBrain:
    """
    LLM-powered decision engine for synthetic agents.
    
    Uses the agent's archetype (personality, values, skepticism) to determine
    how they would react to a signal about the bank.
    """

    def __init__(self, use_llm: bool = True, parallel_limit: int = 10):
        """
        Args:
            use_llm: If True, use LLM for decisions. If False, use heuristics (faster).
            parallel_limit: Max concurrent LLM calls for async processing.
        """
        self.use_llm = use_llm
        self.parallel_limit = parallel_limit
        self.llm = get_llm_client() if use_llm else None

    def decide(
        self, agent: AgentArchetype, signal: SocialSignal, current_stats: Optional[dict] = None
    ) -> AgentDecision:
        """
        Synchronous decision-making for a single agent.
        Uses LLM to roleplay as the agent and decide their action.
        """
        if not self.use_llm:
            return self._heuristic_decision(agent, signal)

        prompt = self._build_decision_prompt(agent, signal, current_stats)
        
        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["agent_simulator"],
                temperature=0.7,  # Some randomness for realistic variance
            )
            
            return AgentDecision(
                agent_id=agent.agent_id,
                signal_id=signal.signal_id,
                action=AgentAction(result.get("action", "IGNORE")),
                reasoning=result.get("reasoning", ""),
                emotional_state=result.get("emotional_state", "Neutral"),
                share_probability=float(result.get("share_probability", 0.0)),
                reach_multiplier=self._calculate_reach(agent),
            )
        except Exception as e:
            logger.error(f"LLM decision failed for agent {agent.agent_id}: {e}")
            return self._heuristic_decision(agent, signal)

    async def async_decide(
        self, agent: AgentArchetype, signal: SocialSignal, current_stats: Optional[dict] = None
    ) -> AgentDecision:
        """
        Async decision-making for parallel agent processing.
        """
        if not self.use_llm:
            return self._heuristic_decision(agent, signal)

        prompt = self._build_decision_prompt(agent, signal, current_stats)

        try:
            result = await self.llm.async_complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["agent_simulator"],
                temperature=0.7,
            )

            return AgentDecision(
                agent_id=agent.agent_id,
                signal_id=signal.signal_id,
                action=AgentAction(result.get("action", "IGNORE")),
                reasoning=result.get("reasoning", ""),
                emotional_state=result.get("emotional_state", "Neutral"),
                share_probability=float(result.get("share_probability", 0.0)),
                reach_multiplier=self._calculate_reach(agent),
            )
        except Exception as e:
            logger.error(f"Async LLM decision failed: {e}")
            return self._heuristic_decision(agent, signal)

    async def batch_decide(
        self, agents: list[AgentArchetype], signal: SocialSignal, current_stats: Optional[dict] = None
    ) -> list[AgentDecision]:
        """
        Process multiple agents in parallel with rate limiting.
        """
        semaphore = asyncio.Semaphore(self.parallel_limit)

        async def limited_decide(agent: AgentArchetype) -> AgentDecision:
            async with semaphore:
                return await self.async_decide(agent, signal, current_stats)

        decisions = await asyncio.gather(
            *[limited_decide(agent) for agent in agents]
        )
        return list(decisions)

    def _build_decision_prompt(
        self, agent: AgentArchetype, signal: SocialSignal, current_stats: Optional[dict] = None
    ) -> str:
        """Build the prompt for LLM decision-making."""
        social_context = ""
        if current_stats:
            shares = current_stats.get("total_shares", 0)
            comments = current_stats.get("total_comments", 0)
            social_context = f"""
SOCIAL CONTEXT (What others are doing):
- Total Shares so far: {shares}
- Total Comments: {comments}
- Trending Status: {"Viral" if shares > 50 else "Quiet"}
"""

        return f"""You are roleplaying as this person:

NAME: {agent.archetype_name}
DEMOGRAPHIC: {agent.demographic_segment}
BACKGROUND: {agent.persona_description}

KEY PERSONALITY TRAITS:
- Financial Literacy: {agent.financial_literacy}/10 (higher = understands banking better)
- Brand Loyalty: {agent.brand_loyalty}/100 (higher = more likely to defend Mashreq)
- Skepticism: {agent.skepticism_score}/10 (higher = needs more proof before believing/sharing)
- Network Influence: {agent.network_influence}/100 (how many followers you have)
- Core Values: {', '.join(agent.core_values)}
- Typical Behavior: {agent.behavioral_pattern}

---

You just saw this post about Mashreq Bank on {signal.platform_source.value}:

"{signal.content_text}"
{social_context}
Based on your persona's personality and values, decide how you would react:

Available actions:
- IGNORE: Just scroll past, not interested or not convinced
- LIKE: Show agreement without amplifying
- SHARE: Repost to your followers (amplifies reach!)
- COMMENT: Add your thoughts (could defend or attack)
- REPORT: Flag as spam/misinformation

Respond with JSON:
{{
    "action": "IGNORE|LIKE|SHARE|COMMENT|REPORT",
    "reasoning": "Why you chose this action, from your persona's perspective",
    "emotional_state": "Fear|Anger|Curiosity|Relief|Neutral|Trust",
    "share_probability": 0.0-1.0 (even if you didn't share, what was the temptation?)
}}"""

    def _heuristic_decision(
        self, agent: AgentArchetype, signal: SocialSignal
    ) -> AgentDecision:
        """
        Fast heuristic-based decision when LLM is disabled.
        Uses agent traits and signal properties to calculate probabilities.
        """
        import random

        # Base share probability from signal virality
        base_share = signal.gt_virality_potential / 100

        # Adjust by agent traits
        share_prob = base_share

        # High skepticism reduces sharing
        share_prob *= (10 - agent.skepticism_score) / 10

        # Low financial literacy increases sharing of scam content
        if signal.gt_category.value == "Fraud_Rumor":
            illiteracy_bonus = (10 - agent.financial_literacy) / 20
            share_prob += illiteracy_bonus

        # High brand loyalty reduces sharing of negative content
        if signal.gt_sentiment < 0:
            loyalty_reduction = agent.brand_loyalty / 200
            share_prob -= loyalty_reduction

        # Clamp to 0-1
        share_prob = max(0.0, min(1.0, share_prob))

        # Decide action based on probability
        roll = random.random()
        if roll < share_prob * 0.7:  # Sharing is rarer
            action = AgentAction.SHARE
        elif roll < share_prob:
            action = AgentAction.COMMENT
        elif roll < share_prob + 0.1:
            action = AgentAction.LIKE
        elif agent.skepticism_score > 7 and signal.gt_is_misinformation:
            action = AgentAction.REPORT
        else:
            action = AgentAction.IGNORE

        # Determine emotional state
        if signal.gt_sentiment < -0.5:
            emotional_state = "Fear" if agent.financial_literacy < 5 else "Concern"
        elif signal.gt_sentiment > 0.5:
            emotional_state = "Trust"
        else:
            emotional_state = "Neutral"

        return AgentDecision(
            agent_id=agent.agent_id,
            signal_id=signal.signal_id,
            action=action,
            reasoning=f"Heuristic: share_prob={share_prob:.2f}, skepticism={agent.skepticism_score}",
            emotional_state=emotional_state,
            share_probability=share_prob,
            reach_multiplier=self._calculate_reach(agent),
        )

    def _calculate_reach(self, agent: AgentArchetype) -> float:
        """Calculate how many people this agent can reach."""
        # Network influence maps to follower count (log scale)
        # influence 1 = ~10 followers, influence 100 = ~10000 followers
        base_reach = 10 * (1.05 ** agent.network_influence)
        
        # Activity frequency affects actual exposure
        activity_multiplier = min(1.0, agent.activity_frequency / 5)
        
        return base_reach * activity_multiplier
