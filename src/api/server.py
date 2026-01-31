import asyncio
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Import backend components
from backend.data.data_loader import get_data_loader
from simulator.engine import ContagionSimulator
from signals.generator import SyntheticSignalGenerator
from backend.core.debate import get_debate_engine, DebateResult
from backend.core.signal_detector import SignalDetector
from backend.core.causal_engine import CausalEngine
from backend.models.schemas import Scenario, SocialSignal
from api.models import (
    StartSimulationRequest,
    GenerateSignalsRequest,
    RunDebateRequest,
    GovernanceDecisionRequest,
    SimulationStateResponse,
    DebateResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Bank Reputational Stress-Test API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State (Simplified for single-user demo)
class GlobalState:
    def __init__(self):
        self.simulator: Optional[ContagionSimulator] = None
        self.active_connections: List[WebSocket] = []
        self.current_scenario: Optional[Scenario] = None
        self.simulation_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.simulation_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.is_paused = False
        self.signal_cache: List[dict] = [] # Cache for the frontend feed

state = GlobalState()
data_loader = get_data_loader()

# --- Connection Manager ---

class ConnectionManager:
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        state.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        state.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in state.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")

manager = ConnectionManager()


# --- Endpoints ---

@app.get("/api/scenarios")
async def get_scenarios():
    """Get all available scenarios."""
    scenarios = data_loader.load_scenarios()
    return [s.model_dump() for s in scenarios]


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: UUID):
    """Get specific scenario details."""
    scenario = data_loader.get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario.model_dump()


@app.get("/api/agents")
async def get_agents(limit: int = 20):
    """Get agent archetypes."""
    agents = data_loader.load_agents()
    return [a.model_dump() for a in agents[:limit]]



@app.get("/api/signals")
async def get_signals(limit: int = 50, category: Optional[str] = None):
    """Get generated signals (Mock/Demo)."""
    # In a real app, this would query the DB. 
    # For demo, we return signals from the current active simulation or generate new ones.
    
    if state.current_scenario:
        # Return cached signals if available, otherwise generate fallback
        if state.signal_cache:
            return state.signal_cache
            
        # Fallback if empty (shouldn't happen if sim started)
        generator = SyntheticSignalGenerator()
        signals = await generator.generate_signals(state.current_scenario, count=5)
        return [s.model_dump() for s in signals]
    else:
        return []

async def detect_signals():
    """Trigger signal detection (Mock/Demo)."""
    # In a full run, this would process incoming signals.
    # For the API demo, we'll return the cluster analysis of the current scenario.
    if not state.current_scenario:
        raise HTTPException(status_code=400, detail="No scenario active")
        
    # Generate some signals first if none exist
    generator = SyntheticSignalGenerator()
    signals = await generator.generate_signals(state.current_scenario, count=20)
    
    # Run detection
    detector = SignalDetector()
    clusters = detector.detect_clusters(signals)
    
    return {
        "clusters": [c.model_dump() for c in clusters],
        "signals_processed": len(signals)
    }


@app.post("/api/analysis/debate", response_model=DebateResponse)
async def run_debate(request: RunDebateRequest):
    """Run an adversarial debate on a finding."""
    engine = get_debate_engine()
    
    result = engine.run_debate(
        initial_finding=request.finding,
        initial_confidence=request.confidence,
        context=request.context,
        max_turns=request.max_turns
    )
    
    return DebateResponse(
        debate_id=str(result.debate_id),
        transcript=[t.__dict__ for t in result.turns],
        final_consensus=result.final_consensus,
        refined_confidence=result.refined_confidence,
        issues_raised=result.issues_raised
    )


@app.post("/api/governance/decision")
async def record_decision(request: GovernanceDecisionRequest):
    """Log a human governance decision."""
    # In a real app, this would save to DB/Ledger
    logger.info(f"Decision recorded: {request.decision} by {request.reviewer_id}")
    
    # TRIGGER INTERVENTION IF APPROVED
    if request.decision.upper() == "APPROVE" and state.simulator and state.is_running:
        logger.info("Applying mitigation strategy to running simulation...")
        state.simulator.apply_intervention(effectiveness=0.7) # 70% reduction in velocity
        await manager.broadcast({
            "type": "intervention",
            "message": "Strategy Approved: Mitigating actions deployed. Viral velocity dampening."
        })
        
    return {"status": "success", "message": "Decision recorded on ledger"}


# --- Simulation WebSocket ---

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "start":
                await start_simulation(data)
            elif action == "stop":
                await stop_simulation()
            elif action == "pause":
                state.is_paused = True
                await manager.broadcast({"status": "paused"})
            elif action == "resume":
                state.is_paused = False
                await manager.broadcast({"status": "running"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        manager.disconnect(websocket)


async def start_simulation(data: dict):
    """Initialize and start the simulation loop."""
    # 1. Load Scenario
    scenario_name = data.get("scenario_name")
    scenario_id = data.get("scenario_id")
    
    selected_scenario = None
    if scenario_id:
        selected_scenario = data_loader.get_scenario_by_id(UUID(scenario_id))
    elif scenario_name:
        selected_scenario = data_loader.get_scenario_by_name(scenario_name)
    
    if not selected_scenario:
        await manager.broadcast({"error": "Scenario not found"})
        return

    state.current_scenario = selected_scenario
    
    # 2. Generate Initial Signals
    generator = SyntheticSignalGenerator()
    signals = await generator.generate_signals(selected_scenario, count=10)
    
    # Cache for API feed
    state.signal_cache = [s.model_dump() for s in signals]
    
    # 3. Initialize Simulator
    state.simulator = ContagionSimulator(
        use_llm=True, # Use LLM for agent decisions
        agents_per_step=15,
        initial_exposure_rate=0.05
    )
    
    # 4. Start Loop
    if state.simulation_task:
        state.simulation_task.cancel()
        
    state.is_running = True
    state.is_paused = False
    
    state.simulation_task = asyncio.create_task(
        run_simulation_loop(selected_scenario, signals, data.get("speed", 1.0))
    )
    
    await manager.broadcast({
        "status": "started",
        "scenario": selected_scenario.scenario_name,
        "message": "Simulation initialized. Agents active."
    })


async def stop_simulation():
    """Stop the current simulation."""
    state.is_running = False
    if state.simulation_task:
        state.simulation_task.cancel()
    state.simulator = None
    await manager.broadcast({"status": "stopped"})


async def run_simulation_loop(scenario: Scenario, signals: List[SocialSignal], speed: float):
    """The main async loop pushing updates to WebSocket."""
    try:
        async for point in state.simulator.run_simulation(
            scenario=scenario,
            trigger_signals=signals,
            duration_hours=24,
            speed_multiplier=speed
        ):
            if not state.is_running:
                break
                
            while state.is_paused:
                await asyncio.sleep(0.5)
            
            # Broadcast update
            metrics = state.simulator.get_current_metrics()
            
            await manager.broadcast({
                "type": "update",
                "point": point.model_dump(),
                "metrics": metrics
            })
            
        await manager.broadcast({"status": "completed"})
            
    except asyncio.CancelledError:
        logger.info("Simulation cancelled")
    except Exception as e:
        logger.error(f"Simulation loop error: {e}")
        await manager.broadcast({"error": str(e)})
