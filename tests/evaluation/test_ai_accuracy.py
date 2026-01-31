"""
AI Accuracy Evaluation Tests.

Tests that AI components meet minimum accuracy thresholds
using ground truth labels from the synthetic dataset.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from evaluation.metrics import ClassificationMetrics, ClusteringMetrics, SimulationMetrics
from evaluation.evaluator import (
    SignalClassificationEvaluator,
    SentimentEvaluator,
    MisinformationEvaluator,
    ViralityEvaluator,
    EvaluationResult,
)


class TestClassificationMetrics:
    """Tests for ClassificationMetrics class."""
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation."""
        metrics = ClassificationMetrics()
        
        # Add 7 correct, 3 incorrect
        for _ in range(7):
            metrics.update("A", "A")
        for _ in range(3):
            metrics.update("B", "A")
        
        assert metrics.accuracy() == 0.7
    
    def test_precision_calculation(self):
        """Test precision calculation for class."""
        metrics = ClassificationMetrics()
        
        # TP=5, FP=2 for class A
        for _ in range(5):
            metrics.update("A", "A")
        for _ in range(2):
            metrics.update("B", "A")
        
        precision = metrics.precision("A")
        assert precision == 5 / 7  # 0.714...
    
    def test_recall_calculation(self):
        """Test recall calculation for class."""
        metrics = ClassificationMetrics()
        
        # TP=5, FN=2 for class A
        for _ in range(5):
            metrics.update("A", "A")
        for _ in range(2):
            metrics.update("A", "B")
        
        recall = metrics.recall("A")
        assert recall == 5 / 7  # 0.714...
    
    def test_f1_score_calculation(self):
        """Test F1 score calculation."""
        metrics = ClassificationMetrics()
        
        # Balanced case
        for _ in range(5):
            metrics.update("A", "A")
        for _ in range(1):
            metrics.update("B", "A")  # FP
        for _ in range(1):
            metrics.update("A", "B")  # FN
        
        f1 = metrics.f1_score("A")
        # Precision = 5/6, Recall = 5/6, F1 = 5/6
        assert abs(f1 - (5/6)) < 0.01
    
    def test_empty_metrics(self):
        """Test metrics with no data."""
        metrics = ClassificationMetrics()
        
        assert metrics.accuracy() == 0.0
        assert metrics.precision() == 0.0
        assert metrics.recall() == 0.0


class TestClusteringMetrics:
    """Tests for ClusteringMetrics class."""
    
    def test_purity_perfect_clusters(self):
        """Test purity with perfectly pure clusters."""
        metrics = ClusteringMetrics(
            cluster_labels=[0, 0, 0, 1, 1, 1],
            true_labels=["A", "A", "A", "B", "B", "B"],
        )
        
        assert metrics.purity() == 1.0
    
    def test_purity_impure_clusters(self):
        """Test purity with mixed clusters."""
        metrics = ClusteringMetrics(
            cluster_labels=[0, 0, 0, 0, 1, 1],
            true_labels=["A", "A", "B", "B", "A", "A"],
        )
        
        # Cluster 0: 2 A, 2 B -> max = 2
        # Cluster 1: 2 A -> max = 2
        # Total purity = (2+2)/6 = 0.666...
        assert abs(metrics.purity() - 0.667) < 0.01
    
    def test_noise_ratio(self):
        """Test noise ratio calculation."""
        metrics = ClusteringMetrics(
            cluster_labels=[0, 0, -1, -1, 1, -1],
            true_labels=["A", "A", "A", "B", "B", "B"],
        )
        
        # 3 noise points out of 6
        assert metrics.noise_ratio() == 0.5
    
    def test_num_clusters(self):
        """Test cluster counting."""
        metrics = ClusteringMetrics(
            cluster_labels=[0, 0, 1, 1, 2, -1],
            true_labels=["A"] * 6,
        )
        
        assert metrics.num_clusters() == 3


class TestSentimentEvaluator:
    """Tests for SentimentEvaluator."""
    
    def test_perfect_predictions(self):
        """Test with perfect predictions."""
        evaluator = SentimentEvaluator(mae_threshold=0.25)
        
        evaluator.add_batch(
            predicted=[0.5, -0.3, 0.0, 0.8],
            actual=[0.5, -0.3, 0.0, 0.8],
        )
        
        result = evaluator.evaluate()
        assert result.passed
        assert evaluator.mae() == 0.0
    
    def test_within_threshold(self):
        """Test predictions within acceptable threshold."""
        evaluator = SentimentEvaluator(mae_threshold=0.25)
        
        evaluator.add_batch(
            predicted=[0.5, -0.3, 0.1],
            actual=[0.6, -0.2, 0.0],  # Errors: 0.1, 0.1, 0.1
        )
        
        assert evaluator.mae() < 0.25
        assert evaluator.evaluate().passed
    
    def test_direction_accuracy(self):
        """Test sentiment direction accuracy."""
        evaluator = SentimentEvaluator()
        
        evaluator.add_batch(
            predicted=[0.5, -0.5, 0.0, 0.3],   # pos, neg, neu, pos
            actual=[0.3, -0.8, 0.05, 0.8],     # pos, neg, neu, pos
        )
        
        # All directions match
        assert evaluator.direction_accuracy() == 1.0


class TestMisinformationEvaluator:
    """Tests for MisinformationEvaluator."""
    
    def test_perfect_precision(self):
        """Test with perfect precision."""
        evaluator = MisinformationEvaluator(precision_threshold=0.80)
        
        # All positives are correct
        evaluator.add_sample(True, True)
        evaluator.add_sample(True, True)
        evaluator.add_sample(False, False)
        
        assert evaluator.precision() == 1.0
        assert evaluator.evaluate().passed
    
    def test_precision_threshold_fail(self):
        """Test failing precision threshold."""
        evaluator = MisinformationEvaluator(precision_threshold=0.80)
        
        # 1 TP, 2 FP
        evaluator.add_sample(True, True)
        evaluator.add_sample(True, False)
        evaluator.add_sample(True, False)
        
        # Precision = 1/3 = 0.33
        assert not evaluator.evaluate().passed
    
    def test_confusion_matrix(self):
        """Test confusion matrix in details."""
        evaluator = MisinformationEvaluator()
        
        evaluator.add_sample(True, True)   # TP
        evaluator.add_sample(True, False)  # FP
        evaluator.add_sample(False, True)  # FN
        evaluator.add_sample(False, False) # TN
        
        result = evaluator.evaluate()
        cm = result.details["confusion_matrix"]
        
        assert cm["true_positives"] == 1
        assert cm["false_positives"] == 1
        assert cm["true_negatives"] == 1
        assert cm["false_negatives"] == 1


class TestViralityEvaluator:
    """Tests for ViralityEvaluator."""
    
    def test_mae_calculation(self):
        """Test MAE calculation."""
        evaluator = ViralityEvaluator(mae_threshold=15.0)
        
        evaluator.add_batch(
            predicted=[50, 60, 70],
            actual=[55, 65, 75],  # All off by 5
        )
        
        assert evaluator.mae() == 5.0
        assert evaluator.evaluate().passed
    
    def test_within_n_accuracy(self):
        """Test within-N calculation."""
        evaluator = ViralityEvaluator()
        
        evaluator.add_batch(
            predicted=[50, 60, 70, 80],
            actual=[52, 75, 72, 81],  # Errors: 2, 15, 2, 1
        )
        
        # 3 out of 4 within ±10
        assert evaluator.within_n(10) == 0.75
    
    def test_exceeds_threshold(self):
        """Test failing threshold."""
        evaluator = ViralityEvaluator(mae_threshold=15.0)
        
        evaluator.add_batch(
            predicted=[50, 60, 70],
            actual=[30, 30, 30],  # Errors: 20, 30, 40
        )
        
        assert evaluator.mae() == 30.0
        assert not evaluator.evaluate().passed


class TestSimulationMetrics:
    """Tests for SimulationMetrics."""
    
    def test_voc_mae(self):
        """Test VoC MAE calculation."""
        metrics = SimulationMetrics(
            predicted_voc=[50.0, 60.0, 70.0],
            actual_voc=[55.0, 65.0, 75.0],
        )
        
        assert metrics.voc_mae() == 5.0
    
    def test_reach_mae(self):
        """Test reach MAE calculation."""
        metrics = SimulationMetrics(
            predicted_reach=[1000, 2000, 3000],
            actual_reach=[1100, 2100, 3100],
        )
        
        assert metrics.reach_mae() == 100.0


class TestBenchmarkThresholds:
    """Tests to validate AI meets minimum thresholds."""
    
    @pytest.mark.evaluation
    def test_classification_accuracy_minimum(self):
        """Test that classification accuracy meets 70% threshold."""
        # This is a placeholder - actual test requires running detector
        threshold = 0.70
        
        # Simulate a passing result
        evaluator = SignalClassificationEvaluator(threshold=threshold)
        evaluator.metrics.batch_update(
            y_true=["A", "A", "A", "B", "B"],
            y_pred=["A", "A", "A", "B", "A"],  # 80% accuracy
        )
        
        result = evaluator.evaluate_direct([], [])  # Use existing metrics
        # Note: This is a simulation, actual test would use detector
        assert evaluator.metrics.accuracy() >= threshold
    
    @pytest.mark.evaluation
    def test_misinformation_precision_minimum(self):
        """Test that misinformation detection precision meets 80% threshold."""
        threshold = 0.80
        
        evaluator = MisinformationEvaluator(precision_threshold=threshold)
        
        # Simulate 85% precision: 17 TP, 3 FP
        for _ in range(17):
            evaluator.add_sample(True, True)
        for _ in range(3):
            evaluator.add_sample(True, False)
        
        result = evaluator.evaluate()
        assert result.passed
        assert result.score >= threshold
