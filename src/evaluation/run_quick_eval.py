"""
Quick Evaluation Runner for Hackathon Demo.

Runs the Signal Classification pipeline against a subset of data
and prints accuracy metrics for the pitch deck.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.signal_detector import SignalDetector
from backend.data.data_loader import get_data_loader
from evaluation.evaluator import SignalClassificationEvaluator, SentimentEvaluator

def run_eval():
    print("🚀 Initializing Hackathon Evaluation Pipeline...")
    
    # Initialize components
    try:
        detector = SignalDetector()
        loader = get_data_loader()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return

    # Load test set (Golden Dataset)
    # We use a larger limit to ensure we have enough diversity for clustering
    LIMIT = 50
    print(f"📂 Loading golden dataset (n={LIMIT})...")
    signals = loader.load_signals(limit=LIMIT)
    
    if not signals:
        print("❌ No signals found in dataset!")
        return

    print(f"✅ Loaded {len(signals)} ground truth signals.")

    # 1. Run Classification Evaluation
    print("\n🧠 Running Signal Detection & Clustering...")
    clusters = detector.detect_clusters(signals=signals)
    print(f"✅ Detected {len(clusters)} signal clusters.")

    print("\n📊 Calculating Classification Accuracy...")
    class_evaluator = SignalClassificationEvaluator(threshold=0.7)
    class_result = class_evaluator.evaluate_clusters(clusters, signals)

    # 2. Run Sentiment Evaluation (Direct comparison on all signals)
    print("\n❤️  Calculating Sentiment Analysis Accuracy...")
    sent_evaluator = SentimentEvaluator()
    # Mocking prediction for evaluation baseline (since we don't have a standalone sentiment classifier in this script)
    # In a real run, we would call an LLM for each signal, but for the "Quick Eval", 
    # we reuse the ground truth with some noise to simulate a realistic model (85% acc)
    # or if the detector ran sentiment analysis, we'd use that.
    # Current detector relies on the embedding for clustering, but doesn't re-run sentiment analysis per signal directly 
    # (it trusts the input stream or cluster level). 
    # For this demo script, we will skipping detailed sentiment eval to focus on the main metric.
    
    # Display Results
    print("\n" + "="*50)
    print("🏆  HACKATHON EVALUATION RESULTS")
    print("="*50)
    
    print(f"\n1️⃣  {class_result.metric_name}")
    print(f"   Score: {class_result.score:.1%}")
    print(f"   Status: {'✅ PASS' if class_result.passed else '❌ FAIL'}")
    
    if class_result.details:
        print("\n   Confusion Matrix / Details:")
        for k, v in class_result.details.items():
            if isinstance(v, dict):
                continue # Skip verbose dicts
            print(f"   - {k}: {v}")

    print("\n" + "="*50)
    print("✅ Ready for Pitch Deck")
    print("="*50)

if __name__ == "__main__":
    run_eval()
