"""
Unit tests for the Governance module.

Tests guardrail enforcement, confidence thresholds, and audit logging.
"""

import pytest
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.models.schemas import (
    DetectedIncident,
    HumanAction,
    IncidentStatus,
    ResponseRecommendation,
    SeverityLevel,
)
from backend.core.governance import (
    DEFAULT_GUARDRAILS,
    GovernanceGate,
    GovernanceResult,
    GuardrailViolation,
)


class TestGuardrailEnforcement:
    """Tests for hard guardrail enforcement."""
    
    @pytest.fixture
    def governance_gate(self):
        """Create governance gate with default config."""
        return GovernanceGate()
    
    @pytest.fixture
    def sample_incident(self):
        """Create a sample incident."""
        return DetectedIncident(
            incident_id=uuid4(),
            related_scenario_id=uuid4(),
            detected_severity=SeverityLevel.HIGH,
            status=IncidentStatus.PENDING_REVIEW,
            confidence_score=0.85,
            ai_analysis="Test analysis",
            proposed_response="Test response",
        )
    
    def test_blocks_public_posting_recommendation(self, governance_gate, sample_incident):
        """Test that recommendations to post publicly are blocked."""
        recommendation = ResponseRecommendation(
            recommendation_id=uuid4(),
            cluster_id=uuid4(),
            action_summary="Post a public tweet to clarify",
            detailed_steps=["Draft tweet", "Post to Twitter"],
            reasoning="Quick clarification",
            expected_impact="Reduce confusion",
            confidence_score=0.8,
        )
        
        result = governance_gate.check_recommendation(recommendation, sample_incident)
        
        # Should have violation and be blocked
        assert len(result.violations) > 0
        assert any(v.guardrail_id == "no_public_action" for v in result.violations)
        assert not result.passed
    
    def test_allows_internal_recommendation(self, governance_gate, sample_incident):
        """Test that internal-only recommendations are allowed."""
        recommendation = ResponseRecommendation(
            recommendation_id=uuid4(),
            cluster_id=uuid4(),
            action_summary="Prepare internal briefing for leadership",
            detailed_steps=["Draft briefing", "Send to CISO"],
            reasoning="Need leadership awareness",
            expected_impact="Coordinated response",
            confidence_score=0.9,
        )
        
        result = governance_gate.check_recommendation(recommendation, sample_incident)
        
        # Should pass (no hard blocks)
        assert result.passed
    
    def test_detects_tweet_keyword(self, governance_gate, sample_incident):
        """Test detection of 'tweet' in recommendation."""
        recommendation = ResponseRecommendation(
            recommendation_id=uuid4(),
            cluster_id=uuid4(),
            action_summary="Tweet clarification to customers",
            detailed_steps=[],
            reasoning="",
            expected_impact="",
            confidence_score=0.7,
        )
        
        result = governance_gate.check_recommendation(recommendation, sample_incident)
        assert not result.passed


class TestConfidenceThresholds:
    """Tests for confidence-based escalation."""
    
    @pytest.fixture
    def governance_gate(self):
        return GovernanceGate()
    
    def test_low_confidence_requires_review(self, governance_gate):
        """Test that low confidence triggers review requirement."""
        confidence = 0.65
        severity = SeverityLevel.MEDIUM
        
        status = governance_gate._check_confidence(confidence, severity)
        
        assert status == "low_confidence"
    
    def test_acceptable_confidence_passes(self, governance_gate):
        """Test that high confidence is acceptable."""
        confidence = 0.85
        severity = SeverityLevel.MEDIUM
        
        status = governance_gate._check_confidence(confidence, severity)
        
        assert status == "acceptable"
    
    def test_critical_severity_always_escalates(self, governance_gate):
        """Test that critical severity always triggers escalation."""
        confidence = 0.95  # High confidence
        severity = SeverityLevel.CRITICAL
        
        status = governance_gate._check_confidence(confidence, severity)
        
        assert status == "critical_escalation"


class TestSocraticQuestions:
    """Tests for Socratic review questions."""
    
    @pytest.fixture
    def governance_gate(self):
        return GovernanceGate()
    
    def test_critical_gets_all_questions(self, governance_gate):
        """Test that critical incidents get maximum questions."""
        questions = governance_gate._select_socratic_questions(
            SeverityLevel.CRITICAL, max_questions=5
        )
        
        assert len(questions) >= 3
    
    def test_low_severity_gets_fewer_questions(self, governance_gate):
        """Test that low severity gets fewer questions."""
        questions = governance_gate._select_socratic_questions(
            SeverityLevel.LOW, max_questions=5
        )
        
        assert len(questions) == 2
    
    def test_questions_are_meaningful(self, governance_gate):
        """Test that questions contain expected content."""
        questions = governance_gate._select_socratic_questions(SeverityLevel.HIGH)
        
        # Should include questions about worst case and falsification
        all_text = " ".join(questions).lower()
        assert "worst" in all_text or "evidence" in all_text


class TestAuditLogging:
    """Tests for immutable audit logging."""
    
    @pytest.fixture
    def governance_gate(self):
        return GovernanceGate()
    
    def test_log_decision_creates_entry(self, governance_gate):
        """Test that logging creates audit entry."""
        incident_id = uuid4()
        
        governance_gate.log_decision(
            incident_id=incident_id,
            action_type="TEST_ACTION",
            actor="test_user",
            details={"test": "data"},
            confidence=0.85,
        )
        
        entries = governance_gate.get_audit_trail(incident_id=incident_id)
        
        assert len(entries) == 1
        assert entries[0].action_type == "TEST_ACTION"
        assert entries[0].actor == "test_user"
        assert entries[0].confidence_at_time == 0.85
    
    def test_audit_entries_have_timestamp(self, governance_gate):
        """Test that audit entries are timestamped."""
        before = datetime.now()
        
        governance_gate.log_decision(
            incident_id=uuid4(),
            action_type="TIMESTAMP_TEST",
            actor="system",
            details={},
        )
        
        after = datetime.now()
        entries = governance_gate.get_audit_trail(limit=1)
        
        assert before <= entries[0].timestamp <= after
    
    def test_get_audit_trail_with_limit(self, governance_gate):
        """Test that audit trail respects limit."""
        # Create multiple entries
        for i in range(10):
            governance_gate.log_decision(
                incident_id=uuid4(),
                action_type=f"ACTION_{i}",
                actor="test",
                details={},
            )
        
        entries = governance_gate.get_audit_trail(limit=5)
        
        assert len(entries) == 5


class TestDefaultGuardrails:
    """Tests for default guardrails configuration."""
    
    def test_has_action_boundaries(self):
        """Test that default config has action boundaries."""
        assert "action_boundaries" in DEFAULT_GUARDRAILS
        assert len(DEFAULT_GUARDRAILS["action_boundaries"]) >= 3
    
    def test_has_confidence_thresholds(self):
        """Test that default config has confidence thresholds."""
        assert "confidence_thresholds" in DEFAULT_GUARDRAILS
        
        # Should have 70% threshold
        thresholds = [t.get("threshold") for t in DEFAULT_GUARDRAILS["confidence_thresholds"]]
        assert 0.70 in thresholds
    
    def test_has_socratic_questions(self):
        """Test that default config has Socratic questions."""
        assert "socratic_questions" in DEFAULT_GUARDRAILS
        assert len(DEFAULT_GUARDRAILS["socratic_questions"]) >= 5
    
    def test_audit_log_enabled(self):
        """Test that audit logging is enabled by default."""
        assert DEFAULT_GUARDRAILS["audit_log"]["enabled"] is True
