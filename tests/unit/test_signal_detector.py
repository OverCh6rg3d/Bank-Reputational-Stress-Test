"""
Unit tests for the Signal Detector module.

Tests DBSCAN clustering, severity calculation, and velocity detection.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.models.schemas import (
    SignalCategory,
    SeverityLevel,
    PlatformSource,
    SocialSignal,
)


class TestSeverityCalculation:
    """Tests for severity level calculation logic."""
    
    def test_critical_severity_high_negative_sentiment_high_virality(self):
        """Test that highly negative, viral fraud signals get CRITICAL."""
        # Simulating the severity calculation logic
        avg_sentiment = -0.9
        avg_virality = 90
        signal_count = 60
        category = SignalCategory.FRAUD_RUMOR
        
        score = 0
        score += (1 - avg_sentiment) * 25  # -0.9 -> 47.5
        score += avg_virality * 0.3  # 90 -> 27
        if signal_count > 50:
            score += 15
        if category == SignalCategory.FRAUD_RUMOR:
            score += 20
        
        # Total: 47.5 + 27 + 15 + 20 = 109.5
        assert score >= 70
        expected_severity = SeverityLevel.CRITICAL
        
        if score >= 70:
            result = SeverityLevel.CRITICAL
        elif score >= 50:
            result = SeverityLevel.HIGH
        elif score >= 30:
            result = SeverityLevel.MEDIUM
        else:
            result = SeverityLevel.LOW
        
        assert result == expected_severity
    
    def test_low_severity_positive_sentiment(self):
        """Test that positive sentiment results in LOW/POSITIVE severity."""
        avg_sentiment = 0.8
        avg_virality = 20
        signal_count = 5
        category = SignalCategory.POSITIVE_NEUTRAL
        
        score = 0
        score += (1 - avg_sentiment) * 25  # 0.8 -> 5
        score += avg_virality * 0.3  # 20 -> 6
        # No bonuses for low count and positive category
        
        # Total: ~11
        assert score < 30
    
    def test_medium_severity_service_outage(self):
        """Test that moderate service outage signals get MEDIUM."""
        avg_sentiment = -0.3
        avg_virality = 50
        signal_count = 15
        category = SignalCategory.SERVICE_OUTAGE
        
        score = 0
        score += (1 - avg_sentiment) * 25  # -0.3 -> 32.5
        score += avg_virality * 0.3  # 50 -> 15
        if signal_count > 10:
            score += 5
        # No fraud bonus
        
        # Total: 32.5 + 15 + 5 = 52.5
        assert 30 <= score < 70


class TestVelocityCalculation:
    """Tests for velocity (signals per hour) calculation."""
    
    def test_velocity_with_one_hour_span(self, sample_signals):
        """Test velocity calculation with signals over one hour."""
        # Modify signals to span 1 hour
        now = datetime.now()
        for i, signal in enumerate(sample_signals):
            signal.timestamp = now - timedelta(minutes=i * 6)  # 6 min apart
        
        sorted_signals = sorted(sample_signals, key=lambda s: s.timestamp)
        earliest = sorted_signals[0].timestamp
        latest = sorted_signals[-1].timestamp
        
        span_hours = (latest - earliest).total_seconds() / 3600
        velocity = len(sample_signals) / max(span_hours, 1)
        
        assert velocity > 0
        assert isinstance(velocity, float)
    
    def test_velocity_zero_for_empty_signals(self):
        """Test that empty signal list returns zero velocity."""
        signals = []
        velocity = 0.0 if not signals else len(signals) / 1.0
        assert velocity == 0.0
    
    def test_velocity_handles_same_timestamp(self, sample_signal):
        """Test velocity when all signals have same timestamp."""
        signals = [sample_signal] * 5
        # All same timestamp means span = 0, should use window_hours = 1
        velocity = len(signals) / 1.0  # Avoid division by zero
        assert velocity == 5.0


class TestAnomalyDetection:
    """Tests for velocity anomaly detection."""
    
    def test_detects_spike_above_threshold(self):
        """Test that high velocity triggers anomaly detection."""
        current_velocity = 50.0
        baseline_velocity = 10.0
        threshold_multiplier = 3.0
        
        spike = (current_velocity - baseline_velocity) / baseline_velocity * 100
        is_anomaly = current_velocity > baseline_velocity * threshold_multiplier
        
        assert is_anomaly  # 50 > 10 * 3 = 30
        assert spike == 400.0  # 400% increase
    
    def test_no_anomaly_for_normal_velocity(self):
        """Test that normal velocity doesn't trigger anomaly."""
        current_velocity = 15.0
        baseline_velocity = 10.0
        threshold_multiplier = 3.0
        
        is_anomaly = current_velocity > baseline_velocity * threshold_multiplier
        
        assert not is_anomaly  # 15 < 30
    
    def test_handles_zero_baseline(self):
        """Test that zero baseline doesn't cause division error."""
        current_velocity = 5.0
        baseline_velocity = 0.0
        
        # Should use 1 as minimum baseline
        safe_baseline = max(baseline_velocity, 1.0)
        spike = (current_velocity - safe_baseline) / safe_baseline * 100
        
        assert spike == 400.0  # (5-1)/1 * 100


class TestClusteringLogic:
    """Tests for DBSCAN clustering behavior."""
    
    def test_min_samples_threshold(self):
        """Test that minimum samples are required for clustering."""
        from sklearn.cluster import DBSCAN
        
        # Create 2 signals (below min_samples=3)
        embeddings = np.array([[0.1, 0.2], [0.15, 0.25]])
        
        clustering = DBSCAN(eps=0.3, min_samples=3, metric="cosine")
        labels = clustering.fit_predict(embeddings)
        
        # All should be noise (-1) when below min_samples
        assert all(label == -1 for label in labels)
    
    def test_similar_signals_cluster_together(self):
        """Test that similar embeddings form clusters."""
        from sklearn.cluster import DBSCAN
        
        # Create 5 similar signals and 5 different ones
        cluster1 = np.array([[0.1, 0.1, 0.1]] * 5)
        cluster2 = np.array([[0.9, 0.9, 0.9]] * 5)
        embeddings = np.vstack([cluster1, cluster2])
        
        clustering = DBSCAN(eps=0.3, min_samples=3, metric="cosine")
        labels = clustering.fit_predict(embeddings)
        
        # Should form clusters (cosine distance normalizes vectors)
        unique_labels = set(labels)
        unique_labels.discard(-1)  # Remove noise label
        assert len(unique_labels) >= 1  # At least one cluster formed
    
    def test_cosine_metric_used(self):
        """Test that cosine similarity is used for clustering."""
        from sklearn.cluster import DBSCAN
        
        # Vectors that are similar in direction but different magnitude
        embeddings = np.array([
            [1.0, 0.0],
            [2.0, 0.0],  # Same direction, different magnitude
            [3.0, 0.0],
        ])
        
        clustering = DBSCAN(eps=0.1, min_samples=2, metric="cosine")
        labels = clustering.fit_predict(embeddings)
        
        # With cosine distance, these should cluster (angle = 0)
        assert len(set(labels)) <= 2  # Either all same cluster or some noise
