
import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulator.agent_brain import AgentBrain
from backend.models.schemas import AgentArchetype, SocialSignal, PlatformSource, SignalCategory

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_agent_simulation():
    print("\n=== Testing Agent Brain (Real LLM) ===\n")
    
    try:
        brain = AgentBrain(use_llm=True)
    except Exception as e:
        print(f"Skipping test: Could not initialize AgentBrain: {e}")
        return

    # Create a mock agent: "Anxious Saver"
    agent = AgentArchetype(
        agent_id=uuid4(),
        archetype_name="Anxious Saver",
        demographic_segment="Gen X",
        financial_literacy=3,
        brand_loyalty=80,
        skepticism_score=2, # Believes things easily
        network_influence=10,
        activity_frequency=2.0,
        preferred_platform=PlatformSource.X_STYLE,
        core_values=["Security", "Family"],
        persona_description="Worries about losing unexpected money. Trusts official looking news.",
        behavioral_pattern="Shares warnings with family groups instantly."
    )

    # Signal: A scary scam rumor
    signal = SocialSignal(
        signal_id=uuid4(),
        timestamp=datetime.now(),
        platform_source=PlatformSource.X_STYLE,
        content_text="URGENT: Central Bank says Mashreq accounts might be frozen due to audit. Withdraw cash now!",
        thread_id=uuid4(),
        media_type="None",
        gt_category=SignalCategory.FRAUD_RUMOR,
        gt_sentiment=-0.9,
        gt_is_misinformation=True,
        gt_virality_potential=90
    )

    print(f"Agent: {agent.archetype_name} (Skepticism: {agent.skepticism_score})")
    print(f"Signal: {signal.content_text}")
    print("-" * 50)

    # Run decision
    decision = await brain.async_decide(agent, signal)

    print(f"\nAction: {decision.action.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Emotional State: {decision.emotional_state}")
    print(f"Share Probability: {decision.share_probability}")
    
    if decision.action.value in ["SHARE", "COMMENT"]:
        print("\nSUCCESS: Agent reacted to the scary signal!")
    elif decision.action.value == "IGNORE":
        print("\nNOTE: Agent ignored it (maybe too loyal?).")

if __name__ == "__main__":
    asyncio.run(test_agent_simulation())
