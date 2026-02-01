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

// Default simulation duration (hours)
const DEFAULT_DURATION_HOURS = 72;
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
    "Fraud/Scam": {
        severity: "HIGH",
        severityBoost: 1.3,
        baseTransmissionRate: 0.10,
        initialVelocity: 20,
        peakVelocityTarget: 80,
        peakHour: 16
    },
    "Sentiment Shift": {
        severity: "MEDIUM",
        severityBoost: 0.95,
        baseTransmissionRate: 0.05,
        initialVelocity: 10,
        peakVelocityTarget: 50,
        peakHour: 20
    },
    "Service": {
        severity: "MEDIUM",
        severityBoost: 1.05,
        baseTransmissionRate: 0.07,
        initialVelocity: 14,
        peakVelocityTarget: 60,
        peakHour: 10
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
    if (scenarioName.includes("Data Leak") || scenarioName.includes("Leak") || scenarioName.includes("Breach")) {
        return SCENARIO_PARAMS["Data Leak"];
    } else if (scenarioName.includes("Outage") || scenarioName.includes("Down") || scenarioName.includes("ATM") || scenarioName.includes("Service")) {
        return SCENARIO_PARAMS["Outage"];
    } else if (scenarioName.includes("Deepfake") || scenarioName.includes("Executive") || scenarioName.includes("Misinformation")) {
        return SCENARIO_PARAMS["Deepfake"];
    } else if (scenarioName.includes("Fraud") || scenarioName.includes("Scam") || scenarioName.includes("Phishing") || scenarioName.includes("OTP") || scenarioName.includes("Exploit") || scenarioName.includes("Bot")) {
        return SCENARIO_PARAMS["Fraud/Scam"];
    } else if (scenarioName.includes("Sentiment") || scenarioName.includes("Fee") || scenarioName.includes("Competitor") || scenarioName.includes("Backlash") || scenarioName.includes("Service Meltdown")) {
        return SCENARIO_PARAMS["Sentiment Shift"];
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
    const [durationHours, setDurationHours] = useState(DEFAULT_DURATION_HOURS);

    // Store the start time when simulation begins
    const [startTime, setStartTime] = useState(() => new Date());

    // Risk Metrics
    const [metrics, setMetrics] = useState({
        velocity: 12,
        confidence: 0, // Start at 0% before simulation
        alerts: 0,
        peak_velocity: 0,
        time_to_critical: null,
        total_shares: 0,
        avgSentiment: 0,
        signalCount: 0,
    });

    // Initial chart data with historical baseline
    const [velocityHistory, setVelocityHistory] = useState(() =>
        generateHistoricalBaseline(new Date(), "Data Leak Rumor")
    );

    const [criticalAlerts, setCriticalAlerts] = useState([]);

    // Live signals that drive the simulation
    const [liveSignals, setLiveSignals] = useState([]);
    const [currentSignal, setCurrentSignal] = useState(null);

    // Intervention state
    // targetDampening: the goal we're moving towards (set by strategy)
    // currentDampening: the actual applied value (gradually moves towards target)
    // interventionHour: when the intervention was applied (affects effectiveness)
    const [targetDampening, setTargetDampening] = useState(1.0);
    const [currentDampening, setCurrentDampening] = useState(1.0);
    const [interventionHour, setInterventionHour] = useState(null);
    const [interventionMessage, setInterventionMessage] = useState(null);
    const [strategyDeployed, setStrategyDeployed] = useState(false);

    // WebSocket connection state
    const [connected, setConnected] = useState(false);
    const [useBackend, setUseBackend] = useState(true);

    // Create refs for state accessed inside closures (timer)
    // simulationStateRef: internal model state (infected, reach, etc.)
    const simulationStateRef = useRef({
        exposedPopulation: 0.05,
        infectedCount: 0,
        cumulativeReach: 0,
        peakVelocity: 0,
        timeToCritical: null,
        totalShares: 0,
        alertsTriggered: [],
    });

    const preSimulationSnapshot = useRef(null); // For resetting (Issue 7)
    const velocityRef = useRef(12); // Source of truth for velocity (shared between signals and timer)
    const timeHorizonRef = useRef(0); // Tracks current sim hour synchronously for logic
    const durationHoursRef = useRef(DEFAULT_DURATION_HOURS);
    const wsRef = useRef(null);
    const signalInjectionRef = useRef(null);
    const criticalActiveRef = useRef(false);
    const startTimeRef = useRef(startTime);
    const activeScenarioNameRef = useRef(activeScenarioName);
    const alertsCountRef = useRef(0);

    useEffect(() => {
        startTimeRef.current = startTime;
    }, [startTime]);

    useEffect(() => {
        activeScenarioNameRef.current = activeScenarioName;
    }, [activeScenarioName]);

    useEffect(() => {
        durationHoursRef.current = durationHours;
    }, [durationHours]);

    const appendAlertEntries = useCallback((count, velocityValue, alertHour) => {
        if (count <= 0) {
            return;
        }
        const scenarioName = activeScenarioNameRef.current || 'Current Scenario';
        const alertTime = formatSimTime(startTimeRef.current || new Date(), alertHour ?? (timeHorizonRef.current || 0));
        setCriticalAlerts(prev => [
            ...prev,
            ...Array.from({ length: count }).map(() => ({
                id: `alert-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                time: alertTime,
                velocity: typeof velocityValue === 'number' ? Math.round(velocityValue * 10) / 10 : null,
                scenario: scenarioName,
                message: `Alert triggered in ${scenarioName}.`
            }))
        ]);
    }, []);

    // Fetch scenarios on mount
    useEffect(() => {
        if (useBackend) {
            api.getScenarios()
                .then(data => {
                    setScenarios(data.scenarios || []);
                    if (data.scenarios?.length > 0) {
                        setActiveScenario(data.scenarios[0]);
                        setActiveScenarioName(data.scenarios[0].name);
                        setDurationHours(data.scenarios[0].duration_hours || DEFAULT_DURATION_HOURS);
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
                // Skip updates when simulation is paused
                if (simulationStatus === 'paused') {
                    return;
                }
                if (data.point) {
                    setVelocityHistory(prev => [...prev, data.point]);
                    setTimeHorizon(data.point.hour);
                    timeHorizonRef.current = data.point.hour;
                }
                if (data.metrics) {
                    const velocityValue = data.metrics.velocity;
                    if (typeof velocityValue === 'number') {
                        const isCritical = velocityValue > 80;
                        if (isCritical && !criticalActiveRef.current) {
                            const alertHour = data.point?.hour ?? timeHorizonRef.current ?? 0;
                            const scenarioName = activeScenarioNameRef.current || 'Current Scenario';
                            const alertTime = formatSimTime(startTimeRef.current || new Date(), alertHour);
                            setCriticalAlerts(prev => [
                                ...prev,
                                {
                                    id: `critical-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                                    time: alertTime,
                                    velocity: Math.round(velocityValue * 10) / 10,
                                    scenario: scenarioName,
                                    message: `Critical velocity threshold breached in ${scenarioName}.`
                                }
                            ]);
                        }
                        criticalActiveRef.current = isCritical;
                    }
                    if (typeof data.metrics.alerts === 'number') {
                        const nextCount = data.metrics.alerts;
                        if (nextCount > alertsCountRef.current) {
                            appendAlertEntries(nextCount - alertsCountRef.current, velocityValue, data.point?.hour);
                        }
                        alertsCountRef.current = nextCount;
                    }
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
                criticalActiveRef.current = false;
                alertsCountRef.current = 0;
                break;

            case 'error':
                console.error('Simulation error:', data.message);
                setSimulationStatus('idle');
                criticalActiveRef.current = false;
                alertsCountRef.current = 0;
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
        timeHorizonRef.current = 0;
        setVelocityHistory(generateHistoricalBaseline(now, activeScenarioName));

        const params = getScenarioParams(activeScenarioName);
        setMetrics({
            velocity: params.initialVelocity,
            confidence: 0, // Start at 0% - builds as simulation runs
            alerts: 0,
            peak_velocity: 0,
            time_to_critical: null,
            total_shares: 0,
            avgSentiment: 0,
            signalCount: 0,
        });

        setCriticalAlerts([]);
        criticalActiveRef.current = false;
        alertsCountRef.current = 0;

        // Reset live signals
        setLiveSignals([]);
        setCurrentSignal(null);
        if (signalInjectionRef.current) {
            clearInterval(signalInjectionRef.current);
        }

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

        // Reset velocity ref source of truth
        velocityRef.current = params.initialVelocity;
    }, [activeScenarioName]);

    // Stop simulation and restore pre-simulation state (Issue 7)
    const stopSimulation = useCallback(() => {
        if (useBackend && wsRef.current) {
            wsRef.current.stopSimulation();
        }
        setSimulationStatus("idle");

        // Restore pre-simulation snapshot if available (Issue 7)
        if (preSimulationSnapshot.current) {
            setMetrics({
                ...preSimulationSnapshot.current.metrics,
                confidence: 0, // Always reset confidence to 0 (Issue 6)
            });
            setVelocityHistory(preSimulationSnapshot.current.velocityHistory);
            setLiveSignals(preSimulationSnapshot.current.liveSignals);
            setTimeHorizon(preSimulationSnapshot.current.timeHorizon);
            timeHorizonRef.current = preSimulationSnapshot.current.timeHorizon || 0;
            preSimulationSnapshot.current = null; // Clear snapshot for next run
        } else {
            // Fallback to full reset if no snapshot
            resetSimulation();
        }

        // Reset intervention state
        setTargetDampening(1.0);
        setCurrentDampening(1.0);
        setInterventionHour(null);
        setInterventionMessage(null);
        setStrategyDeployed(false);

        // Reset velocity ref to ensure metric card resets
        // The setMetrics call above might use a snapshot, but we want to be sure
        const params = getScenarioParams(activeScenarioName);
        velocityRef.current = params.initialVelocity;
        setCriticalAlerts([]);
        criticalActiveRef.current = false;
        alertsCountRef.current = 0;
    }, [useBackend, resetSimulation, activeScenarioName]);

    // Note: Do not auto-reset on completion. Keep results visible until user resets.

    const selectScenario = useCallback((scenarioNameOrId) => {
        const scenario = scenarios.find(
            s => s.id === scenarioNameOrId || s.name === scenarioNameOrId
        );
        if (scenario) {
            setActiveScenario(scenario);
            setActiveScenarioName(scenario.name);
            setDurationHours(scenario.duration_hours || DEFAULT_DURATION_HOURS);
        } else {
            setActiveScenarioName(scenarioNameOrId);
            setDurationHours(DEFAULT_DURATION_HOURS);
        }

        // Update baseline when scenario changes (only if not running)
        if (simulationStatus === 'idle') {
            const now = new Date();
            setStartTime(now);
            const newName = scenario?.name || scenarioNameOrId;
            setVelocityHistory(generateHistoricalBaseline(now, newName));
            const params = getScenarioParams(newName);
            setMetrics(prev => ({ ...prev, velocity: params.initialVelocity }));
            setCriticalAlerts([]);
            criticalActiveRef.current = false;
            alertsCountRef.current = 0;
        }
    }, [scenarios, simulationStatus]);

    // Demo mode simulation loop using realistic contagion model
    useEffect(() => {
        if (useBackend || simulationStatus !== "running") return;

        const scenarioParams = getScenarioParams(activeScenarioName);

        const intervalMs = 1000 / simulationSpeed;
        const interval = setInterval(() => {
            // Calculate new time based on current state
            // We use the functional update just to get the prev value, but return it immediately
            // Then do logic outside. Wait, we need the new time for logic.
            // Better pattern: Use a timeRef if needed, or just trust the loop sequence.
            // Actually, we can do the logic *inside* the interval callback using the ref for state,
            // and functional update for time is fine, BUT we must move the side effects out.

            setTimeHorizon(prevTime => {
                // If complete, stop updating
                if (prevTime >= durationHoursRef.current) {
                    setSimulationStatus('complete');
                    return prevTime;
                }
                return prevTime + 1;
            });

            // NOW perform the physics and other updates based on the *expected* new time
            // Since setTimeHorizon is async, we can't read 'timeHorizon' state immediately.
            // But we know it will be prevTime + 1. 
            // To imply synchronization, we should track internal time in a Ref for the physics engine.
            const newTime = (timeHorizonRef.current || 0) + 1;
            timeHorizonRef.current = newTime;

            const state = simulationStateRef.current;
            const scenarioParams = getScenarioParams(activeScenarioName);

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
            let timingMultiplier = 1.0;
            if (interventionHour !== null && strategyDeployed) {
                const hoursActive = newTime - interventionHour;
                const earlinessBonus = Math.max(-0.25, Math.min(0.25, (36 - interventionHour) / 144));
                const buildupFactor = Math.min(1, hoursActive / 12);
                timingMultiplier = 1 + (earlinessBonus * buildupFactor);
            }
            const adjustedDampening = Math.max(0.1, effectiveDampening * timingMultiplier);

            // === CONTAGION MODEL ===
            const peakHour = scenarioParams.peakHour || 18;
            const distanceFromPeak = Math.abs(newTime - peakHour);
            const growthPhase = newTime <= peakHour ? 1 : 0.7;
            const momentum = Math.max(0.15, growthPhase * Math.exp(-distanceFromPeak / 30));

            const effectiveTransmissionRate = scenarioParams.baseTransmissionRate * momentum * adjustedDampening;
            const susceptible = 1 - state.exposedPopulation;
            const newExposures = effectiveTransmissionRate * susceptible * state.exposedPopulation;
            state.exposedPopulation = Math.min(0.95, state.exposedPopulation + newExposures);

            const newSharers = Math.floor(newExposures * TOTAL_POPULATION * 0.3);
            state.infectedCount += newSharers;
            state.totalShares += newSharers;
            state.cumulativeReach += newSharers * (5 + Math.floor(Math.random() * 10));

            // === VELOCITY CALCULATION ===
            let currentSignalVelocity = velocityRef.current;
            const baseVelocity = (newExposures * 1000);
            const momentumBonus = momentum * scenarioParams.peakVelocityTarget * 0.3;
            let modelVelocity = (baseVelocity * scenarioParams.severityBoost + momentumBonus);
            modelVelocity = modelVelocity * adjustedDampening;

            const blendedVelocity = Math.max(0, Math.min(100, currentSignalVelocity));
            velocityRef.current = blendedVelocity;
            state.peakVelocity = Math.max(state.peakVelocity, blendedVelocity);

            if (blendedVelocity > 80 && state.timeToCritical === null) {
                state.timeToCritical = newTime;
            }

            // === METRICS & ALERTS ===
            const dataPoints = newTime;
            const velocityPenalty = Math.max(0, blendedVelocity * 0.5);
            const chaosPenalty = Math.min(20, state.alertsTriggered.length * 5);
            const dataBonus = Math.min(10, dataPoints * 0.5);
            const baseConfidence = 95 - velocityPenalty - chaosPenalty + dataBonus;
            const confidence = Math.max(5, Math.min(99, Math.round(baseConfidence)));

            if (blendedVelocity > 80 && !state.alertsTriggered.includes('critical')) state.alertsTriggered.push('critical');
            else if (blendedVelocity > 50 && !state.alertsTriggered.includes('high')) state.alertsTriggered.push('high');
            else if (blendedVelocity > 30 && !state.alertsTriggered.includes('elevated')) state.alertsTriggered.push('elevated');

            // === ATOMIC UPDATE ===
            // We update both Chart data and Metrics data in the same tick 
            // using the EXACT same variables calculated above.
            const finalVelocity = Math.round(blendedVelocity * 10) / 10;

            const isCritical = finalVelocity > 80;
            if (isCritical && !criticalActiveRef.current) {
                const alertTime = formatSimTime(startTime, newTime);
                setCriticalAlerts(prev => [
                    ...prev,
                    {
                        id: `critical-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                        time: alertTime,
                        velocity: finalVelocity,
                        scenario: activeScenarioName,
                        message: `Critical velocity threshold breached in ${activeScenarioName}.`
                    }
                ]);
            }
            criticalActiveRef.current = isCritical;

            const nextAlertsCount = state.alertsTriggered.length;
            if (nextAlertsCount > alertsCountRef.current) {
                appendAlertEntries(nextAlertsCount - alertsCountRef.current, finalVelocity, newTime);
                alertsCountRef.current = nextAlertsCount;
            }

            setMetrics(prev => ({
                velocity: finalVelocity,
                confidence: confidence,
                peak_velocity: Math.max(prev.peak_velocity || 0, Math.round(state.peakVelocity * 10) / 10),
                time_to_critical: state.timeToCritical,
                total_shares: state.totalShares,
                alerts: state.alertsTriggered.length,
                reach: state.cumulativeReach,
                exposedPercent: Math.round(state.exposedPopulation * 100),
                avgSentiment: prev.avgSentiment || -0.5,
                signalCount: (prev.signalCount || 0),
            }));

            setVelocityHistory(prev => [
                ...prev,
                {
                    time: formatSimTime(startTime, newTime),
                    velocity: finalVelocity,
                    hour: newTime
                }
            ]);

            // Auto-complete at 24 hours
            if (newTime >= durationHoursRef.current) {
                setSimulationStatus('complete');
            }

        }, intervalMs);

        return () => clearInterval(interval);
    }, [useBackend, simulationStatus, simulationSpeed, startTime, activeScenarioName,
        targetDampening, currentDampening, interventionHour, strategyDeployed]);

    // Signal injection system - injects signals continuously
    // These signals drive the "live" feel and update metrics INCLUDING velocity
    // NOTE: Confidence is ONLY updated when simulation is running
    const injectSignal = useCallback((signal) => {
        // Don't inject signals when simulation is paused or complete (but allow during idle for baseline feed)
        if (simulationStatus === 'paused' || simulationStatus === 'complete') {
            return;
        }

        const signalWithMeta = {
            ...signal,
            id: `signal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
            isNew: true,
        };

        setCurrentSignal(signalWithMeta);
        setLiveSignals(prev => [signalWithMeta, ...prev].slice(0, 50)); // Keep last 50

        // Compute velocity using Exponential Moving Average (EMA) for smooth transitions
        const sentiment = signal.gt_sentiment || -0.5;
        const virality = signal.gt_virality_potential || 30;

        // Calculate velocity impact from signal
        const viralityImpact = (virality / 100) * 2;
        const sentimentImpact = Math.abs(Math.min(0, sentiment));
        const signalImpact = viralityImpact * (1 + sentimentImpact * 0.5);

        // Compute target velocity based on signal
        const currentVelocity = velocityRef.current; // Use ref as source of truth
        const signalTargetVelocity = Math.min(100, virality * 1.8 + signalImpact * 2);

        // Use EMA for smooth velocity transitions (alpha = 0.15 for gradual change)
        // Formula: newValue = alpha * target + (1 - alpha) * current
        const alpha = 0.15; // Lower = smoother, higher = more responsive
        const smoothedVelocity = alpha * signalTargetVelocity + (1 - alpha) * currentVelocity;
        const roundedVelocity = Math.round(Math.max(5, smoothedVelocity) * 10) / 10;

        // Update source of truth
        velocityRef.current = roundedVelocity;

        // Always update signal count and sentiment so the feed and metrics stay in sync
        setMetrics(prev => {
            const newSignalCount = (prev.signalCount || 0) + 1;
            const oldTotal = (prev.avgSentiment || 0) * (prev.signalCount || 0);
            const newAvgSentiment = (oldTotal + sentiment) / newSignalCount;

            // If running, let the timer loop own velocity/confidence updates
            if (simulationStatus === 'running') {
                return {
                    ...prev,
                    signalCount: newSignalCount,
                    avgSentiment: Math.round(newAvgSentiment * 100) / 100,
                };
            }

            // If NOT running (Idle/Paused), manually update UI so the feed feels alive
            const newConfidence = 0;
            return {
                ...prev,
                signalCount: newSignalCount,
                avgSentiment: Math.round(newAvgSentiment * 100) / 100,
                velocity: roundedVelocity,
                peak_velocity: Math.max(prev.peak_velocity || 0, roundedVelocity),
                confidence: newConfidence,
            };
        });

        // Keep chart and card in sync by updating the latest chart point (only when not running)
        if (simulationStatus !== 'running') {
            setVelocityHistory(prev => {
                if (!prev || prev.length === 0) {
                    return prev;
                }
                const lastIndex = prev.length - 1;
                const lastPoint = prev[lastIndex];
                const updatedPoint = {
                    ...lastPoint,
                    velocity: roundedVelocity,
                };
                return [...prev.slice(0, lastIndex), updatedPoint];
            });
        }

        // Clear "new" flag after animation
        setTimeout(() => setCurrentSignal(null), 1500);
    }, [metrics.velocity, simulationStatus]);

    // Start simulation - continues from current state (Issue 1)
    const runSimulation = useCallback(() => {
        // Handle resume from pause
        if (simulationStatus === 'paused' && !useBackend) {
            setSimulationStatus("running");
            return;
        }

        // Store pre-simulation snapshot for reset (Issue 7)
        // Only store if we don't already have one (first run)
        if (!preSimulationSnapshot.current) {
            preSimulationSnapshot.current = {
                metrics: { ...metrics },
                velocityHistory: [...velocityHistory],
                liveSignals: [...liveSignals],
                timeHorizon: timeHorizon,
            };
        }

        // Reset only intervention state, NOT metrics/velocity/signals (Issue 1)
        setTargetDampening(1.0);
        setCurrentDampening(1.0);
        setInterventionHour(null);
        setInterventionMessage(null);
        setStrategyDeployed(false);

        if (useBackend && wsRef.current && connected) {
            wsRef.current.startSimulation(
                activeScenario?.id,
                activeScenarioName,
                simulationSpeed,
                durationHoursRef.current
            );
        } else {
            setSimulationStatus("running");
        }
    }, [simulationStatus, useBackend, connected, activeScenario, activeScenarioName, simulationSpeed, metrics, velocityHistory, liveSignals, timeHorizon]);

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
        durationHours,
        criticalAlerts,

        // Live signals
        liveSignals,
        currentSignal,
        injectSignal,

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
