
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.core.debate import DebateEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_real_debate():
    print("\n=== Testing Real AI Debate Engine ===\n")
    
    # Initialize with use_llm=True
    try:
        engine = DebateEngine(use_llm=True)
    except Exception as e:
        print(f"Skipping test: Could not initialize DebateEngine (missing API key?): {e}")
        return

    # Scenario: Uncertain data leak
    finding = "A cluster of 15 tweets suggests a potential data leak at Mashreq. High severity."
    confidence = 0.85
    context = """
    Signals:
    - @User123: "Heard rumors Mashreq got hacked? My app is acting weird."
    - @TechGuru: "Just saw a pastebin link claiming to be Mashreq DB. Looking into it."
    - @RandomBot: "Alert! mashreq breach! click here" (Spam probability 0.9)
    
    Analysis:
    - Cluster size: 15
    - Velocity: 5 signals/hour
    - Sentiment: Negative (-0.7)
    """

    print(f"Topic: {finding}")
    print(f"Initial Confidence: {confidence}")
    print("-" * 50)

    # Run debate
    result = engine.run_debate(
        initial_finding=finding,
        initial_confidence=confidence,
        context=context,
        max_turns=2
    )

    # Print transcript
    for turn in result.turns:
        print(f"\n{turn.speaker} (Conf: {turn.confidence:.2f}):")
        print(f"\"{turn.content}\"")
        
    print("-" * 50)
    print(f"\nFinal Consensus: {result.final_consensus}")
    print(f"Refined Confidence: {result.refined_confidence:.2f}")
    
    if result.refined_confidence != confidence:
        print("\nSUCCESS: Confidence was adjusted by the debate!")
    else:
        print("\nNOTE: Confidence remained unchanged.")

if __name__ == "__main__":
    test_real_debate()
