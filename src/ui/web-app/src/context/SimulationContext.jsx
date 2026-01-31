import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api, createSimulationSocket } from '../services/api';

const SimulationContext = createContext();

export const useSimulation = () => useContext(SimulationContext);

// Format time as "Jan 30 14:00" based on start time + hours offset
const formatSimTime = (startTime, hoursOffset) => {
    const date = new Date(startTime.getTime() + hoursOffset * 60 * 60 * 1000);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const day = date.getDate();
    const hours = date.getHours().toString().padStart(2, '0');
    return `${month} ${day} ${hours}:00`;
};

// Simulation duration (72 hours = 3 days for realistic crisis lifecycle)
const DURATION_HOURS = 72;
const TOTAL_POPULATION = 10000;

// Scenario parameters matching backend engine.py severity_boost values
// Transmission rates adjusted for 72h timeline (slower spread over 3 days)
const SCENARIO_PARAMS = {
    "Data Leak": {
        severity: "HIGH",
        severityBoost: 1.2,
        baseTransmissionRate: 0.08,  // Reduced for 72h spread
        initialVelocity: 18,
        peakVelocityTarget: 75,
        peakHour: 18  // When crisis typically peaks
    },
    "Outage": {
        severity: "MEDIUM",
        severityBoost: 1.0,
        baseTransmissionRate: 0.06,
        initialVelocity: 12,
        peakVelocityTarget: 55,
        peakHour: 12
    },
    "Deepfake": {
        severity: "CRITICAL",
        severityBoost: 1.5,
        baseTransmissionRate: 0.12,  // Higher for viral misinformation
        initialVelocity: 25,
        peakVelocityTarget: 90,
        peakHour: 24
    },
    "default": {
        severity: "MEDIUM",
        severityBoost: 1.0,
        baseTransmissionRate: 0.05,
        initialVelocity: 10,
        peakVelocityTarget: 50,
        peakHour: 16
    }
};

// Get scenario params by name (matches partial names)
const getScenarioParams = (scenarioName) => {
    if (scenarioName.includes("Data Leak") || scenarioName.includes("Leak")) {
        return SCENARIO_PARAMS["Data Leak"];
    } else if (scenarioName.includes("Outage")) {
        return SCENARIO_PARAMS["Outage"];
    } else if (scenarioName.includes("Deepfake") || scenarioName.includes("Executive")) {
        return SCENARIO_PARAMS["Deepfake"];
    }
    return SCENARIO_PARAMS["default"];
};

// Generate initial historical baseline data (past 6 hours before T=0)
// Now takes scenario into account for severity-appropriate baseline
const generateHistoricalBaseline = (startTime, scenarioName) => {
    const params = getScenarioParams(scenarioName);
    const baseVelocity = params.initialVelocity * 0.6; // Historical is lower than trigger point

    const history = [];
    for (let i = -6; i <= 0; i++) {
        // Gradually increase towards T=0 (the trigger point)
        const progress = (i + 6) / 6; // 0 to 1
        const velocity = baseVelocity + (params.initialVelocity - baseVelocity) * progress;
        // Add small noise ±1.5
        const noise = (Math.random() - 0.5) * 3;
        history.push({
            time: formatSimTime(startTime, i),
            velocity: Math.round((velocity + noise) * 10) / 10,
            hour: i
        });
    }
    return history;
};

export const SimulationProvider = ({ children }) => {
    // Scenarios from backend
    const [scenarios, setScenarios] = useState([]);
    const [activeScenario, setActiveScenario] = useState(null);
    const [activeScenarioName, setActiveScenarioName] = useState("Data Leak Rumor");

    // Simulation state
    const [simulationStatus, setSimulationStatus] = useState("idle"); // idle, running, paused, complete
    const [simulationSpeed, setSimulationSpeed] = useState(1);
    const [timeHorizon, setTimeHorizon] = useState(0);

    // Store the start time when simulation begins
    const [startTime, setStartTime] = useState(() => new Date());

    // Risk Metrics
    const [metrics, setMetrics] = useState({
        velocity: 12,
        confidence: 45,
        alerts: 0,
        peak_velocity: 0,
        time_to_critical: null,
        total_shares: 0,
    });

    // Initial chart data with historical baseline
    const [velocityHistory, setVelocityHistory] = useState(() =>
        generateHistoricalBaseline(new Date(), "Data Leak Rumor")
    );

    // WebSocket connection
    const wsRef = useRef(null);
    const [connected, setConnected] = useState(false);
    const [useBackend, setUseBackend] = useState(true);

    // Intervention state
    // targetDampening: the goal we're moving towards (set by strategy)
    // currentDampening: the actual applied value (gradually moves towards target)
    // interventionHour: when the intervention was applied (affects effectiveness)
    const [targetDampening, setTargetDampening] = useState(1.0);
    const [currentDampening, setCurrentDampening] = useState(1.0);
    const [interventionHour, setInterventionHour] = useState(null);
    const [interventionMessage, setInterventionMessage] = useState(null);
    const [strategyDeployed, setStrategyDeployed] = useState(false);

    // Simulation state ref for the model
    const simulationStateRef = useRef({
        exposedPopulation: 0.05,
        infectedCount: 0,
        cumulativeReach: 0,
        peakVelocity: 0,
        timeToCritical: null,
        totalShares: 0,
        alertsTriggered: [],
    });

    // Fetch scenarios on mount
    useEffect(() => {
        if (useBackend) {
            api.getScenarios()
                .then(data => {
                    setScenarios(data.scenarios || []);
                    if (data.scenarios?.length > 0) {
                        setActiveScenario(data.scenarios[0]);
                        setActiveScenarioName(data.scenarios[0].name);
                    }
                })
                .catch(err => {
                    console.warn('Backend not available, using demo mode:', err);
                    setUseBackend(false);
                });
        }
    }, []);

    // WebSocket message handler
    const handleMessage = useCallback((data) => {
        switch (data.type) {
            case 'simulation_start':
                setSimulationStatus('running');
                break;

            case 'simulation_update':
                if (data.point) {
                    setVelocityHistory(prev => [...prev, data.point]);
                    setTimeHorizon(data.point.hour);
                }
                if (data.metrics) {
                    setMetrics(prev => ({
                        ...prev,
                        velocity: data.metrics.velocity || prev.velocity,
                        confidence: data.metrics.confidence || prev.confidence,
                        alerts: data.metrics.alerts ?? prev.alerts,
                        peak_velocity: data.metrics.peak_velocity || prev.peak_velocity,
                        time_to_critical: data.metrics.time_to_critical,
                        total_shares: data.metrics.total_shares || prev.total_shares,
                    }));
                }
                break;

            case 'simulation_complete':
                setSimulationStatus('complete');
                if (data.metrics) {
                    setMetrics(prev => ({ ...prev, ...data.metrics }));
                }
                break;

            case 'error':
                console.error('Simulation error:', data.message);
                setSimulationStatus('idle');
                break;

            case 'intervention':
                console.log('Intervention applied:', data.message);
                setInterventionMessage(data.message);
                if (data.effectiveness) {
                    setTargetDampening(Math.max(0, 1.0 - data.effectiveness));
                }
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }, []);

    // Initialize WebSocket connection
    useEffect(() => {
        if (!useBackend) return;

        const ws = createSimulationSocket({
            onMessage: handleMessage,
            onError: (err) => {
                console.error('WebSocket error:', err);
                setConnected(false);
            },
            onClose: () => {
                setConnected(false);
            },
        });

        ws.connect()
            .then(() => {
                wsRef.current = ws;
                setConnected(true);
            })
            .catch(err => {
                console.warn('WebSocket connection failed:', err);
                setUseBackend(false);
            });

        return () => {
            ws.disconnect();
        };
    }, [useBackend, handleMessage]);

    const pauseSimulation = useCallback(() => {
        if (useBackend && wsRef.current) {
            wsRef.current.pauseSimulation();
        }
        setSimulationStatus("paused");
    }, [useBackend]);

    // Reset everything for a fresh simulation
    const resetSimulation = useCallback(() => {
        const now = new Date();
        setStartTime(now);
        setTimeHorizon(0);
        setVelocityHistory(generateHistoricalBaseline(now, activeScenarioName));

        const params = getScenarioParams(activeScenarioName);
        setMetrics({
            velocity: params.initialVelocity,
            confidence: 45,
            alerts: 0,
            peak_velocity: 0,
            time_to_critical: null,
            total_shares: 0
        });

        // Reset intervention state
        setTargetDampening(1.0);
        setCurrentDampening(1.0);
        setInterventionHour(null);
        setInterventionMessage(null);
        setStrategyDeployed(false);

        // Reset simulation model state
        simulationStateRef.current = {
            exposedPopulation: 0.05,
            infectedCount: 0,
            cumulativeReach: 0,
            peakVelocity: params.initialVelocity,
            timeToCritical: null,
            totalShares: 0,
            alertsTriggered: [],
        };
    }, [activeScenarioName]);

    const stopSimulation = useCallback(() => {
        if (useBackend && wsRef.current) {
            wsRef.current.stopSimulation();
        }
        setSimulationStatus("idle");
        resetSimulation();
    }, [useBackend, resetSimulation]);

    const selectScenario = useCallback((scenarioNameOrId) => {
        const scenario = scenarios.find(
            s => s.id === scenarioNameOrId || s.name === scenarioNameOrId
        );
        if (scenario) {
            setActiveScenario(scenario);
            setActiveScenarioName(scenario.name);
        } else {
            setActiveScenarioName(scenarioNameOrId);
        }

        // Update baseline when scenario changes (only if not running)
        if (simulationStatus === 'idle') {
            const now = new Date();
            setStartTime(now);
            const newName = scenario?.name || scenarioNameOrId;
            setVelocityHistory(generateHistoricalBaseline(now, newName));
            const params = getScenarioParams(newName);
            setMetrics(prev => ({ ...prev, velocity: params.initialVelocity }));
        }
    }, [scenarios, simulationStatus]);

    // Demo mode simulation loop using realistic contagion model
    useEffect(() => {
        if (useBackend || simulationStatus !== "running") return;

        const scenarioParams = getScenarioParams(activeScenarioName);

        const intervalMs = 1000 / simulationSpeed;
        const interval = setInterval(() => {
            setTimeHorizon(prevTime => {
                const newTime = prevTime + 1;
                const state = simulationStateRef.current;

                // === GRADUAL DAMPENING EFFECT ===
                // Dampening moves gradually towards target over ~6-8 hours for 72h sim
                let effectiveDampening = currentDampening;
                if (targetDampening !== currentDampening) {
                    const dampeningStep = 0.08; // Slower: 8% per hour (reaches target in ~8-10h)
                    if (currentDampening > targetDampening) {
                        effectiveDampening = Math.max(targetDampening, currentDampening - dampeningStep);
                    } else {
                        effectiveDampening = Math.min(targetDampening, currentDampening + dampeningStep);
                    }
                    setCurrentDampening(effectiveDampening);
                }

                // === TIMING BONUS: Earlier intervention = more effective ===
                // Day 1 (0-24h): Early intervention bonus up to 25%
                // Day 2 (24-48h): Neutral
                // Day 3 (48-72h): Late intervention penalty up to 25%
                let timingMultiplier = 1.0;
                if (interventionHour !== null && strategyDeployed) {
                    const hoursActive = newTime - interventionHour;
                    // Bonus/penalty based on when intervention was applied
                    const earlinessBonus = Math.max(-0.25, Math.min(0.25, (36 - interventionHour) / 144));
                    // Effect builds up over time (full effect after 12 hours)
                    const buildupFactor = Math.min(1, hoursActive / 12);
                    timingMultiplier = 1 + (earlinessBonus * buildupFactor);
                }

                // Apply timing bonus to dampening
                const adjustedDampening = Math.max(0.1, effectiveDampening * timingMultiplier);

                // === CONTAGION MODEL (3-day crisis lifecycle) ===
                // Phase 1 (0-24h): Rapid growth
                // Phase 2 (24-48h): Peak and plateau
                // Phase 3 (48-72h): Natural decay or sustained if not addressed

                // Momentum now follows a bell curve peaking around scenario's peakHour
                const peakHour = scenarioParams.peakHour || 18;
                const distanceFromPeak = Math.abs(newTime - peakHour);
                const growthPhase = newTime <= peakHour ? 1 : 0.7; // Faster growth, slower decay
                const momentum = Math.max(0.15, growthPhase * Math.exp(-distanceFromPeak / 30));

                const effectiveTransmissionRate = scenarioParams.baseTransmissionRate * momentum * adjustedDampening;

                // SIR-model: new_infections = β * S * I
                const susceptible = 1 - state.exposedPopulation;
                const newExposures = effectiveTransmissionRate * susceptible * state.exposedPopulation;
                state.exposedPopulation = Math.min(0.95, state.exposedPopulation + newExposures);

                // Sharing behavior
                const newSharers = Math.floor(newExposures * TOTAL_POPULATION * 0.3);
                state.infectedCount += newSharers;
                state.totalShares += newSharers;
                state.cumulativeReach += newSharers * (5 + Math.floor(Math.random() * 10));

                // === VELOCITY CALCULATION (matches backend) ===
                const baseVelocity = (newExposures * 1000);
                const momentumBonus = momentum * scenarioParams.peakVelocityTarget * 0.3;
                const infectedBonus = Math.min(20, state.infectedCount * 0.015);

                let velocity = (baseVelocity * scenarioParams.severityBoost + momentumBonus + infectedBonus);

                // Apply dampening to velocity growth (not instant - affects rate of change)
                velocity = velocity * adjustedDampening;

                // Ensure velocity doesn't go below a floor based on existing exposure
                const exposureFloor = state.exposedPopulation * 15;
                velocity = Math.max(exposureFloor, velocity);

                // Add minimal noise
                velocity += (Math.random() - 0.5) * 2;
                velocity = Math.max(0, Math.min(100, velocity));

                // Track peak
                if (velocity > state.peakVelocity) {
                    state.peakVelocity = velocity;
                }

                // Track time to critical
                if (velocity > 80 && state.timeToCritical === null) {
                    state.timeToCritical = newTime;
                }

                // === UPDATE CHART ===
                setVelocityHistory(prev => [
                    ...prev,
                    {
                        time: formatSimTime(startTime, newTime),
                        velocity: Math.round(velocity * 10) / 10,
                        hour: newTime
                    }
                ]);

                // === METRICS ===
                const dataPoints = newTime;
                const baseConfidence = 45 + Math.min(40, dataPoints * 2);
                const confidence = Math.min(95, Math.round(baseConfidence));

                // Alerts
                if (velocity > 80 && !state.alertsTriggered.includes('critical')) {
                    state.alertsTriggered.push('critical');
                } else if (velocity > 50 && !state.alertsTriggered.includes('high')) {
                    state.alertsTriggered.push('high');
                } else if (velocity > 30 && !state.alertsTriggered.includes('elevated')) {
                    state.alertsTriggered.push('elevated');
                }

                setMetrics({
                    velocity: Math.round(velocity * 10) / 10,
                    confidence: confidence,
                    peak_velocity: Math.round(state.peakVelocity * 10) / 10,
                    time_to_critical: state.timeToCritical,
                    total_shares: state.totalShares,
                    alerts: state.alertsTriggered.length,
                    reach: state.cumulativeReach,
                    exposedPercent: Math.round(state.exposedPopulation * 100),
                });

                // Auto-complete at 24 hours but don't crash
                if (newTime >= DURATION_HOURS) {
                    setSimulationStatus('complete');
                    return DURATION_HOURS; // Stop incrementing
                }

                return newTime;
            });
        }, intervalMs);

        return () => clearInterval(interval);
    }, [useBackend, simulationStatus, simulationSpeed, startTime, activeScenarioName,
        targetDampening, currentDampening, interventionHour, strategyDeployed]);

    // Start simulation
    const runSimulation = useCallback(() => {
        // Handle resume from pause
        if (simulationStatus === 'paused' && !useBackend) {
            setSimulationStatus("running");
            return;
        }

        // Full reset for new simulation
        resetSimulation();

        if (useBackend && wsRef.current && connected) {
            wsRef.current.startSimulation(
                activeScenario?.id,
                activeScenarioName,
                simulationSpeed,
                24
            );
        } else {
            setSimulationStatus("running");
        }
    }, [simulationStatus, useBackend, connected, activeScenario, activeScenarioName, simulationSpeed, resetSimulation]);

    // Apply intervention (called when user deploys strategy)
    const applyIntervention = useCallback((effectiveness) => {
        // Don't allow intervention before simulation starts
        if (simulationStatus !== 'running') {
            console.warn('Cannot deploy strategy before simulation starts');
            return false;
        }

        // effectiveness: 0.0 to 1.0
        const newTarget = Math.max(0.1, 1.0 - effectiveness);
        setTargetDampening(newTarget);
        setInterventionHour(timeHorizon);
        setStrategyDeployed(true);

        if (effectiveness > 0) {
            setInterventionMessage(`Strategy deployed at hour ${timeHorizon}. Effect building gradually...`);
        } else {
            setInterventionMessage('Observing natural crisis trajectory.');
        }

        return true;
    }, [simulationStatus, timeHorizon]);

    const value = {
        // Scenarios
        scenarios,
        activeScenario,
        activeScenarioName,
        setActiveScenario: selectScenario,

        // Simulation state
        simulationStatus,
        simulationSpeed,
        setSimulationSpeed,
        runSimulation,
        pauseSimulation,
        stopSimulation,

        // Metrics
        metrics,
        velocityHistory,
        timeHorizon,

        // Connection state
        connected,
        useBackend,
        setUseBackend,

        // Intervention
        dampeningFactor: currentDampening,
        targetDampening,
        interventionMessage,
        strategyDeployed,
        interventionHour,
        applyIntervention,
    };

    return (
        <SimulationContext.Provider value={value}>
            {children}
        </SimulationContext.Provider>
    );
};
