"""
Real-Time Alert System module.

Provides configurable alert thresholds, monitoring, and notification
capabilities for the simulation system.
"""

import sys
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import UUID, uuid4
import json
import logging

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.schemas import SeverityLevel


class AlertPriority(str, Enum):
    """Alert priority levels."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action within hours
    MEDIUM = "medium"      # Action within 24 hours
    LOW = "low"           # Informational
    INFO = "info"         # Log only


class AlertType(str, Enum):
    """Types of alerts."""
    VOC_SPIKE = "voc_spike"
    SEVERITY_CRITICAL = "severity_critical"
    CLUSTER_DETECTED = "cluster_detected"
    VELOCITY_ANOMALY = "velocity_anomaly"
    MISINFORMATION_DETECTED = "misinformation_detected"
    GOVERNANCE_VIOLATION = "governance_violation"
    SIMULATION_COMPLETE = "simulation_complete"
    REVIEW_REQUIRED = "review_required"


class AlertStatus(str, Enum):
    """Alert lifecycle status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class AlertThreshold:
    """Configuration for an alert threshold."""
    
    alert_type: AlertType
    metric_name: str
    threshold_value: float
    comparison: str  # "gt", "lt", "gte", "lte", "eq"
    priority: AlertPriority
    enabled: bool = True
    cooldown_minutes: int = 15  # Prevent duplicate alerts
    
    def check(self, value: float) -> bool:
        """Check if value triggers this threshold."""
        if not self.enabled:
            return False
        
        ops = {
            "gt": lambda v, t: v > t,
            "lt": lambda v, t: v < t,
            "gte": lambda v, t: v >= t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: abs(v - t) < 0.001,
        }
        
        return ops.get(self.comparison, lambda v, t: False)(value, self.threshold_value)


@dataclass
class Alert:
    """A single alert instance."""
    
    alert_id: UUID
    alert_type: AlertType
    priority: AlertPriority
    status: AlertStatus
    
    title: str
    message: str
    timestamp: datetime
    
    source_id: Optional[UUID] = None  # ID of cluster, signal, etc.
    metadata: dict[str, Any] = field(default_factory=dict)
    
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": str(self.alert_id),
            "type": self.alert_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "source_id": str(self.source_id) if self.source_id else None,
            "metadata": self.metadata,
        }
    
    def acknowledge(self, user: str) -> None:
        """Mark alert as acknowledged."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user
    
    def resolve(self, user: str) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolved_by = user


class AlertConfig:
    """
    Alert system configuration.
    
    Defines thresholds and rules for when alerts should be triggered.
    """
    
    def __init__(self):
        self.thresholds: list[AlertThreshold] = []
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default alert thresholds."""
        self.thresholds = [
            # VoC thresholds
            AlertThreshold(
                alert_type=AlertType.VOC_SPIKE,
                metric_name="voc_score",
                threshold_value=80,
                comparison="gte",
                priority=AlertPriority.CRITICAL,
            ),
            AlertThreshold(
                alert_type=AlertType.VOC_SPIKE,
                metric_name="voc_score",
                threshold_value=60,
                comparison="gte",
                priority=AlertPriority.HIGH,
            ),
            
            # Velocity anomaly
            AlertThreshold(
                alert_type=AlertType.VELOCITY_ANOMALY,
                metric_name="velocity_ratio",  # Current / baseline
                threshold_value=3.0,
                comparison="gte",
                priority=AlertPriority.HIGH,
            ),
            
            # Cluster detection
            AlertThreshold(
                alert_type=AlertType.CLUSTER_DETECTED,
                metric_name="cluster_size",
                threshold_value=50,
                comparison="gte",
                priority=AlertPriority.MEDIUM,
            ),
            
            # Misinformation
            AlertThreshold(
                alert_type=AlertType.MISINFORMATION_DETECTED,
                metric_name="misinfo_confidence",
                threshold_value=0.8,
                comparison="gte",
                priority=AlertPriority.HIGH,
            ),
        ]
    
    def add_threshold(self, threshold: AlertThreshold) -> None:
        """Add a custom threshold."""
        self.thresholds.append(threshold)
    
    def get_thresholds_for_type(self, alert_type: AlertType) -> list[AlertThreshold]:
        """Get all thresholds for a specific alert type."""
        return [t for t in self.thresholds if t.alert_type == alert_type]
    
    def to_dict(self) -> dict[str, Any]:
        """Export configuration."""
        return {
            "thresholds": [
                {
                    "type": t.alert_type.value,
                    "metric": t.metric_name,
                    "value": t.threshold_value,
                    "comparison": t.comparison,
                    "priority": t.priority.value,
                    "enabled": t.enabled,
                    "cooldown_minutes": t.cooldown_minutes,
                }
                for t in self.thresholds
            ]
        }


class AlertSubscriber:
    """Base class for alert subscribers (WebSocket, email, etc.)."""
    
    async def notify(self, alert: Alert) -> bool:
        """Send notification for an alert. Returns True if successful."""
        raise NotImplementedError


class WebSocketSubscriber(AlertSubscriber):
    """Sends alerts to connected WebSocket clients."""
    
    def __init__(self):
        self.connections: list[Any] = []  # WebSocket connections
    
    def add_connection(self, ws) -> None:
        """Add a WebSocket connection."""
        self.connections.append(ws)
    
    def remove_connection(self, ws) -> None:
        """Remove a WebSocket connection."""
        if ws in self.connections:
            self.connections.remove(ws)
    
    async def notify(self, alert: Alert) -> bool:
        """Send alert to all connected WebSocket clients."""
        if not self.connections:
            return False
        
        message = json.dumps({
            "type": "alert",
            "data": alert.to_dict(),
        })
        
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.remove_connection(ws)
        
        return len(self.connections) > len(disconnected)


class LogSubscriber(AlertSubscriber):
    """Logs alerts to the logging system."""
    
    async def notify(self, alert: Alert) -> bool:
        log_level = {
            AlertPriority.CRITICAL: logging.CRITICAL,
            AlertPriority.HIGH: logging.ERROR,
            AlertPriority.MEDIUM: logging.WARNING,
            AlertPriority.LOW: logging.INFO,
            AlertPriority.INFO: logging.DEBUG,
        }.get(alert.priority, logging.INFO)
        
        logger.log(
            log_level,
            f"[ALERT] {alert.priority.value.upper()}: {alert.title} - {alert.message}"
        )
        return True


class AlertManager:
    """
    Central alert management system.
    
    Monitors metrics, triggers alerts based on thresholds,
    and distributes notifications to subscribers.
    """
    
    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig()
        self.alerts: list[Alert] = []
        self.subscribers: list[AlertSubscriber] = [LogSubscriber()]
        self._cooldowns: dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    def add_subscriber(self, subscriber: AlertSubscriber) -> None:
        """Add a notification subscriber."""
        self.subscribers.append(subscriber)
    
    def _is_on_cooldown(self, alert_type: AlertType, source_id: Optional[UUID]) -> bool:
        """Check if an alert type is on cooldown."""
        key = f"{alert_type.value}:{source_id or 'global'}"
        if key in self._cooldowns:
            threshold = self.config.get_thresholds_for_type(alert_type)
            cooldown_mins = threshold[0].cooldown_minutes if threshold else 15
            if datetime.now() - self._cooldowns[key] < timedelta(minutes=cooldown_mins):
                return True
        return False
    
    def _set_cooldown(self, alert_type: AlertType, source_id: Optional[UUID]) -> None:
        """Set cooldown for an alert type."""
        key = f"{alert_type.value}:{source_id or 'global'}"
        self._cooldowns[key] = datetime.now()
    
    async def check_and_alert(
        self,
        alert_type: AlertType,
        metric_name: str,
        value: float,
        source_id: Optional[UUID] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[Alert]:
        """
        Check a metric value against thresholds and create alert if triggered.
        
        Args:
            alert_type: Type of alert to check
            metric_name: Name of the metric
            value: Current metric value
            source_id: Optional source identifier
            context: Additional context for the alert
        
        Returns:
            Alert if triggered, None otherwise
        """
        # Find matching threshold
        thresholds = self.config.get_thresholds_for_type(alert_type)
        triggered_threshold = None
        
        for threshold in thresholds:
            if threshold.metric_name == metric_name and threshold.check(value):
                if triggered_threshold is None or threshold.priority.value < triggered_threshold.priority.value:
                    triggered_threshold = threshold
        
        if not triggered_threshold:
            return None
        
        # Check cooldown
        if self._is_on_cooldown(alert_type, source_id):
            logger.debug(f"Alert {alert_type.value} on cooldown, skipping")
            return None
        
        # Create alert
        alert = self._create_alert(
            alert_type,
            triggered_threshold.priority,
            metric_name,
            value,
            triggered_threshold.threshold_value,
            source_id,
            context,
        )
        
        # Store and notify
        async with self._lock:
            self.alerts.append(alert)
            self._set_cooldown(alert_type, source_id)
        
        await self._notify_subscribers(alert)
        
        return alert
    
    def _create_alert(
        self,
        alert_type: AlertType,
        priority: AlertPriority,
        metric_name: str,
        value: float,
        threshold: float,
        source_id: Optional[UUID],
        context: Optional[dict[str, Any]],
    ) -> Alert:
        """Create an alert instance."""
        titles = {
            AlertType.VOC_SPIKE: "Velocity of Contagion Spike Detected",
            AlertType.SEVERITY_CRITICAL: "Critical Severity Event",
            AlertType.CLUSTER_DETECTED: "Signal Cluster Identified",
            AlertType.VELOCITY_ANOMALY: "Abnormal Velocity Pattern",
            AlertType.MISINFORMATION_DETECTED: "Potential Misinformation",
            AlertType.GOVERNANCE_VIOLATION: "Governance Violation",
            AlertType.SIMULATION_COMPLETE: "Simulation Complete",
            AlertType.REVIEW_REQUIRED: "Human Review Required",
        }
        
        return Alert(
            alert_id=uuid4(),
            alert_type=alert_type,
            priority=priority,
            status=AlertStatus.NEW,
            title=titles.get(alert_type, f"Alert: {alert_type.value}"),
            message=f"{metric_name} = {value:.2f} (threshold: {threshold:.2f})",
            timestamp=datetime.now(),
            source_id=source_id,
            metadata={
                "metric_name": metric_name,
                "value": value,
                "threshold": threshold,
                **(context or {}),
            },
        )
    
    async def _notify_subscribers(self, alert: Alert) -> None:
        """Send alert to all subscribers."""
        for subscriber in self.subscribers:
            try:
                await subscriber.notify(alert)
            except Exception as e:
                logger.error(f"Subscriber notification failed: {e}")
    
    async def create_manual_alert(
        self,
        alert_type: AlertType,
        priority: AlertPriority,
        title: str,
        message: str,
        source_id: Optional[UUID] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Alert:
        """Create an alert manually (not from threshold)."""
        alert = Alert(
            alert_id=uuid4(),
            alert_type=alert_type,
            priority=priority,
            status=AlertStatus.NEW,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source_id=source_id,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self.alerts.append(alert)
        
        await self._notify_subscribers(alert)
        return alert
    
    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        priority: Optional[AlertPriority] = None,
        alert_type: Optional[AlertType] = None,
        limit: int = 100,
    ) -> list[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            alert_type: Filter by type
            limit: Maximum alerts to return
        
        Returns:
            List of matching alerts
        """
        results = self.alerts
        
        if status:
            results = [a for a in results if a.status == status]
        if priority:
            results = [a for a in results if a.priority == priority]
        if alert_type:
            results = [a for a in results if a.alert_type == alert_type]
        
        # Sort by timestamp descending
        results = sorted(results, key=lambda a: a.timestamp, reverse=True)
        
        return results[:limit]
    
    def acknowledge_alert(self, alert_id: UUID, user: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge(user)
                return alert
        return None
    
    def resolve_alert(self, alert_id: UUID, user: str) -> Optional[Alert]:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolve(user)
                return alert
        return None
    
    def get_active_count(self) -> dict[str, int]:
        """Get count of active alerts by priority."""
        active = [a for a in self.alerts if a.status in (AlertStatus.NEW, AlertStatus.ACKNOWLEDGED)]
        return {
            "total": len(active),
            "critical": sum(1 for a in active if a.priority == AlertPriority.CRITICAL),
            "high": sum(1 for a in active if a.priority == AlertPriority.HIGH),
            "medium": sum(1 for a in active if a.priority == AlertPriority.MEDIUM),
            "low": sum(1 for a in active if a.priority == AlertPriority.LOW),
        }


# Module-level singleton
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager singleton."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
