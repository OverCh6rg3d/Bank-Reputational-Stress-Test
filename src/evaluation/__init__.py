"""
AI Evaluation Framework package.

Provides metrics, evaluators, and benchmarks for assessing AI performance.
"""

from .metrics import ClassificationMetrics, ClusteringMetrics, SimulationMetrics
from .evaluator import (
    SignalClassificationEvaluator,
    SentimentEvaluator,
    MisinformationEvaluator,
    ViralityEvaluator,
)
from .benchmarks import run_benchmarks, BenchmarkResult

__all__ = [
    "ClassificationMetrics",
    "ClusteringMetrics",
    "SimulationMetrics",
    "SignalClassificationEvaluator",
    "SentimentEvaluator",
    "MisinformationEvaluator",
    "ViralityEvaluator",
    "run_benchmarks",
    "BenchmarkResult",
]
