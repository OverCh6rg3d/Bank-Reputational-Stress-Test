"""
Explainability Layer module.

Generates human-readable explanations for AI predictions and recommendations.
Provides feature attribution, reasoning traces, and decision breakdowns.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4
import re
import logging

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.schemas import SignalCategory, SeverityLevel


@dataclass
class FeatureContribution:
    """A single feature's contribution to a prediction."""
    
    feature_name: str
    feature_value: Any
    contribution_weight: float  # -1 to 1, positive = increases prediction
    explanation: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature_name,
            "value": str(self.feature_value),
            "weight": self.contribution_weight,
            "explanation": self.explanation,
        }


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    
    step_number: int
    action: str
    observation: str
    conclusion: str
    confidence_delta: float  # How much this step changed confidence
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step_number,
            "action": self.action,
            "observation": self.observation,
            "conclusion": self.conclusion,
            "confidence_change": self.confidence_delta,
        }
    
    def __str__(self) -> str:
        return f"Step {self.step_number}: {self.action} → {self.conclusion}"


@dataclass
class Explanation:
    """Complete explanation for an AI prediction or decision."""
    
    explanation_id: UUID
    timestamp: datetime
    prediction_type: str  # "classification", "simulation", "recommendation"
    summary: str
    confidence: float
    calibrated_confidence: Optional[float]
    
    feature_contributions: list[FeatureContribution] = field(default_factory=list)
    reasoning_chain: list[ReasoningStep] = field(default_factory=list)
    
    key_factors: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)
    uncertainty_sources: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "explanation_id": str(self.explanation_id),
            "timestamp": self.timestamp.isoformat(),
            "type": self.prediction_type,
            "summary": self.summary,
            "confidence": self.confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "features": [f.to_dict() for f in self.feature_contributions],
            "reasoning": [r.to_dict() for r in self.reasoning_chain],
            "key_factors": self.key_factors,
            "counter_evidence": self.counter_evidence,
            "uncertainty_sources": self.uncertainty_sources,
        }
    
    def to_natural_language(self) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"**{self.summary}**",
            f"",
            f"Confidence: {self.confidence:.0%}" + (
                f" (calibrated: {self.calibrated_confidence:.0%})" 
                if self.calibrated_confidence else ""
            ),
            f"",
        ]
        
        if self.key_factors:
            lines.append("**Key Factors:**")
            for factor in self.key_factors[:5]:
                lines.append(f"• {factor}")
            lines.append("")
        
        if self.feature_contributions:
            lines.append("**Feature Contributions:**")
            sorted_features = sorted(
                self.feature_contributions, 
                key=lambda f: abs(f.contribution_weight), 
                reverse=True
            )
            for feat in sorted_features[:5]:
                direction = "↑" if feat.contribution_weight > 0 else "↓"
                lines.append(f"• {feat.feature_name}: {feat.explanation} {direction}")
            lines.append("")
        
        if self.counter_evidence:
            lines.append("**Counter-Evidence to Consider:**")
            for evidence in self.counter_evidence[:3]:
                lines.append(f"⚠️ {evidence}")
            lines.append("")
        
        if self.uncertainty_sources:
            lines.append("**Sources of Uncertainty:**")
            for source in self.uncertainty_sources[:3]:
                lines.append(f"❓ {source}")
        
        return "\n".join(lines)


class ClassificationExplainer:
    """
    Generates explanations for signal classification predictions.
    
    Analyzes signal content to identify which features contributed
    to the category prediction.
    """
    
    # Feature patterns for different categories (using actual SignalCategory values)
    CATEGORY_PATTERNS = {
        SignalCategory.FRAUD_RUMOR: {
            "keywords": ["hack", "breach", "stolen", "scam", "fraud", "OTP", "phishing"],
            "explain": "contains fraud-related terminology",
        },
        SignalCategory.SERVICE_OUTAGE: {
            "keywords": ["down", "outage", "error", "not working", "can't access", "unavailable"],
            "explain": "mentions service availability issues",
        },
        SignalCategory.COMPETITOR_NEWS: {
            "keywords": ["competitor", "rival", "better than", "switching to", "alternative"],
            "explain": "mentions competitor activity",
        },
        SignalCategory.POSITIVE_NEUTRAL: {
            "keywords": ["great", "love", "excellent", "best", "happy", "satisfied"],
            "explain": "contains positive or neutral sentiment",
        },
        SignalCategory.IRRELEVANT: {
            "keywords": [],
            "explain": "does not match any specific category patterns",
        },
    }
    
    def explain(
        self,
        signal_content: str,
        predicted_category: SignalCategory,
        confidence: float,
        sentiment: Optional[float] = None,
        virality: Optional[float] = None,
    ) -> Explanation:
        """
        Generate explanation for a classification prediction.
        
        Args:
            signal_content: Text content of the signal
            predicted_category: Predicted category
            confidence: Prediction confidence
            sentiment: Optional sentiment score
            virality: Optional virality score
        
        Returns:
            Complete Explanation object
        """
        features = []
        key_factors = []
        reasoning_steps = []
        
        # Step 1: Keyword analysis
        content_lower = signal_content.lower()
        patterns = self.CATEGORY_PATTERNS.get(predicted_category, {})
        keywords = patterns.get("keywords", [])
        
        matched_keywords = [kw for kw in keywords if kw.lower() in content_lower]
        if matched_keywords:
            features.append(FeatureContribution(
                feature_name="keyword_match",
                feature_value=matched_keywords,
                contribution_weight=0.35,
                explanation=f"Signal {patterns.get('explain', 'matches category patterns')}",
            ))
            key_factors.append(f"Keywords detected: {', '.join(matched_keywords[:3])}")
            
            reasoning_steps.append(ReasoningStep(
                step_number=1,
                action="Keyword Analysis",
                observation=f"Found {len(matched_keywords)} category-specific keywords",
                conclusion=f"Content aligns with {predicted_category.value} pattern",
                confidence_delta=0.15,
            ))
        
        # Step 2: Sentiment analysis
        if sentiment is not None:
            sentiment_contribution = -sentiment * 0.2  # Negative sentiment increases risk
            features.append(FeatureContribution(
                feature_name="sentiment",
                feature_value=f"{sentiment:.2f}",
                contribution_weight=sentiment_contribution,
                explanation=f"{'Negative' if sentiment < 0 else 'Positive'} tone detected",
            ))
            
            if sentiment < -0.5:
                key_factors.append("Strong negative sentiment amplifies concern")
                reasoning_steps.append(ReasoningStep(
                    step_number=2,
                    action="Sentiment Analysis",
                    observation=f"Sentiment score: {sentiment:.2f} (negative)",
                    conclusion="Emotional tone increases risk perception",
                    confidence_delta=0.1,
                ))
        
        # Step 3: Virality potential
        if virality is not None:
            virality_normalized = virality / 100
            features.append(FeatureContribution(
                feature_name="virality_potential",
                feature_value=f"{virality:.0f}%",
                contribution_weight=virality_normalized * 0.25,
                explanation=f"{'High' if virality > 70 else 'Moderate' if virality > 40 else 'Low'} spread potential",
            ))
            
            if virality > 70:
                key_factors.append(f"High virality potential ({virality:.0f}%) increases urgency")
                reasoning_steps.append(ReasoningStep(
                    step_number=3,
                    action="Virality Assessment",
                    observation=f"Predicted reach: {virality:.0f}%",
                    conclusion="High potential for rapid spread",
                    confidence_delta=0.05,
                ))
        
        # Step 4: Content length heuristic
        word_count = len(signal_content.split())
        features.append(FeatureContribution(
            feature_name="content_length",
            feature_value=word_count,
            contribution_weight=0.05 if word_count > 20 else -0.05,
            explanation="Longer content provides more context" if word_count > 20 else "Brief content may lack context",
        ))
        
        # Generate uncertainty sources
        uncertainty_sources = []
        if confidence < 0.7:
            uncertainty_sources.append("Moderate confidence suggests ambiguous signal content")
        if not matched_keywords:
            uncertainty_sources.append("No strong keyword matches for this category")
        if sentiment is None:
            uncertainty_sources.append("Sentiment analysis not available")
        
        # Generate counter-evidence
        counter_evidence = []
        for other_cat, other_patterns in self.CATEGORY_PATTERNS.items():
            if other_cat != predicted_category:
                other_keywords = other_patterns.get("keywords", [])
                other_matches = [kw for kw in other_keywords if kw.lower() in content_lower]
                if other_matches:
                    counter_evidence.append(
                        f"Also matches {other_cat.value} keywords: {', '.join(other_matches[:2])}"
                    )
        
        # Build summary
        summary = f"Classified as {predicted_category.value}"
        if key_factors:
            summary += f" based on {key_factors[0].lower()}"
        
        return Explanation(
            explanation_id=uuid4(),
            timestamp=datetime.now(),
            prediction_type="classification",
            summary=summary,
            confidence=confidence,
            calibrated_confidence=None,
            feature_contributions=features,
            reasoning_chain=reasoning_steps,
            key_factors=key_factors,
            counter_evidence=counter_evidence[:3],
            uncertainty_sources=uncertainty_sources,
        )


class SeverityExplainer:
    """
    Generates explanations for severity level predictions.
    """
    
    def explain(
        self,
        category: SignalCategory,
        sentiment: float,
        virality: float,
        signal_count: int,
        predicted_severity: SeverityLevel,
        confidence: float,
    ) -> Explanation:
        """Generate explanation for severity prediction."""
        features = []
        key_factors = []
        reasoning_steps = []
        
        # Score calculation (mirrors actual severity logic)
        score = 0
        
        # Sentiment contribution
        sentiment_score = (1 - sentiment) * 25
        score += sentiment_score
        features.append(FeatureContribution(
            feature_name="sentiment_impact",
            feature_value=f"{sentiment:.2f}",
            contribution_weight=sentiment_score / 100,
            explanation=f"Sentiment contributes {sentiment_score:.1f} points to severity",
        ))
        
        if sentiment < -0.5:
            key_factors.append("Strong negative sentiment increases severity")
            reasoning_steps.append(ReasoningStep(
                step_number=1,
                action="Sentiment Impact Assessment",
                observation=f"Sentiment {sentiment:.2f} is highly negative",
                conclusion=f"Added {sentiment_score:.0f} points to severity score",
                confidence_delta=0.1,
            ))
        
        # Virality contribution
        virality_score = virality * 0.3
        score += virality_score
        features.append(FeatureContribution(
            feature_name="virality_impact",
            feature_value=f"{virality:.0f}%",
            contribution_weight=virality_score / 100,
            explanation=f"Virality potential adds {virality_score:.1f} points",
        ))
        
        if virality > 70:
            key_factors.append("High viral potential escalates severity")
            reasoning_steps.append(ReasoningStep(
                step_number=2,
                action="Virality Scale Assessment",
                observation=f"Virality score {virality:.0f}% is high",
                conclusion=f"Added {virality_score:.0f} points to severity",
                confidence_delta=0.08,
            ))
        
        # Signal count contribution
        if signal_count > 50:
            count_bonus = 15
            score += count_bonus
            key_factors.append(f"High signal volume ({signal_count}) indicates widespread discussion")
            features.append(FeatureContribution(
                feature_name="signal_volume",
                feature_value=signal_count,
                contribution_weight=0.15,
                explanation="High volume suggests significant attention",
            ))
        
        # Category contribution
        if category == SignalCategory.FRAUD_RUMOR:
            category_bonus = 20
            score += category_bonus
            key_factors.append("Fraud-related content triggers elevated severity")
            features.append(FeatureContribution(
                feature_name="category_weight",
                feature_value=category.value,
                contribution_weight=0.2,
                explanation="Fraud rumors carry inherent high risk",
            ))
        
        # Determine severity from score
        if score >= 70:
            threshold_msg = "Score ≥70 triggers CRITICAL"
        elif score >= 50:
            threshold_msg = "Score ≥50 triggers HIGH"
        elif score >= 30:
            threshold_msg = "Score ≥30 triggers MEDIUM"
        else:
            threshold_msg = "Score <30 results in LOW"
        
        reasoning_steps.append(ReasoningStep(
            step_number=len(reasoning_steps) + 1,
            action="Threshold Evaluation",
            observation=f"Total severity score: {score:.0f}",
            conclusion=threshold_msg,
            confidence_delta=0.0,
        ))
        
        summary = f"Severity assessed as {predicted_severity.value} (score: {score:.0f})"
        
        return Explanation(
            explanation_id=uuid4(),
            timestamp=datetime.now(),
            prediction_type="severity",
            summary=summary,
            confidence=confidence,
            calibrated_confidence=None,
            feature_contributions=features,
            reasoning_chain=reasoning_steps,
            key_factors=key_factors,
            counter_evidence=[],
            uncertainty_sources=[
                "Severity thresholds are configurable and may need tuning",
            ] if confidence < 0.8 else [],
        )


class VoCExplainer:
    """
    Generates explanations for Velocity of Contagion predictions.
    """
    
    def explain(
        self,
        voc_score: float,
        peak_hour: float,
        total_reach: int,
        agent_breakdown: Optional[dict[str, int]] = None,
    ) -> Explanation:
        """Generate explanation for VoC simulation results."""
        features = []
        key_factors = []
        reasoning_steps = []
        
        # VoC interpretation
        if voc_score > 80:
            voc_level = "extremely rapid"
            key_factors.append("CRITICAL: Viral spread pattern detected")
        elif voc_score > 60:
            voc_level = "rapid"
            key_factors.append("High velocity spread expected")
        elif voc_score > 40:
            voc_level = "moderate"
            key_factors.append("Moderate spread velocity observed")
        else:
            voc_level = "slow"
            key_factors.append("Spread velocity within normal parameters")
        
        features.append(FeatureContribution(
            feature_name="velocity_score",
            feature_value=f"{voc_score:.0f}",
            contribution_weight=voc_score / 100,
            explanation=f"Contagion velocity is {voc_level}",
        ))
        
        reasoning_steps.append(ReasoningStep(
            step_number=1,
            action="Velocity Analysis",
            observation=f"VoC score: {voc_score:.0f}/100",
            conclusion=f"Classified as {voc_level} spread",
            confidence_delta=0.2,
        ))
        
        # Peak timing
        if peak_hour < 6:
            timing_msg = "Early peak suggests rapid escalation"
        elif peak_hour < 12:
            timing_msg = "Peak within first half-day is concerning"
        else:
            timing_msg = "Later peak allows time for response"
        
        features.append(FeatureContribution(
            feature_name="peak_timing",
            feature_value=f"Hour {peak_hour:.0f}",
            contribution_weight=(24 - peak_hour) / 24 * 0.3,
            explanation=timing_msg,
        ))
        
        key_factors.append(f"Peak velocity expected at hour {peak_hour:.0f}")
        
        # Reach analysis
        if total_reach > 10000:
            reach_level = "mass"
        elif total_reach > 1000:
            reach_level = "significant"
        else:
            reach_level = "limited"
        
        features.append(FeatureContribution(
            feature_name="predicted_reach",
            feature_value=f"{total_reach:,}",
            contribution_weight=min(1.0, total_reach / 10000) * 0.25,
            explanation=f"{reach_level.title()} audience exposure predicted",
        ))
        
        key_factors.append(f"Estimated reach: {total_reach:,} individuals")
        
        # Agent breakdown if available
        if agent_breakdown:
            reasoning_steps.append(ReasoningStep(
                step_number=2,
                action="Agent Analysis",
                observation=f"Agent actions: {agent_breakdown}",
                conclusion="Network effects analyzed",
                confidence_delta=0.1,
            ))
        
        summary = f"VoC prediction: {voc_score:.0f}/100 ({voc_level} spread)"
        
        return Explanation(
            explanation_id=uuid4(),
            timestamp=datetime.now(),
            prediction_type="simulation",
            summary=summary,
            confidence=0.75,  # Simulations inherently have uncertainty
            calibrated_confidence=None,
            feature_contributions=features,
            reasoning_chain=reasoning_steps,
            key_factors=key_factors,
            counter_evidence=[
                "Real-world spread may differ from simulation",
                "External factors not modeled may influence outcome",
            ],
            uncertainty_sources=[
                "Monte Carlo simulation has inherent randomness",
                "Agent behavior is probabilistic",
            ],
        )


class ExplanationGenerator:
    """
    Main interface for generating explanations.
    
    Provides a unified API for explaining different types of predictions.
    """
    
    def __init__(self):
        self.classification_explainer = ClassificationExplainer()
        self.severity_explainer = SeverityExplainer()
        self.voc_explainer = VoCExplainer()
    
    def explain_classification(
        self,
        signal_content: str,
        predicted_category: SignalCategory,
        confidence: float,
        **kwargs
    ) -> Explanation:
        """Generate explanation for classification."""
        return self.classification_explainer.explain(
            signal_content, predicted_category, confidence, **kwargs
        )
    
    def explain_severity(
        self,
        category: SignalCategory,
        sentiment: float,
        virality: float,
        signal_count: int,
        predicted_severity: SeverityLevel,
        confidence: float,
    ) -> Explanation:
        """Generate explanation for severity."""
        return self.severity_explainer.explain(
            category, sentiment, virality, signal_count, predicted_severity, confidence
        )
    
    def explain_voc(
        self,
        voc_score: float,
        peak_hour: float,
        total_reach: int,
        **kwargs
    ) -> Explanation:
        """Generate explanation for VoC simulation."""
        return self.voc_explainer.explain(voc_score, peak_hour, total_reach, **kwargs)


# Module-level singleton
_explainer: Optional[ExplanationGenerator] = None


def get_explainer() -> ExplanationGenerator:
    """Get the global explanation generator singleton."""
    global _explainer
    if _explainer is None:
        _explainer = ExplanationGenerator()
    return _explainer
