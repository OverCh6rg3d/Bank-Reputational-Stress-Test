"""
Governance Layer - Guardrails, Socratic review, and audit logging.

Implements the "Constitutional AI" approach with:
1. Hard constraints (zero-action protocol)
2. Confidence thresholds
3. Socratic review questions
4. Immutable audit logging
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import yaml
from pydantic import BaseModel, Field

from ..models.schemas import (
    AuditLogEntry,
    DetectedIncident,
    HumanAction,
    ResponseRecommendation,
    SeverityLevel,
)

logger = logging.getLogger(__name__)

# Default guardrails configuration
DEFAULT_GUARDRAILS = {
    "version": "1.0",
    "action_boundaries": [
        {
            "id": "no_public_action",
            "description": "System NEVER posts to public social media",
            "enforcement": "hard_block",
        },
        {
            "id": "human_approval_required", 
            "description": "All response strategies require human approval",
            "enforcement": "hard_block",
        },
        {
            "id": "no_customer_data",
            "description": "System never processes real customer PII",
            "enforcement": "hard_block",
        },
    ],
    "confidence_thresholds": [
        {
            "id": "low_confidence_escalation",
            "description": "Predictions below 70% confidence require human review",
            "threshold": 0.70,
            "action": "require_review",
        },
        {
            "id": "critical_severity_escalation",
            "description": "Critical severity always requires immediate escalation",
            "severity": "Critical",
            "action": "immediate_escalation",
        },
    ],
    "socratic_questions": [
        "What is the worst-case scenario if this prediction is wrong?",
        "What evidence would falsify this conclusion?",
        "Which demographic segments might be disproportionately affected?",
        "What are the regulatory implications of this response?",
        "Is there potential for Streisand effect if we act on this?",
    ],
    "audit_log": {
        "enabled": True,
        "retention_days": 365,
        "fields": ["timestamp", "prediction", "confidence", "human_decision", "reasoning"],
    },
}


class GuardrailViolation(BaseModel):
    """A detected guardrail violation."""
    
    guardrail_id: str
    description: str
    severity: str
    blocked: bool


class GovernanceResult(BaseModel):
    """Result of governance check."""
    
    passed: bool
    violations: list[GuardrailViolation] = Field(default_factory=list)
    requires_human_review: bool = True
    socratic_questions: list[str] = Field(default_factory=list)
    confidence_status: str = "acceptable"


class GovernanceGate:
    """
    Runtime guardrails enforcement.
    
    Validates all AI outputs before presenting to users:
    1. Checks action boundaries (hard blocks)
    2. Enforces confidence thresholds
    3. Generates Socratic review questions
    4. Logs all decisions for audit
    """

    def __init__(self, guardrails_path: Optional[Path] = None):
        """
        Initialize governance with guardrails config.
        
        Args:
            guardrails_path: Path to guardrails.yaml. Uses defaults if None.
        """
        self.guardrails = self._load_guardrails(guardrails_path)
        self.audit_log: list[AuditLogEntry] = []
        
        logger.info(f"GovernanceGate initialized with {len(self.guardrails.get('action_boundaries', []))} boundaries")

    def _load_guardrails(self, path: Optional[Path]) -> dict:
        """Load guardrails from YAML or use defaults."""
        if path and path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load guardrails: {e}, using defaults")
        
        return DEFAULT_GUARDRAILS

    def check_recommendation(
        self,
        recommendation: ResponseRecommendation,
        incident: DetectedIncident,
    ) -> GovernanceResult:
        """
        Validate a response recommendation against guardrails.
        
        Returns GovernanceResult indicating whether the recommendation
        can proceed and what human review is needed.
        """
        violations = []
        requires_review = True
        
        # Check action boundaries
        for boundary in self.guardrails.get("action_boundaries", []):
            violation = self._check_boundary(boundary, recommendation)
            if violation:
                violations.append(violation)

        # Check confidence thresholds
        confidence_status = self._check_confidence(
            recommendation.confidence_score,
            incident.detected_severity,
        )

        # Get relevant Socratic questions
        questions = self._select_socratic_questions(incident.detected_severity)

        # Determine if passed
        hard_blocks = [v for v in violations if v.blocked]
        passed = len(hard_blocks) == 0

        return GovernanceResult(
            passed=passed,
            violations=violations,
            requires_human_review=requires_review or confidence_status != "acceptable",
            socratic_questions=questions,
            confidence_status=confidence_status,
        )

    def _check_boundary(
        self,
        boundary: dict,
        recommendation: ResponseRecommendation,
    ) -> Optional[GuardrailViolation]:
        """Check if a specific boundary is violated."""
        boundary_id = boundary.get("id", "unknown")
        
        # Check for public action keywords in recommendation
        if boundary_id == "no_public_action":
            forbidden_keywords = ["post", "tweet", "reply publicly", "comment on social"]
            action_lower = recommendation.action_summary.lower()
            if any(kw in action_lower for kw in forbidden_keywords):
                return GuardrailViolation(
                    guardrail_id=boundary_id,
                    description=boundary["description"],
                    severity="critical",
                    blocked=True,
                )
        
        return None

    def _check_confidence(
        self,
        confidence: float,
        severity: SeverityLevel,
    ) -> str:
        """Check confidence against thresholds."""
        for threshold in self.guardrails.get("confidence_thresholds", []):
            if "threshold" in threshold:
                if confidence < threshold["threshold"]:
                    return "low_confidence"
            
            if "severity" in threshold:
                if severity.value == threshold["severity"]:
                    return "critical_escalation"
        
        return "acceptable"

    def _select_socratic_questions(
        self,
        severity: SeverityLevel,
        max_questions: int = 3,
    ) -> list[str]:
        """Select relevant Socratic questions based on severity."""
        all_questions = self.guardrails.get("socratic_questions", [])
        
        if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            # Return all questions for critical situations
            return all_questions[:max_questions]
        else:
            # Return subset for lower severity
            return all_questions[:2]

    def log_decision(
        self,
        incident_id: UUID,
        action_type: str,
        actor: str,
        details: dict,
        confidence: Optional[float] = None,
    ):
        """
        Log a decision to the immutable audit trail.
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            action_type=action_type,
            actor=actor,
            target_id=incident_id,
            details=details,
            confidence_at_time=confidence,
        )
        
        self.audit_log.append(entry)
        logger.info(f"Audit log: {action_type} by {actor} on {incident_id}")

    def get_audit_trail(
        self,
        incident_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Retrieve audit log entries, optionally filtered by incident."""
        if incident_id:
            return [e for e in self.audit_log if e.target_id == incident_id][:limit]
        return self.audit_log[-limit:]

    def record_human_decision(
        self,
        incident: DetectedIncident,
        decision: HumanAction,
        reviewer_id: str,
        notes: str = "",
    ):
        """Record a human's decision on an incident."""
        self.log_decision(
            incident_id=incident.incident_id,
            action_type=f"HUMAN_{decision.value.upper()}",
            actor=reviewer_id,
            details={
                "previous_status": incident.human_action.value,
                "new_status": decision.value,
                "notes": notes,
                "severity": incident.detected_severity.value,
            },
            confidence=incident.confidence_score,
        )


# Singleton instance
_governance_gate: Optional[GovernanceGate] = None


def get_governance_gate() -> GovernanceGate:
    """Get singleton governance gate instance."""
    global _governance_gate
    if _governance_gate is None:
        # Try to load from default location
        default_path = Path(__file__).parent.parent.parent.parent / "governance" / "guardrails.yaml"
        _governance_gate = GovernanceGate(default_path)
    return _governance_gate
