"""
AI Benchmarks module.

Provides benchmark suite runner for systematic AI evaluation.
Aggregates results and tracks performance trends.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.data_loader import get_data_loader
from backend.core.signal_detector import SignalDetector
from .evaluator import (
    EvaluationResult,
    SignalClassificationEvaluator,
    SentimentEvaluator,
    MisinformationEvaluator,
    ViralityEvaluator,
)


@dataclass
class BenchmarkResult:
    """Aggregated benchmark results."""
    
    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    results: list[EvaluationResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        return self.passed_tests / self.total_tests if self.total_tests > 0 else 0.0
    
    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.passed_tests == self.total_tests
    
    def to_dict(self) -> dict[str, Any]:
        """Export as dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": self.pass_rate,
            "results": [
                {
                    "name": r.metric_name,
                    "score": r.score,
                    "threshold": r.threshold,
                    "passed": r.passed,
                    "details": r.details,
                }
                for r in self.results
            ],
            "metadata": self.metadata,
        }
    
    def save(self, path: Path) -> None:
        """Save results to JSON file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))
    
    def __str__(self) -> str:
        """Format as readable string."""
        lines = [
            f"═══════════════════════════════════════════",
            f"  AI BENCHMARK RESULTS",
            f"  {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"═══════════════════════════════════════════",
            f"",
            f"  Pass Rate: {self.pass_rate:.1%} ({self.passed_tests}/{self.total_tests})",
            f"",
        ]
        
        for result in self.results:
            lines.append(str(result))
        
        lines.append("")
        lines.append("═══════════════════════════════════════════")
        
        return "\n".join(lines)


def run_classification_benchmark(
    signals: list,
    detector: Optional[SignalDetector] = None,
    threshold: float = 0.70
) -> EvaluationResult:
    """
    Run classification benchmark on signals.
    
    Args:
        signals: List of SocialSignal with gt_category
        detector: Optional detector to use for predictions
        threshold: Minimum accuracy threshold
    """
    evaluator = SignalClassificationEvaluator(threshold=threshold)
    
    # If detector provided, run detection
    if detector:
        clusters = detector.detect_clusters(signals)
        return evaluator.evaluate_clusters(clusters, signals)
    
    # Otherwise just return empty result
    return EvaluationResult(
        metric_name="Signal Classification Accuracy",
        score=0.0,
        threshold=threshold,
        passed=False,
        details={"error": "No detector provided"},
    )


def run_sentiment_benchmark(
    signals: list,
    predicted_sentiments: Optional[list[float]] = None,
    threshold: float = 0.25
) -> EvaluationResult:
    """
    Run sentiment analysis benchmark.
    
    Args:
        signals: List of SocialSignal with gt_sentiment
        predicted_sentiments: Optional list of predicted sentiments
        threshold: Maximum MAE threshold
    """
    evaluator = SentimentEvaluator(mae_threshold=threshold)
    
    if predicted_sentiments:
        for signal, pred in zip(signals, predicted_sentiments):
            if hasattr(signal, 'gt_sentiment') and signal.gt_sentiment is not None:
                evaluator.add_sample(pred, signal.gt_sentiment)
    
    return evaluator.evaluate()


def run_misinformation_benchmark(
    signals: list,
    predicted_misinfo: Optional[list[bool]] = None,
    threshold: float = 0.80
) -> EvaluationResult:
    """
    Run misinformation detection benchmark.
    
    Args:
        signals: List of SocialSignal with gt_is_misinformation
        predicted_misinfo: Optional list of predictions
        threshold: Minimum precision threshold
    """
    evaluator = MisinformationEvaluator(precision_threshold=threshold)
    
    if predicted_misinfo:
        for signal, pred in zip(signals, predicted_misinfo):
            if hasattr(signal, 'gt_is_misinformation') and signal.gt_is_misinformation is not None:
                evaluator.add_sample(pred, signal.gt_is_misinformation)
    
    return evaluator.evaluate()


def run_virality_benchmark(
    signals: list,
    predicted_virality: Optional[list[float]] = None,
    threshold: float = 15.0
) -> EvaluationResult:
    """
    Run virality prediction benchmark.
    
    Args:
        signals: List of SocialSignal with gt_virality_potential
        predicted_virality: Optional list of predictions (0-100)
        threshold: Maximum MAE threshold
    """
    evaluator = ViralityEvaluator(mae_threshold=threshold)
    
    if predicted_virality:
        for signal, pred in zip(signals, predicted_virality):
            if hasattr(signal, 'gt_virality_potential') and signal.gt_virality_potential is not None:
                evaluator.add_sample(pred, signal.gt_virality_potential)
    
    return evaluator.evaluate()


def run_benchmarks(
    n_signals: int = 100,
    run_detector: bool = False,
    save_results: bool = True,
    output_dir: Optional[Path] = None
) -> BenchmarkResult:
    """
    Run full benchmark suite.
    
    Args:
        n_signals: Number of signals to evaluate
        run_detector: Whether to run signal detector
        save_results: Whether to save results to file
        output_dir: Directory for saving results
    """
    loader = get_data_loader()
    signals = loader.load_signals(limit=n_signals)
    
    results: list[EvaluationResult] = []
    
    # Run classification benchmark
    if run_detector:
        try:
            detector = SignalDetector()
            result = run_classification_benchmark(signals, detector)
            results.append(result)
        except Exception as e:
            results.append(EvaluationResult(
                metric_name="Signal Classification Accuracy",
                score=0.0,
                threshold=0.70,
                passed=False,
                details={"error": str(e)},
            ))
    
    # Create benchmark result
    passed = sum(1 for r in results if r.passed)
    benchmark = BenchmarkResult(
        timestamp=datetime.now(),
        total_tests=len(results),
        passed_tests=passed,
        failed_tests=len(results) - passed,
        results=results,
        metadata={
            "n_signals": n_signals,
            "ran_detector": run_detector,
        },
    )
    
    # Save if requested
    if save_results and output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        benchmark.save(output_dir / filename)
    
    return benchmark


if __name__ == "__main__":
    """Run benchmarks from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run AI benchmarks")
    parser.add_argument("-n", "--n-signals", type=int, default=100)
    parser.add_argument("--run-detector", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark_results"))
    
    args = parser.parse_args()
    
    result = run_benchmarks(
        n_signals=args.n_signals,
        run_detector=args.run_detector,
        save_results=True,
        output_dir=args.output_dir,
    )
    
    print(result)
