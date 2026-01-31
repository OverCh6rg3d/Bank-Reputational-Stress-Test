"""
Multi-Agent Debate Framework.

Implements a structured debate process between a Proponent (who proposes findings)
and a Critic (who challenges them). This adversarial process improves 
robustness and reduces hallucinations.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, List
from uuid import UUID, uuid4
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.llm_client import get_llm_client

logger = logging.getLogger(__name__)

@dataclass
class DebateTurn:
    """A single turn in the debate."""
    turn_id: int
    speaker: str  # "Proponent" or "Critic"
    content: str
    confidence: float

@dataclass
class DebateResult:
    """Outcome of the debate."""
    debate_id: UUID
    turns: List[DebateTurn]
    final_consensus: str
    refined_confidence: float
    issues_raised: List[str]
    issues_resolved: List[str]

    def to_dict(self) -> dict:
        return {
            "debate_id": str(self.debate_id),
            "turns": [{"speaker": t.speaker, "content": t.content} for t in self.turns],
            "final_consensus": self.final_consensus,
            "refined_confidence": self.refined_confidence,
            "issues_raised": self.issues_raised,
            "issues_resolved": self.issues_resolved,
        }

class DebateEngine:
    """
    Orchestrates a multi-turn debate between AI agents.
    """
    
    def __init__(self, use_llm: bool = True):
        self.llm = get_llm_client() if use_llm else None
        self.use_llm = use_llm
        
    def run_debate(
        self, 
        initial_finding: str, 
        initial_confidence: float,
        context: str,
        max_turns: int = 3
    ) -> DebateResult:
        """
        Run a debate on a specific finding.
        
        Args:
            initial_finding: The claim/finding to debate
            initial_confidence: Starting confidence score
            context: Background context (signals, scenario)
            max_turns: Maximum round-trips
        
        Returns:
            DebateResult with transcript and refined outcome
        """
        debate_id = uuid4()
        turns = []
        
        logger.info(f"Starting debate {debate_id} on: {initial_finding[:50]}...")
        
        # Turn 0: Proponent presents case
        turns.append(DebateTurn(
            turn_id=0,
            speaker="Proponent",
            content=f"I propose the following finding based on the data: {initial_finding}",
            confidence=initial_confidence
        ))
        
        current_confidence = initial_confidence
        issues_raised = []
        issues_resolved = []
        
        for i in range(1, max_turns * 2 + 1):
            is_critic = (i % 2 != 0)
            speaker = "Critic" if is_critic else "Proponent"
            
            # Get response
            response, conf = self._get_agent_response(
                speaker=speaker,
                history=turns,
                context=context,
                current_finding=initial_finding
            )
            
            turns.append(DebateTurn(
                turn_id=i,
                speaker=speaker,
                content=response,
                confidence=conf
            ))
            
            # Update confidence
            if self.use_llm:
                # Trust the agent's self-assessed confidence
                current_confidence = conf
            else:
                # Heuristic updates for offline mode
                if is_critic:
                    if any(kw in response.lower() for kw in ["disagree", "flaw", "bias", "question", "issue"]):
                        current_confidence = max(0.1, current_confidence - 0.15)
                        issues_raised.append(response[:50] + "...")
                else:
                    if any(kw in response.lower() for kw in ["agree", "corrected", "adjusted", "point"]):
                        # If proponent agrees with critic, reliability might drop? 
                        # This heuristic is tricky, so simplified for offline:
                        current_confidence = min(0.95, current_confidence + 0.1)
                        if issues_raised:
                            issues_resolved.append(issues_raised[-1])
            
            # Check for consensus (stop if confidence is stable high/low or agents agree)
            if i > 1 and "agree" in response.lower():
                break
        
        # Final Judge Turn to synthesize verdict
        judge_verdict, final_conf = self._get_agent_response(
            speaker="Judge",
            history=turns,
            context=context,
            current_finding=initial_finding
        )
        
        turns.append(DebateTurn(
            turn_id=len(turns),
            speaker="Judge",
            content=judge_verdict,
            confidence=final_conf
        ))

        return DebateResult(
            debate_id=debate_id,
            turns=turns,
            final_consensus=judge_verdict,
            refined_confidence=final_conf,
            issues_raised=issues_raised,
            issues_resolved=issues_resolved,
        )

    def _get_agent_response(self, speaker: str, history: List[DebateTurn], context: str, current_finding: str) -> tuple[str, float]:
        """Generate a response for the speaker."""
        if not self.use_llm:
            # Simple mocked responses for testing/offline
            if speaker == "Critic":
                return "I identified a potential bias in the signal selection. Have you considered the source reliability?", 0.6
            else:
                return "Good point. I have adjusted the finding to reflect lower source reliability.", 0.7
        
        try:
            # tailored prompts for each speaker
            if speaker == "Critic":
                system_prompt = """You are the Adversarial Critic. Your role is identify flaws, logical gaps, and missing evidence in risk findings.
                
                Guidelines:
                - Be skeptical but constructive.
                - Focus on specific weaknesses in the reasoning.
                - If the finding implies a high confidence (e.g. >0.8) without strong evidence, challenge it.
                - Keep your response under 3 sentences."""
            elif speaker == "Judge":
                system_prompt = """You are the Debate Judge. Your role is to read the arguments from the Proponent and Critic and issue a final verdict.
                
                Guidelines:
                - Weigh the evidence presented.
                - If the Critic found valid holes, lower the confidence.
                - If the Proponent defended well, maintain confidence.
                - Provide a final synthesized conclusion.
                - Return a confidence score (0.0 to 1.0) reflecting the final certainty."""
            else:
                system_prompt = """You are the Proponent. Your role is to defend the risk finding using available evidence, but admit when the Critic makes a valid point.
                
                Guidelines:
                - Defend your conclusion if the data supports it.
                - If the Critic identifies a real gap, acknowledge it and lower your confidence.
                - Keep your response under 3 sentences."""

            # Build conversation history
            history_text = "\n".join([f"{t.speaker}: {t.content} (Confidence: {t.confidence})" for t in history])
            
            prompt = f"""
            CONTEXT (Signals & Analysis):
            {context}

            CURRENT DEBATE HISTORY:
            {history_text}

            YOUR TURN ({speaker}):
            Respond to the last point.
            
            Also provide your current confidence in the original finding (0.0 to 1.0).
            
            Format as JSON:
            {{
                "response": "...",
                "confidence": 0.X
            }}
            """

            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            return result.get("response", ""), float(result.get("confidence", 0.5))

        except Exception as e:
            logger.error(f"LLM debate failure for {speaker}: {e}")
            # Fallback
            if speaker == "Critic":
                return f"I question the confidence level given the limited data points in: {context[:50]}...", 0.6
            else:
                return "I acknowledge the limitation but the pattern remains significant across multiple signals.", 0.75

# Singleton
_debate_engine: Optional[DebateEngine] = None

def get_debate_engine() -> DebateEngine:
    global _debate_engine
    if _debate_engine is None:
        _debate_engine = DebateEngine(use_llm=True) # Enabled AI by default
    return _debate_engine
