"""
FastAPI Backend for the Reputational Stress-Test Simulator.

Provides:
- REST API for scenario management and briefings
- WebSocket for real-time simulation updates
- CORS support for frontend integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our modules
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from backend.data.data_loader import get_data_loader
from backend.models.schemas import (
    GovernanceDecisionRequest,
    HumanAction,
    Scenario,
    SeverityLevel,
    SimulationStartRequest,
    SimulationStatusResponse,
    VelocityDataPoint,
)
from backend.core.signal_detector import SignalDetector, RAGFactChecker
from backend.core.causal_engine import CausalEngine
from backend.core.governance import get_governance_gate
from simulator.engine import ContagionSimulator
from reporting.briefing_generator import BriefingGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Reputational Stress-Test Simulator API",
    description="AI-powered crisis simulation and prediction for banking",
    version="1.0.0",
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (lazy loading)
_data_loader = None
_simulator = None
_detector = None
_causal_engine = None
_briefing_generator = None
_governance = None


def get_components():
    """Lazy initialization of components."""
    global _data_loader, _simulator, _detector, _causal_engine, _briefing_generator, _governance
    
    if _data_loader is None:
        _data_loader = get_data_loader()
    if _simulator is None:
        _simulator = ContagionSimulator(use_llm=False)  # Start with heuristics for speed
    if _detector is None:
        _detector = SignalDetector()
    if _causal_engine is None:
        _causal_engine = CausalEngine()
    if _briefing_generator is None:
        _briefing_generator = BriefingGenerator()
    if _governance is None:
        _governance = get_governance_gate()
    
    return _data_loader, _simulator, _detector, _causal_engine, _briefing_generator, _governance


# =============================================================================
# REST Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Reputational Stress-Test Simulator",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/scenarios")
async def list_scenarios():
    """List all available scenarios."""
    data_loader, *_ = get_components()
    scenarios = data_loader.load_scenarios()
    
    return {
        "scenarios": [
            {
                "id": str(s.scenario_id),
                "name": s.scenario_name,
                "description": s.description,
                "severity": s.severity_level.value,
                "target_segment": s.target_segment,
                "duration_hours": s.simulation_duration_hours,
                "expected_velocity_peak": s.expected_velocity_peak,
            }
            for s in scenarios
        ]
    }


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get details for a specific scenario."""
    data_loader, *_ = get_components()
    
    try:
        uuid = UUID(scenario_id)
        scenario = data_loader.get_scenario_by_id(uuid)
    except ValueError:
        # Try by name
        scenario = data_loader.get_scenario_by_name(scenario_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return {
        "scenario": {
            "id": str(scenario.scenario_id),
            "name": scenario.scenario_name,
            "description": scenario.description,
            "severity": scenario.severity_level.value,
            "target_segment": scenario.target_segment,
            "duration_hours": scenario.simulation_duration_hours,
            "expected_velocity_peak": scenario.expected_velocity_peak,
            "key_narratives": scenario.key_narratives,
            "monitoring_keywords": scenario.monitoring_keywords,
            "potential_impact": scenario.potential_impact,
        }
    }


@app.get("/api/signals")
async def list_signals(
    limit: int = Query(default=50, le=500),
    category: Optional[str] = None,
):
    """Get synthetic signals with optional filtering."""
    data_loader, *_ = get_components()
    signals = data_loader.load_signals(limit=limit)
    
    if category:
        signals = [s for s in signals if s.gt_category.value == category]
    
    return {
        "signals": [
            {
                "id": str(s.signal_id),
                "timestamp": s.timestamp.isoformat(),
                "platform": s.platform_source.value,
                "content": s.content_text[:300] + "..." if len(s.content_text) > 300 else s.content_text,
                "category": s.gt_category.value,
                "sentiment": s.gt_sentiment,
                "virality": s.gt_virality_potential,
            }
            for s in signals[:limit]
        ],
        "total": len(signals),
    }


@app.get("/api/agents")
async def list_agents(limit: int = Query(default=20, le=200)):
    """Get agent archetypes."""
    data_loader, *_ = get_components()
    agents = data_loader.load_agents()
    
    return {
        "agents": [
            {
                "id": str(a.agent_id),
                "name": a.archetype_name,
                "segment": a.demographic_segment,
                "skepticism": a.skepticism_score,
                "brand_loyalty": a.brand_loyalty,
                "influence": a.network_influence,
                "values": a.core_values,
            }
            for a in agents[:limit]
        ],
        "total": len(agents),
    }


@app.post("/api/detect")
async def detect_signals():
    """Run signal detection on the dataset."""
    data_loader, _, detector, *_ = get_components()
    
    try:
        clusters = detector.detect_clusters()
        
        return {
            "clusters": [
                {
                    "id": str(c.cluster_id),
                    "category": c.primary_category.value,
                    "severity": c.detected_severity.value,
                    "confidence": c.confidence_score,
                    "summary": c.ai_summary,
                    "themes": c.key_themes,
                    "signal_count": len(c.signals),
                    "has_misinformation": c.detected_misinformation,
                }
                for c in clusters
            ]
        }
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge")
async def search_knowledge(query: str = Query(..., min_length=3)):
    """Search the knowledge base."""
    data_loader, *_ = get_components()
    
    results = data_loader.query_knowledge_base(query)
    
    return {
        "query": query,
        "results": results,
    }


# =============================================================================
# WebSocket for Real-Time Simulation
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")


manager = ConnectionManager()


@app.websocket("/ws/simulation")
async def websocket_simulation(websocket: WebSocket):
    """
    WebSocket endpoint for real-time simulation updates.
    
    Client sends: { "action": "start", "scenario_id": "...", "speed": 1.0 }
    Server sends: VelocityDataPoint updates every simulation step
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_json()
            
            action = data.get("action")
            
            if action == "start":
                # Start simulation
                scenario_id = data.get("scenario_id")
                scenario_name = data.get("scenario_name")
                speed = float(data.get("speed", 1.0))
                duration = int(data.get("duration", 24))
                
                # Get components
                data_loader, simulator, *_ = get_components()
                
                # Find scenario
                scenario = None
                if scenario_id:
                    try:
                        scenario = data_loader.get_scenario_by_id(UUID(scenario_id))
                    except:
                        pass
                if not scenario and scenario_name:
                    scenario = data_loader.get_scenario_by_name(scenario_name)
                if not scenario:
                    scenarios = data_loader.load_scenarios()
                    scenario = scenarios[0] if scenarios else None
                
                if not scenario:
                    await websocket.send_json({"error": "No scenario found"})
                    continue

                # Get trigger signals
                signals = data_loader.get_signals_for_scenario(scenario, limit=50)
                
                # Send simulation start message
                await websocket.send_json({
                    "type": "simulation_start",
                    "scenario": scenario.scenario_name,
                    "severity": scenario.severity_level.value,
                    "duration": duration,
                })
                
                # Run simulation and stream updates
                try:
                    async for point in simulator.run_simulation(
                        scenario=scenario,
                        trigger_signals=signals,
                        duration_hours=min(duration, 48),
                        speed_multiplier=speed,
                    ):
                        # Send each data point
                        metrics = simulator.get_current_metrics()
                        
                        await websocket.send_json({
                            "type": "simulation_update",
                            "point": {
                                "time": point.time,
                                "hour": point.hour,
                                "velocity": point.velocity,
                                "active_sharers": point.active_sharers,
                                "cumulative_reach": point.cumulative_reach,
                            },
                            "metrics": metrics,
                        })
                    
                    # Send completion message
                    await websocket.send_json({
                        "type": "simulation_complete",
                        "metrics": simulator.get_current_metrics(),
                    })
                    
                except Exception as e:
                    logger.error(f"Simulation error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})
            
            elif action == "pause":
                await websocket.send_json({"type": "paused"})
            
            elif action == "stop":
                await websocket.send_json({"type": "stopped"})
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# =============================================================================
# Governance Endpoints
# =============================================================================

@app.post("/api/governance/decision")
async def record_decision(request: GovernanceDecisionRequest):
    """Record a human governance decision."""
    *_, governance = get_components()
    
    governance.log_decision(
        incident_id=request.incident_id,
        action_type=f"HUMAN_{request.decision.value}",
        actor=request.reviewer_id,
        details={"notes": request.notes},
    )
    
    return {"status": "recorded", "decision": request.decision.value}


@app.get("/api/governance/audit")
async def get_audit_log(limit: int = Query(default=50, le=200)):
    """Get audit log entries."""
    *_, governance = get_components()
    
    entries = governance.get_audit_trail(limit=limit)
    
    return {
        "entries": [
            {
                "timestamp": e.timestamp.isoformat(),
                "action": e.action_type,
                "actor": e.actor,
                "target": str(e.target_id),
                "details": e.details,
            }
            for e in entries
        ]
    }


# =============================================================================
# LangGraph Workflow Endpoints
# =============================================================================

class WorkflowRequest(BaseModel):
    """Request to run the LangGraph workflow."""
    scenario_name: Optional[str] = None
    scenario_id: Optional[str] = None
    signal_limit: int = 100
    use_llm: bool = False


@app.post("/api/workflow/run")
async def run_langgraph_workflow(request: WorkflowRequest):
    """
    Run the complete LangGraph simulation workflow.
    
    This endpoint orchestrates the full pipeline:
    1. Load data
    2. Detect signals
    3. Analyze clusters
    4. Run simulation (conditional)
    5. Adversarial review
    6. Generate briefing (conditional)
    7. Governance check
    
    Returns:
        Complete workflow results including briefing and recommendations.
    """
    try:
        from workflow.graph import run_workflow, get_workflow_summary
        
        final_state = await run_workflow(
            scenario_name=request.scenario_name,
            scenario_id=request.scenario_id,
            signal_limit=request.signal_limit,
            use_llm=request.use_llm,
        )
        
        summary = get_workflow_summary(final_state)
        
        return {
            "success": True,
            "summary": summary,
            "briefing": final_state.get("briefing"),
            "socratic_questions": final_state.get("socratic_questions", []),
            "requires_human_review": final_state.get("requires_human_review", False),
        }
        
    except ImportError as e:
        logger.warning(f"LangGraph not available: {e}")
        raise HTTPException(
            status_code=503,
            detail="LangGraph workflow not available. Install langgraph package."
        )
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflow/status")
async def get_workflow_status():
    """
    Check if LangGraph workflow is available.
    
    Returns:
        Status of the workflow system.
    """
    try:
        from workflow.graph import create_workflow
        create_workflow()
        return {
            "available": True,
            "nodes": [
                "load_data",
                "detect_signals", 
                "analyze_clusters",
                "run_simulation",
                "adversarial_review",
                "generate_briefing",
                "governance_check",
            ]
        }
    except ImportError:
        return {
            "available": False,
            "error": "LangGraph not installed"
        }


# =============================================================================
# Alert System Endpoints
# =============================================================================

from backend.core.alerts import (
    get_alert_manager, 
    AlertPriority, 
    AlertType, 
    AlertStatus,
    WebSocketSubscriber,
)

# WebSocket subscriber for real-time alerts
_ws_subscriber = WebSocketSubscriber()
get_alert_manager().add_subscriber(_ws_subscriber)


class CreateAlertRequest(BaseModel):
    """Request to create a manual alert."""
    alert_type: str
    priority: str
    title: str
    message: str
    metadata: Optional[dict] = None


@app.get("/api/alerts")
async def get_alerts(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get alerts with optional filtering.
    
    Query parameters:
    - status: "new", "acknowledged", "resolved", "dismissed"
    - priority: "critical", "high", "medium", "low", "info"
    - alert_type: "voc_spike", "severity_critical", etc.
    - limit: Maximum alerts to return
    """
    manager = get_alert_manager()
    
    status_filter = AlertStatus(status) if status else None
    priority_filter = AlertPriority(priority) if priority else None
    type_filter = AlertType(alert_type) if alert_type else None
    
    alerts = manager.get_alerts(
        status=status_filter,
        priority=priority_filter,
        alert_type=type_filter,
        limit=limit,
    )
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
        "active_summary": manager.get_active_count(),
    }


@app.post("/api/alerts")
async def create_alert(request: CreateAlertRequest):
    """Create a manual alert."""
    manager = get_alert_manager()
    
    try:
        alert = await manager.create_manual_alert(
            alert_type=AlertType(request.alert_type),
            priority=AlertPriority(request.priority),
            title=request.title,
            message=request.message,
            metadata=request.metadata,
        )
        return {"success": True, "alert": alert.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: str = Query(...)):
    """Acknowledge an alert."""
    manager = get_alert_manager()
    alert = manager.acknowledge_alert(UUID(alert_id), user)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "alert": alert.to_dict()}


@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: str = Query(...)):
    """Resolve an alert."""
    manager = get_alert_manager()
    alert = manager.resolve_alert(UUID(alert_id), user)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "alert": alert.to_dict()}


@app.get("/api/alerts/config")
async def get_alert_config():
    """Get current alert configuration."""
    manager = get_alert_manager()
    return manager.config.to_dict()


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.
    
    Clients connected to this endpoint will receive alerts in real-time.
    """
    await websocket.accept()
    _ws_subscriber.add_connection(websocket)
    
    try:
        # Send initial message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to alert stream",
            "active_alerts": get_alert_manager().get_active_count(),
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for any message (ping/pong or close)
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                break
    finally:
        _ws_subscriber.remove_connection(websocket)


# =============================================================================
# Explainability Endpoints
# =============================================================================

from backend.core.explainability import get_explainer
from backend.core.calibration import get_calibrator


class ExplainClassificationRequest(BaseModel):
    """Request to explain a classification."""
    signal_content: str
    predicted_category: str
    confidence: float
    sentiment: Optional[float] = None
    virality: Optional[float] = None


@app.post("/api/explain/classification")
async def explain_classification(request: ExplainClassificationRequest):
    """
    Generate explanation for a signal classification.
    
    Returns feature contributions, reasoning steps, and uncertainty sources.
    """
    from backend.models.schemas import SignalCategory
    
    explainer = get_explainer()
    calibrator = get_calibrator()
    
    try:
        category = SignalCategory(request.predicted_category)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category: {request.predicted_category}"
        )
    
    # Generate explanation
    explanation = explainer.explain_classification(
        signal_content=request.signal_content,
        predicted_category=category,
        confidence=request.confidence,
        sentiment=request.sentiment,
        virality=request.virality,
    )
    
    # Apply calibration
    calibration = calibrator.calibrate(request.confidence)
    explanation.calibrated_confidence = calibration.calibrated_confidence
    
    return {
        "explanation": explanation.to_dict(),
        "natural_language": explanation.to_natural_language(),
        "calibration": calibration.to_dict(),
    }


@app.post("/api/explain/severity")
async def explain_severity(
    category: str,
    sentiment: float,
    virality: float,
    signal_count: int,
    predicted_severity: str,
    confidence: float,
):
    """Generate explanation for a severity prediction."""
    from backend.models.schemas import SignalCategory, SeverityLevel
    
    explainer = get_explainer()
    
    explanation = explainer.explain_severity(
        category=SignalCategory(category),
        sentiment=sentiment,
        virality=virality,
        signal_count=signal_count,
        predicted_severity=SeverityLevel(predicted_severity),
        confidence=confidence,
    )
    
    return {
        "explanation": explanation.to_dict(),
        "natural_language": explanation.to_natural_language(),
    }


@app.post("/api/calibrate")
async def calibrate_confidence(confidence: float):
    """
    Calibrate a confidence score.
    
    Returns calibrated confidence with uncertainty interval.
    """
    calibrator = get_calibrator()
    result = calibrator.calibrate(confidence)
    return result.to_dict()


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


