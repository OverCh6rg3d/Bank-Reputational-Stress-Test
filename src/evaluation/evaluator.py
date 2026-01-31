"""
AI Evaluators module.

Provides evaluators for comparing AI predictions to ground truth labels
present in the synthetic dataset.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.schemas import SocialSignal, SignalCluster, SignalCategory
from .metrics import ClassificationMetrics


@dataclass
class EvaluationResult:
    """Result of evaluating AI predictions against ground truth."""
    
    metric_name: str
    score: float
    threshold: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} {self.metric_name}: {self.score:.2%} (threshold: {self.threshold:.2%})"


class SignalClassificationEvaluator:
    """
    Evaluates signal classification accuracy.
    
    Compares predicted categories to gt_category field in signals.
    """
    
    def __init__(self, threshold: float = 0.70):
        """
        Initialize evaluator.
        
        Args:
            threshold: Minimum accuracy to pass (default 70%)
        """
        self.threshold = threshold
        self.metrics = ClassificationMetrics()
    
    def evaluate_clusters(
        self, 
        clusters: list[SignalCluster], 
        signals: list[SocialSignal]
    ) -> EvaluationResult:
        """
        Evaluate classification accuracy from clustered signals.
        
        Each cluster has a primary_category that should match
        the majority of gt_category values in its signals.
        """
        signal_lookup = {s.signal_id: s for s in signals}
        
        for cluster in clusters:
            predicted = cluster.primary_category.value if hasattr(cluster.primary_category, 'value') else str(cluster.primary_category)
            
            for signal_id in cluster.signals:
                signal = signal_lookup.get(signal_id)
                if signal and signal.gt_category:
                    actual = signal.gt_category.value if hasattr(signal.gt_category, 'value') else str(signal.gt_category)
                    self.metrics.update(actual, predicted)
        
        accuracy = self.metrics.accuracy()
        
        return EvaluationResult(
            metric_name="Signal Classification Accuracy",
            score=accuracy,
            threshold=self.threshold,
            passed=accuracy >= self.threshold,
            details=self.metrics.to_dict(),
        )
    
    def evaluate_direct(
        self,
        predictions: list[SignalCategory],
        ground_truth: list[SignalCategory]
    ) -> EvaluationResult:
        """
        Evaluate direct predictions against ground truth.
        
        Args:
            predictions: Predicted categories
            ground_truth: Actual categories from gt_category
        """
        y_pred = [p.value if hasattr(p, 'value') else str(p) for p in predictions]
        y_true = [g.value if hasattr(g, 'value') else str(g) for g in ground_truth]
        
        self.metrics.batch_update(y_true, y_pred)
        accuracy = self.metrics.accuracy()
        
        return EvaluationResult(
            metric_name="Signal Classification Accuracy",
            score=accuracy,
            threshold=self.threshold,
            passed=accuracy >= self.threshold,
            details=self.metrics.to_dict(),
        )


class SentimentEvaluator:
    """
    Evaluates sentiment analysis accuracy.
    
    Compares detected sentiment values to gt_sentiment field.
    Uses Mean Absolute Error and correlation.
    """
    
    def __init__(self, mae_threshold: float = 0.25):
        """
        Initialize evaluator.
        
        Args:
            mae_threshold: Maximum MAE to pass (default 0.25 on -1 to 1 scale)
        """
        self.mae_threshold = mae_threshold
        self.predictions: list[float] = []
        self.ground_truth: list[float] = []
    
    def add_sample(self, predicted: float, actual: float) -> None:
        """Add a single prediction-ground truth pair."""
        self.predictions.append(predicted)
        self.ground_truth.append(actual)
    
    def add_batch(self, predicted: list[float], actual: list[float]) -> None:
        """Add batch of predictions."""
        self.predictions.extend(predicted)
        self.ground_truth.extend(actual)
    
    def mae(self) -> float:
        """Calculate Mean Absolute Error."""
        if not self.predictions:
            return 0.0
        errors = [abs(p - a) for p, a in zip(self.predictions, self.ground_truth)]
        return sum(errors) / len(errors)
    
    def correlation(self) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(self.predictions) < 2:
            return 0.0
        
        import numpy as np
        return float(np.corrcoef(self.predictions, self.ground_truth)[0, 1])
    
    def direction_accuracy(self) -> float:
        """
        Calculate accuracy of sentiment direction.
        
        Positive (>0), Negative (<0), Neutral (≈0)
        """
        if not self.predictions:
            return 0.0
        
        def direction(v: float) -> str:
            if v > 0.1:
                return "positive"
            elif v < -0.1:
                return "negative"
            return "neutral"
        
        correct = sum(
            1 for p, a in zip(self.predictions, self.ground_truth)
            if direction(p) == direction(a)
        )
        return correct / len(self.predictions)
    
    def evaluate(self) -> EvaluationResult:
        """Run evaluation and return result."""
        mae = self.mae()
        
        return EvaluationResult(
            metric_name="Sentiment Analysis MAE",
            score=1 - mae,  # Convert to accuracy-like score
            threshold=1 - self.mae_threshold,
            passed=mae <= self.mae_threshold,
            details={
                "mae": mae,
                "correlation": self.correlation(),
                "direction_accuracy": self.direction_accuracy(),
                "n_samples": len(self.predictions),
            },
        )


class MisinformationEvaluator:
    """
    Evaluates misinformation detection accuracy.
    
    Compares RAG fact-checker results to gt_is_misinformation field.
    Focuses on precision to minimize false positives.
    """
    
    def __init__(self, precision_threshold: float = 0.80):
        """
        Initialize evaluator.
        
        Args:
            precision_threshold: Minimum precision to pass (default 80%)
        """
        self.precision_threshold = precision_threshold
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.true_negatives = 0
    
    def add_sample(self, predicted_misinfo: bool, actual_misinfo: bool) -> None:
        """Add a single prediction."""
        if predicted_misinfo and actual_misinfo:
            self.true_positives += 1
        elif predicted_misinfo and not actual_misinfo:
            self.false_positives += 1
        elif not predicted_misinfo and actual_misinfo:
            self.false_negatives += 1
        else:
            self.true_negatives += 1
    
    def precision(self) -> float:
        """Calculate precision (avoid false accusations)."""
        total_predicted = self.true_positives + self.false_positives
        return self.true_positives / total_predicted if total_predicted > 0 else 0.0
    
    def recall(self) -> float:
        """Calculate recall (catch all misinformation)."""
        total_actual = self.true_positives + self.false_negatives
        return self.true_positives / total_actual if total_actual > 0 else 0.0
    
    def f1_score(self) -> float:
        """Calculate F1 score."""
        p = self.precision()
        r = self.recall()
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
    
    def accuracy(self) -> float:
        """Calculate overall accuracy."""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0
    
    def evaluate(self) -> EvaluationResult:
        """Run evaluation and return result."""
        precision = self.precision()
        
        return EvaluationResult(
            metric_name="Misinformation Detection Precision",
            score=precision,
            threshold=self.precision_threshold,
            passed=precision >= self.precision_threshold,
            details={
                "precision": precision,
                "recall": self.recall(),
                "f1_score": self.f1_score(),
                "accuracy": self.accuracy(),
                "confusion_matrix": {
                    "true_positives": self.true_positives,
                    "false_positives": self.false_positives,
                    "true_negatives": self.true_negatives,
                    "false_negatives": self.false_negatives,
                },
            },
        )


class ViralityEvaluator:
    """
    Evaluates virality prediction accuracy.
    
    Compares VoC predictions to gt_virality_potential field.
    """
    
    def __init__(self, mae_threshold: float = 15.0):
        """
        Initialize evaluator.
        
        Args:
            mae_threshold: Maximum MAE to pass (default 15 on 0-100 scale)
        """
        self.mae_threshold = mae_threshold
        self.predictions: list[float] = []
        self.ground_truth: list[float] = []
    
    def add_sample(self, predicted: float, actual: float) -> None:
        """Add a single prediction (0-100 scale)."""
        self.predictions.append(predicted)
        self.ground_truth.append(actual)
    
    def add_batch(self, predicted: list[float], actual: list[float]) -> None:
        """Add batch of predictions."""
        self.predictions.extend(predicted)
        self.ground_truth.extend(actual)
    
    def mae(self) -> float:
        """Calculate Mean Absolute Error."""
        if not self.predictions:
            return 0.0
        errors = [abs(p - a) for p, a in zip(self.predictions, self.ground_truth)]
        return sum(errors) / len(errors)
    
    def mape(self) -> float:
        """Calculate Mean Absolute Percentage Error."""
        if not self.predictions:
            return 0.0
        errors = []
        for p, a in zip(self.predictions, self.ground_truth):
            if a > 0:
                errors.append(abs(p - a) / a * 100)
        return sum(errors) / len(errors) if errors else 0.0
    
    def within_n(self, n: float = 10.0) -> float:
        """Calculate percentage of predictions within ±n of actual."""
        if not self.predictions:
            return 0.0
        correct = sum(
            1 for p, a in zip(self.predictions, self.ground_truth)
            if abs(p - a) <= n
        )
        return correct / len(self.predictions)
    
    def evaluate(self) -> EvaluationResult:
        """Run evaluation and return result."""
        mae = self.mae()
        
        return EvaluationResult(
            metric_name="Virality Prediction MAE",
            score=max(0, 1 - mae / 100),  # Convert to 0-1 scale
            threshold=1 - self.mae_threshold / 100,
            passed=mae <= self.mae_threshold,
            details={
                "mae": mae,
                "mape": self.mape(),
                "within_10": self.within_n(10),
                "within_20": self.within_n(20),
                "n_samples": len(self.predictions),
            },
        )
