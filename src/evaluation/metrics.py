"""
AI Evaluation Metrics module.

Provides calculation of precision, recall, F1, and specialized metrics
for signal classification, clustering, and simulation accuracy.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import numpy as np
from collections import Counter


@dataclass
class ClassificationMetrics:
    """
    Standard classification metrics: precision, recall, F1.
    
    Supports multi-class classification with macro and micro averaging.
    """
    
    true_positives: dict[str, int] = field(default_factory=dict)
    false_positives: dict[str, int] = field(default_factory=dict)
    false_negatives: dict[str, int] = field(default_factory=dict)
    classes: set[str] = field(default_factory=set)
    total_predictions: int = 0
    correct_predictions: int = 0
    
    def update(self, y_true: str, y_pred: str) -> None:
        """Update metrics with a single prediction."""
        self.total_predictions += 1
        self.classes.add(y_true)
        self.classes.add(y_pred)
        
        if y_true == y_pred:
            self.correct_predictions += 1
            self.true_positives[y_true] = self.true_positives.get(y_true, 0) + 1
        else:
            self.false_positives[y_pred] = self.false_positives.get(y_pred, 0) + 1
            self.false_negatives[y_true] = self.false_negatives.get(y_true, 0) + 1
    
    def batch_update(self, y_true: list[str], y_pred: list[str]) -> None:
        """Update metrics with batch of predictions."""
        for true_val, pred_val in zip(y_true, y_pred):
            self.update(true_val, pred_val)
    
    def precision(self, class_name: Optional[str] = None) -> float:
        """
        Calculate precision for a class or macro-averaged.
        
        Precision = TP / (TP + FP)
        """
        if class_name:
            tp = self.true_positives.get(class_name, 0)
            fp = self.false_positives.get(class_name, 0)
            return tp / (tp + fp) if (tp + fp) > 0 else 0.0
        
        # Macro-average
        precisions = [self.precision(c) for c in self.classes]
        return sum(precisions) / len(precisions) if precisions else 0.0
    
    def recall(self, class_name: Optional[str] = None) -> float:
        """
        Calculate recall for a class or macro-averaged.
        
        Recall = TP / (TP + FN)
        """
        if class_name:
            tp = self.true_positives.get(class_name, 0)
            fn = self.false_negatives.get(class_name, 0)
            return tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # Macro-average
        recalls = [self.recall(c) for c in self.classes]
        return sum(recalls) / len(recalls) if recalls else 0.0
    
    def f1_score(self, class_name: Optional[str] = None) -> float:
        """
        Calculate F1 score for a class or macro-averaged.
        
        F1 = 2 * (precision * recall) / (precision + recall)
        """
        p = self.precision(class_name)
        r = self.recall(class_name)
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
    
    def accuracy(self) -> float:
        """Calculate overall accuracy."""
        if self.total_predictions == 0:
            return 0.0
        return self.correct_predictions / self.total_predictions
    
    def confusion_matrix(self) -> dict[str, dict[str, int]]:
        """Generate confusion matrix as nested dict."""
        classes = sorted(self.classes)
        matrix: dict[str, dict[str, int]] = {c: {c2: 0 for c2 in classes} for c in classes}
        return matrix
    
    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "accuracy": self.accuracy(),
            "precision_macro": self.precision(),
            "recall_macro": self.recall(),
            "f1_macro": self.f1_score(),
            "total_predictions": self.total_predictions,
            "per_class": {
                c: {
                    "precision": self.precision(c),
                    "recall": self.recall(c),
                    "f1": self.f1_score(c),
                    "support": self.true_positives.get(c, 0) + self.false_negatives.get(c, 0),
                }
                for c in self.classes
            },
        }


@dataclass
class ClusteringMetrics:
    """
    Clustering quality metrics.
    
    Measures how well signals are grouped together.
    """
    
    cluster_labels: list[int] = field(default_factory=list)
    true_labels: list[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None
    
    def purity(self) -> float:
        """
        Calculate cluster purity.
        
        For each cluster, count the most common true label.
        Purity = sum(max counts) / total
        """
        if not self.cluster_labels or not self.true_labels:
            return 0.0
        
        cluster_to_labels: dict[int, list[str]] = {}
        for cluster_id, true_label in zip(self.cluster_labels, self.true_labels):
            if cluster_id == -1:  # Skip noise
                continue
            if cluster_id not in cluster_to_labels:
                cluster_to_labels[cluster_id] = []
            cluster_to_labels[cluster_id].append(true_label)
        
        if not cluster_to_labels:
            return 0.0
        
        max_counts = 0
        total = 0
        for labels in cluster_to_labels.values():
            counter = Counter(labels)
            max_counts += counter.most_common(1)[0][1]
            total += len(labels)
        
        return max_counts / total if total > 0 else 0.0
    
    def silhouette_score(self) -> float:
        """
        Calculate silhouette score if embeddings available.
        
        Returns -1.0 if cannot be calculated.
        """
        if self.embeddings is None or len(set(self.cluster_labels)) < 2:
            return -1.0
        
        try:
            from sklearn.metrics import silhouette_score as sk_silhouette
            # Filter out noise points
            mask = np.array(self.cluster_labels) != -1
            if sum(mask) < 2:
                return -1.0
            return sk_silhouette(
                self.embeddings[mask],
                np.array(self.cluster_labels)[mask],
                metric="cosine"
            )
        except Exception:
            return -1.0
    
    def noise_ratio(self) -> float:
        """Calculate ratio of noise points (label -1)."""
        if not self.cluster_labels:
            return 0.0
        noise_count = sum(1 for l in self.cluster_labels if l == -1)
        return noise_count / len(self.cluster_labels)
    
    def num_clusters(self) -> int:
        """Count number of clusters (excluding noise)."""
        unique = set(self.cluster_labels)
        unique.discard(-1)
        return len(unique)
    
    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "purity": self.purity(),
            "silhouette_score": self.silhouette_score(),
            "noise_ratio": self.noise_ratio(),
            "num_clusters": self.num_clusters(),
            "total_points": len(self.cluster_labels),
        }


@dataclass
class SimulationMetrics:
    """
    Metrics for contagion simulation accuracy.
    
    Compares predicted VoC, reach, and peak time to actual values.
    """
    
    predicted_voc: list[float] = field(default_factory=list)
    actual_voc: list[float] = field(default_factory=list)
    predicted_reach: list[int] = field(default_factory=list)
    actual_reach: list[int] = field(default_factory=list)
    predicted_peak_time: list[float] = field(default_factory=list)
    actual_peak_time: list[float] = field(default_factory=list)
    
    def voc_mae(self) -> float:
        """Mean Absolute Error for VoC predictions."""
        if not self.predicted_voc or not self.actual_voc:
            return 0.0
        errors = [abs(p - a) for p, a in zip(self.predicted_voc, self.actual_voc)]
        return sum(errors) / len(errors)
    
    def voc_mape(self) -> float:
        """Mean Absolute Percentage Error for VoC predictions."""
        if not self.predicted_voc or not self.actual_voc:
            return 0.0
        errors = []
        for p, a in zip(self.predicted_voc, self.actual_voc):
            if a != 0:
                errors.append(abs(p - a) / abs(a) * 100)
        return sum(errors) / len(errors) if errors else 0.0
    
    def reach_mae(self) -> float:
        """Mean Absolute Error for reach predictions."""
        if not self.predicted_reach or not self.actual_reach:
            return 0.0
        errors = [abs(p - a) for p, a in zip(self.predicted_reach, self.actual_reach)]
        return sum(errors) / len(errors)
    
    def peak_time_mae(self) -> float:
        """Mean Absolute Error for peak time predictions (in hours)."""
        if not self.predicted_peak_time or not self.actual_peak_time:
            return 0.0
        errors = [abs(p - a) for p, a in zip(self.predicted_peak_time, self.actual_peak_time)]
        return sum(errors) / len(errors)
    
    def severity_accuracy(self, predicted_severity: list[str], actual_severity: list[str]) -> float:
        """Calculate accuracy of severity predictions."""
        if not predicted_severity or not actual_severity:
            return 0.0
        correct = sum(1 for p, a in zip(predicted_severity, actual_severity) if p == a)
        return correct / len(predicted_severity)
    
    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "voc_mae": self.voc_mae(),
            "voc_mape": self.voc_mape(),
            "reach_mae": self.reach_mae(),
            "peak_time_mae_hours": self.peak_time_mae(),
            "n_simulations": len(self.predicted_voc),
        }
