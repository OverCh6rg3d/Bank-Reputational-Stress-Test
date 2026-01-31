"""
Contagion Simulation Engine - The "Killer Feature"

This is a Monte Carlo Agent-Based Model that predicts how social signals
(rumors, complaints, etc.) spread through synthetic customer segments.

Key concept: "Velocity of Contagion" (VoC) - a score 0-100 indicating
how fast a signal is spreading.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, AsyncGenerator
from uuid import UUID, uuid4

from backend.data.data_loader import get_data_loader
from backend.models.schemas import (
    AgentAction,
    AgentArchetype,
    ContagionResult,
    Scenario,
    SeverityLevel,
    SimulationStep,
    SocialSignal,
    VelocityDataPoint,
)
from simulator.agent_brain import AgentBrain, AgentDecision

logger = logging.getLogger(__name__)


class ContagionSimulator:
    """
    Monte Carlo simulation engine for rumor propagation.
    
    The simulation runs in discrete time steps (hours), and at each step:
    1. A subset of agents is "exposed" to the signal
    2. Each exposed agent decides to IGNORE, SHARE, COMMENT, etc.
    3. Sharing increases the reach for the next step
    4. We calculate VoC (Velocity of Contagion) at each step
    
    The goal is to predict: "If we do nothing, how bad does this get?"
    """

    def __init__(
        self,
        use_llm: bool = True,
        agents_per_step: int = 20,  # How many agents to process per hour
        initial_exposure_rate: float = 0.05,  # Initial % of population exposed
    ):
        self.use_llm = use_llm
        self.agents_per_step = agents_per_step
        self.initial_exposure_rate = initial_exposure_rate
        
        self.data_loader = get_data_loader()
        self.agent_brain = AgentBrain(use_llm=use_llm)
        
        # State
        self._agents: Optional[list[AgentArchetype]] = None
        self._current_simulation: Optional[ContagionResult] = None

    @property
    def agents(self) -> list[AgentArchetype]:
        """Lazy load agent archetypes."""
        if self._agents is None:
            self._agents = self.data_loader.load_agents()
        return self._agents

    def get_agents_for_segment(self, segment: str) -> list[AgentArchetype]:
        """Filter agents by demographic segment."""
        if segment.lower() == "all":
            return self.agents
        
        segments = [s.strip() for s in segment.split(",")]
        return [
            a for a in self.agents
            if any(seg.lower() in a.demographic_segment.lower() for seg in segments)
        ]

    async def run_simulation(
        self,
        scenario: Scenario,
        trigger_signals: list[SocialSignal],
        duration_hours: int = 24,
        speed_multiplier: float = 1.0,
    ) -> AsyncGenerator[VelocityDataPoint, None]:
        """
        Run the full simulation and yield data points for real-time display.
        
        This is a generator that yields VelocityDataPoint at each simulation step,
        allowing the frontend to display updates in real-time.
        
        Args:
            scenario: The scenario being simulated
            trigger_signals: Initial signals that trigger the crisis
            duration_hours: How many hours to simulate
            speed_multiplier: How fast to run (1.0 = 1 second per hour)
        """
        simulation_id = uuid4()
        start_time = datetime.now()
        
        logger.info(f"Starting simulation {simulation_id} for scenario: {scenario.scenario_name}")

        # Initialize result tracking
        result = ContagionResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            started_at=start_time,
            duration_hours=duration_hours,
            peak_velocity=0.0,
            final_reach_percentage=0.0,
            velocity_trajectory=[],
        )
        self._current_simulation = result

        # Get relevant agents for this scenario
        target_agents = self.get_agents_for_segment(scenario.target_segment)
        if not target_agents:
            target_agents = self.agents  # Fallback to all

        total_population = len(target_agents)
        logger.info(f"Simulating with {total_population} agents for segment: {scenario.target_segment}")

        # Simulation state
        exposed_agents: set[UUID] = set()
        infected_agents: set[UUID] = set()  # Agents who shared/commented
        cumulative_reach = 0
        
        # Track all simulation steps for detailed logging
        all_steps: list[SimulationStep] = []

        # Initial exposure (people who see the trigger signal)
        initial_exposed_count = int(total_population * self.initial_exposure_rate)
        initial_exposed = random.sample(target_agents, min(initial_exposed_count, len(target_agents)))
        for agent in initial_exposed:
            exposed_agents.add(agent.agent_id)

        # Generate historical baseline (T-6 to T0)
        for hour in range(-6, 1):
            base_velocity = 8 + random.random() * 6
            point = VelocityDataPoint(
                time=self._format_time(start_time, hour),
                hour=hour,
                velocity=round(base_velocity, 1),
                active_sharers=0,
                cumulative_reach=0,
            )
            result.velocity_trajectory.append(point)
            yield point

        # Main simulation loop
        primary_signal = trigger_signals[0] if trigger_signals else None
        if not primary_signal:
            logger.error("No trigger signals provided")
            return

        for hour in range(1, duration_hours + 1):
            step_start = datetime.now()
            
            # Select agents to process this step
            # Prioritize newly exposed agents, then sample from population
            exposed_list = [a for a in target_agents if a.agent_id in exposed_agents]
            unexposed_list = [a for a in target_agents if a.agent_id not in exposed_agents]
            
            # Mix of exposed and random unexposed (simulating organic discovery)
            agents_to_process = []
            if exposed_list:
                agents_to_process.extend(random.sample(
                    exposed_list, 
                    min(self.agents_per_step // 2, len(exposed_list))
                ))
            if unexposed_list:
                agents_to_process.extend(random.sample(
                    unexposed_list,
                    min(self.agents_per_step // 2, len(unexposed_list))
                ))

            # Process agent decisions
            if self.use_llm:
                current_stats = {
                    "total_shares": result.total_shares,
                    "total_comments": result.total_comments,
                }
                decisions = await self.agent_brain.batch_decide(
                    agents_to_process, primary_signal, current_stats
                )
            else:
                decisions = [
                    self.agent_brain._heuristic_decision(a, primary_signal)
                    for a in agents_to_process
                ]

            # Update state based on decisions
            new_sharers = 0
            new_commenters = 0
            hour_reach = 0
            
            for decision in decisions:
                if decision.action == AgentAction.SHARE:
                    infected_agents.add(decision.agent_id)
                    new_sharers += 1
                    # Sharing exposes more agents
                    new_exposed = int(decision.reach_multiplier * 0.1)
                    for _ in range(new_exposed):
                        if unexposed_list:
                            new_agent = random.choice(unexposed_list)
                            exposed_agents.add(new_agent.agent_id)
                            hour_reach += 1
                    
                elif decision.action == AgentAction.COMMENT:
                    infected_agents.add(decision.agent_id)
                    new_commenters += 1
                    # Commenting has smaller reach
                    new_exposed = int(decision.reach_multiplier * 0.03)
                    for _ in range(new_exposed):
                        if unexposed_list:
                            new_agent = random.choice(unexposed_list)
                            exposed_agents.add(new_agent.agent_id)
                            hour_reach += 1
                
                elif decision.action == AgentAction.REPORT:
                    result.total_reports += 1

                # Record step
                step = SimulationStep(
                    simulation_id=simulation_id,
                    step_number=hour,
                    step_time=start_time + timedelta(hours=hour),
                    agent_id=decision.agent_id,
                    interacting_with_signal=decision.signal_id,
                    action_taken=decision.action,
                    reasoning_trace=decision.reasoning,
                    emotional_state_after=decision.emotional_state,
                    virality_velocity=0.0,  # Will update below
                )
                all_steps.append(step)

            cumulative_reach += hour_reach
            result.total_shares += new_sharers
            result.total_comments += new_commenters

            # Calculate Velocity of Contagion
            # VoC = (new exposures this hour / total population) * 100
            # Plus momentum from previous velocity
            base_velocity = (hour_reach / max(total_population, 1)) * 1000
            
            # Add scenario severity modifier
            severity_boost = {
                SeverityLevel.CRITICAL: 1.5,
                SeverityLevel.HIGH: 1.2,
                SeverityLevel.MEDIUM: 1.0,
                SeverityLevel.LOW: 0.7,
                SeverityLevel.POSITIVE: 0.3,
            }.get(scenario.severity_level, 1.0)
            
            # Momentum: velocity tends to grow early then plateau
            momentum = (scenario.expected_velocity_peak / 100) * (1 - hour / duration_hours)
            
            velocity = min(100, base_velocity * severity_boost + momentum * 30 + len(infected_agents) * 0.5)
            
            # Add some noise for realism
            velocity += random.uniform(-3, 3)
            velocity = max(0, min(100, velocity))

            # Track peak
            if velocity > result.peak_velocity:
                result.peak_velocity = velocity
                
            # Track time to critical
            if velocity > 80 and result.time_to_critical is None:
                result.time_to_critical = hour

            # Create data point
            point = VelocityDataPoint(
                time=self._format_time(start_time, hour),
                hour=hour,
                velocity=round(velocity, 1),
                active_sharers=len(infected_agents),
                cumulative_reach=cumulative_reach,
            )
            result.velocity_trajectory.append(point)

            # Control simulation speed
            elapsed = (datetime.now() - step_start).total_seconds()
            target_time = 1.0 / speed_multiplier
            if elapsed < target_time:
                await asyncio.sleep(target_time - elapsed)

            yield point

        # Finalize result
        result.ended_at = datetime.now()
        result.final_reach_percentage = len(exposed_agents) / total_population * 100
        
        # Detect if it looks like a coordinated attack
        if result.peak_velocity > 80 and result.time_to_critical and result.time_to_critical < 3:
            result.is_coordinated_attack = True
            result.attack_confidence = 0.85

        logger.info(
            f"Simulation complete. Peak VoC: {result.peak_velocity:.1f}, "
            f"Time to critical: {result.time_to_critical or 'N/A'}h, "
            f"Final reach: {result.final_reach_percentage:.1f}%"
        )

    def run_simulation_sync(
        self,
        scenario: Scenario,
        trigger_signals: list[SocialSignal],
        duration_hours: int = 24,
    ) -> ContagionResult:
        """
        Synchronous version that runs full simulation and returns result.
        Useful for batch processing and testing.
        """
        async def collect():
            points = []
            async for point in self.run_simulation(
                scenario, trigger_signals, duration_hours, speed_multiplier=100
            ):
                points.append(point)
            return points

        asyncio.run(collect())
        return self._current_simulation

    def _format_time(self, start: datetime, hours_offset: int) -> str:
        """Format simulation time as 'Jan 30 14:00'."""
        dt = start + timedelta(hours=hours_offset)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f"{months[dt.month - 1]} {dt.day} {dt.hour:02d}:00"

    def get_current_metrics(self) -> dict:
        """Get current simulation metrics for API response."""
        if self._current_simulation is None:
            return {
                "velocity": 0,
                "confidence": 85,
                "alerts": 0,
            }
        
        result = self._current_simulation
        latest = result.velocity_trajectory[-1] if result.velocity_trajectory else None
        
        return {
            "velocity": latest.velocity if latest else 0,
            "confidence": 85 - (10 if result.is_coordinated_attack else 0),
            "alerts": 1 if result.peak_velocity > 80 else 0,
            "peak_velocity": result.peak_velocity,
            "time_to_critical": result.time_to_critical,
            "total_shares": result.total_shares,
            "total_comments": result.total_comments,
        }
