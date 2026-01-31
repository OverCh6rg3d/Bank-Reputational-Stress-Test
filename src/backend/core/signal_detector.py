"""
Signal Detection Engine for the Reputational Stress-Test Simulator.

This module is the "eye" of the system - it monitors the synthetic social stream
for anomalies and clusters related signals together.

Key Features:
1. Embedding-based clustering (DBSCAN) to group related signals
2. Velocity calculation (signals/hour) with anomaly detection
3. LLM-powered classification into risk categories
4. Confidence scoring with uncertainty quantification
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

import numpy as np
from sklearn.cluster import DBSCAN

# Use TYPE_CHECKING to avoid circular import at runtime
if TYPE_CHECKING:
    from backend.data.data_loader import DataLoader

from backend.models.schemas import (
    SignalCategory,
    SignalCluster,
    SeverityLevel,
    SocialSignal,
)
from backend.core.llm_client import get_llm_client, SYSTEM_PROMPTS

logger = logging.getLogger(__name__)


class SignalDetector:
    """
    Monitors synthetic social stream for anomalies.
    
    Workflow:
    1. Load signals within time window
    2. Generate embeddings for all signals
    3. Cluster using DBSCAN
    4. For each cluster, calculate velocity and classify
    5. Return detected clusters with severity scores
    """

    def __init__(
        self,
        eps: float = 0.3,  # DBSCAN epsilon (similarity threshold)
        min_samples: int = 3,  # Minimum signals to form a cluster
        velocity_window_hours: int = 1,  # Window for velocity calculation
    ):
        self.eps = eps
        self.min_samples = min_samples
        self.velocity_window_hours = velocity_window_hours
        
        # Lazy import to avoid circular import
        from backend.data.data_loader import get_data_loader
        self.data_loader = get_data_loader()
        self.llm = get_llm_client()

        logger.info(f"SignalDetector initialized (eps={eps}, min_samples={min_samples})")

    def detect_clusters(
        self,
        signals: Optional[list[SocialSignal]] = None,
        time_window_hours: int = 24,
    ) -> list[SignalCluster]:
        """
        Main detection pipeline.
        
        Args:
            signals: Optional list of signals. If None, loads from dataset.
            time_window_hours: How far back to look for signals.
            
        Returns:
            List of detected signal clusters with severity and classification.
        """
        # Load signals if not provided
        if signals is None:
            all_signals = self.data_loader.load_signals()
            # Filter to recent signals (simulated time window)
            cutoff = datetime.now() - timedelta(hours=time_window_hours)
            signals = [s for s in all_signals if s.timestamp >= cutoff]
            
            # If no recent signals, use latest N signals for demo
            if len(signals) < 10:
                signals = all_signals[:500]  # Use first 500 for demo

        if len(signals) < self.min_samples:
            logger.warning(f"Not enough signals ({len(signals)}) for clustering")
            return []

        logger.info(f"Processing {len(signals)} signals for clustering...")

        # Step 1: Generate embeddings
        embeddings = self.data_loader.embed_signals(signals)
        embeddings_array = np.array(embeddings)

        # Step 2: Cluster with DBSCAN
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="cosine")
        labels = clustering.fit_predict(embeddings_array)

        # Step 3: Group signals by cluster
        clusters_dict: dict[int, list[SocialSignal]] = defaultdict(list)
        for i, label in enumerate(labels):
            if label != -1:  # -1 is noise
                clusters_dict[label].append(signals[i])

        logger.info(f"Found {len(clusters_dict)} clusters (excluded {sum(1 for l in labels if l == -1)} noise signals)")

        # Step 4: Analyze each cluster
        detected_clusters = []
        for cluster_label, cluster_signals in clusters_dict.items():
            cluster = self._analyze_cluster(cluster_signals)
            if cluster:
                detected_clusters.append(cluster)

        # Sort by severity (Critical first)
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.POSITIVE: 4,
        }
        detected_clusters.sort(key=lambda c: severity_order.get(c.detected_severity, 5))

        return detected_clusters

    def _analyze_cluster(self, signals: list[SocialSignal]) -> Optional[SignalCluster]:
        """
        Analyze a single cluster of signals.
        
        Returns SignalCluster with:
        - Primary category (most common ground truth category)
        - Severity level (based on velocity and sentiment)
        - AI summary and confidence
        """
        if not signals:
            return None

        cluster_id = uuid4()
        signal_ids = [s.signal_id for s in signals]

        # Calculate cluster statistics
        categories = [s.gt_category for s in signals]
        sentiments = [s.gt_sentiment for s in signals]
        virality_scores = [s.gt_virality_potential for s in signals]

        # Primary category = most common
        primary_category = max(set(categories), key=categories.count)
        avg_sentiment = np.mean(sentiments)
        avg_virality = np.mean(virality_scores)
        max_virality = max(virality_scores)

        # Determine severity based on metrics
        severity = self._calculate_severity(
            avg_sentiment=avg_sentiment,
            avg_virality=avg_virality,
            signal_count=len(signals),
            category=primary_category,
        )

        # Check for misinformation
        misinformation_count = sum(1 for s in signals if s.gt_is_misinformation)
        has_misinformation = misinformation_count > len(signals) * 0.3  # >30% are misinfo

        # Get AI classification and summary
        ai_result = self._classify_cluster_with_llm(signals, primary_category)

        # Get supporting facts from knowledge base if potential misinfo
        supporting_facts = []
        if has_misinformation or severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            sample_text = signals[0].content_text[:500]
            kb_results = self.data_loader.query_knowledge_base(sample_text, n_results=3)
            supporting_facts = [r["fact"] for r in kb_results if r["relevance"] > 0.5]

        return SignalCluster(
            cluster_id=cluster_id,
            signals=signal_ids,
            primary_category=primary_category,
            detected_severity=severity,
            confidence_score=ai_result.get("confidence", 0.75),
            ai_summary=ai_result.get("summary", "Cluster detected"),
            key_themes=ai_result.get("themes", []),
            detected_misinformation=has_misinformation,
            supporting_facts=supporting_facts,
        )

    def _calculate_severity(
        self,
        avg_sentiment: float,
        avg_virality: float,
        signal_count: int,
        category: SignalCategory,
    ) -> SeverityLevel:
        """
        Calculate severity based on multiple factors.
        
        Factors:
        - Sentiment (-1 to 1, more negative = higher severity)
        - Virality potential (0-100)
        - Volume of signals
        - Category (Fraud rumors are more severe)
        """
        score = 0

        # Sentiment contribution (negative = higher score)
        score += (1 - avg_sentiment) * 25  # -1 sentiment = +50, +1 = 0

        # Virality contribution
        score += avg_virality * 0.3  # Max +30

        # Volume contribution
        if signal_count > 50:
            score += 15
        elif signal_count > 20:
            score += 10
        elif signal_count > 10:
            score += 5

        # Category bonus
        if category == SignalCategory.FRAUD_RUMOR:
            score += 20

        # Map to severity
        if score >= 70:
            return SeverityLevel.CRITICAL
        elif score >= 50:
            return SeverityLevel.HIGH
        elif score >= 30:
            return SeverityLevel.MEDIUM
        elif score >= 10:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.POSITIVE

    def _classify_cluster_with_llm(
        self, signals: list[SocialSignal], ground_truth_category: SignalCategory
    ) -> dict:
        """
        Use LLM to generate a summary and themes for the cluster.
        """
        # Sample up to 5 signals for the prompt
        sample_signals = signals[:5]
        signal_texts = "\n\n".join([
            f"[{s.platform_source.value}] {s.content_text[:300]}..."
            for s in sample_signals
        ])

        prompt = f"""Analyze this cluster of {len(signals)} related social media signals about Mashreq Bank:

SAMPLE SIGNALS:
{signal_texts}

Provide:
1. A 2-3 sentence summary of what this cluster is about
2. 3-5 key themes/topics mentioned
3. Your confidence (0-1) that this is a genuine risk vs noise
4. The likely root cause

Format your response as JSON:
{{
    "summary": "...",
    "themes": ["theme1", "theme2", ...],
    "confidence": 0.XX,
    "likely_cause": "..."
}}"""

        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPTS["signal_classifier"],
                temperature=0.3,
            )
            return result
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return {
                "summary": f"Cluster of {len(signals)} signals related to {ground_truth_category.value}",
                "themes": [],
                "confidence": 0.5,
            }

    def calculate_velocity(
        self,
        signals: list[SocialSignal],
        window_hours: int = 1,
    ) -> float:
        """
        Calculate the velocity of signals (signals per hour).
        
        This is a key metric for the "Velocity of Contagion" feature.
        """
        if not signals:
            return 0.0

        # Sort by timestamp
        sorted_signals = sorted(signals, key=lambda s: s.timestamp)
        
        # Get time span
        earliest = sorted_signals[0].timestamp
        latest = sorted_signals[-1].timestamp
        
        span_hours = (latest - earliest).total_seconds() / 3600
        if span_hours == 0:
            span_hours = 1  # Avoid division by zero
            
        velocity = len(signals) / max(span_hours, window_hours)
        return round(velocity, 2)

    def detect_velocity_anomaly(
        self,
        current_velocity: float,
        baseline_velocity: float = 10.0,
        threshold_multiplier: float = 3.0,
    ) -> tuple[bool, float]:
        """
        Detect if current velocity is anomalously high.
        
        Returns:
            (is_anomaly, spike_percentage)
        """
        if baseline_velocity == 0:
            baseline_velocity = 1

        spike = (current_velocity - baseline_velocity) / baseline_velocity * 100
        is_anomaly = current_velocity > baseline_velocity * threshold_multiplier

        return is_anomaly, round(spike, 1)


class RAGFactChecker:
    """
    RAG-based fact-checker using the bank knowledge base.
    
    Used to verify claims in social signals against official facts.
    """

    def __init__(self):
        # Lazy import to avoid circular import
        from backend.data.data_loader import get_data_loader
        self.data_loader = get_data_loader()
        self.llm = get_llm_client()
        
        # Initialize knowledge base
        self.data_loader.init_knowledge_base_rag()

    def check_claim(self, claim: str) -> dict:
        """
        Check a claim against the knowledge base.
        
        Returns:
            {
                "is_misinformation": bool,
                "confidence": float,
                "supporting_facts": [str],
                "reasoning": str
            }
        """
        # Query knowledge base
        relevant_facts = self.data_loader.query_knowledge_base(claim, n_results=5)
        
        if not relevant_facts:
            return {
                "is_misinformation": None,  # Unknown
                "confidence": 0.3,
                "supporting_facts": [],
                "reasoning": "No relevant facts found in knowledge base",
            }

        # Format facts for LLM
        facts_text = "\n".join([
            f"- {r['fact']} (Topic: {r['topic']}, Relevance: {r['relevance']:.2f})"
            for r in relevant_facts
        ])

        prompt = f"""Analyze whether this claim contains misinformation by comparing to official bank facts.

CLAIM:
"{claim}"

OFFICIAL BANK FACTS:
{facts_text}

Determine:
1. Is this claim misinformation? (true/false/uncertain)
2. Your confidence (0-1)
3. Reasoning

Format as JSON:
{{
    "is_misinformation": true/false/null,
    "confidence": 0.XX,
    "reasoning": "..."
}}"""

        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system_prompt="You are a fact-checker for Mashreq Bank. Compare claims against official facts.",
                temperature=0.2,
            )
            result["supporting_facts"] = [r["fact"] for r in relevant_facts[:3]]
            return result
        except Exception as e:
            logger.error(f"Fact-check failed: {e}")
            return {
                "is_misinformation": None,
                "confidence": 0.5,
                "supporting_facts": [],
                "reasoning": "Error during fact-check",
            }

    def batch_check(self, claims: list[str]) -> list[dict]:
        """Check multiple claims efficiently."""
        return [self.check_claim(claim) for claim in claims]
