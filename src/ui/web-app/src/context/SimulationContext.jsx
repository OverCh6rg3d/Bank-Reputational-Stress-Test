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

// Generate initial historical baseline data (past 6 hours before T=0)
const generateHistoricalBaseline = (startTime) => {
    const history = [];
    for (let i = -6; i <= 0; i++) {
        const baseVelocity = 8 + Math.random() * 6;
        history.push({
            time: formatSimTime(startTime, i),
            velocity: Math.round(baseVelocity),
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
        confidence: 85,
        alerts: 0,
        peak_velocity: 0,
        time_to_critical: null,
        total_shares: 0,
    });

    // Initial chart data with historical baseline
    const [velocityHistory, setVelocityHistory] = useState(() => generateHistoricalBaseline(new Date()));

    // WebSocket connection
    const wsRef = useRef(null);
    const [connected, setConnected] = useState(false);
    const [useBackend, setUseBackend] = useState(true); // Toggle for demo mode

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

    // Actions
    const runSimulation = useCallback(() => {
        if (simulationStatus === 'paused' && !useBackend) {
            setSimulationStatus("running");
            return;
        }

        // Reset state
        const now = new Date();
        setStartTime(now);
        setTimeHorizon(0);
        setVelocityHistory(generateHistoricalBaseline(now));
        setMetrics({ velocity: 12, confidence: 85, alerts: 0, peak_velocity: 0, time_to_critical: null, total_shares: 0 });

        if (useBackend && wsRef.current && connected) {
            // Start via WebSocket
            wsRef.current.startSimulation(
                activeScenario?.id,
                activeScenarioName,
                simulationSpeed,
                24 // duration hours
            );
        } else {
            // Fallback to demo mode
            setSimulationStatus("running");
        }
    }, [simulationStatus, useBackend, connected, activeScenario, activeScenarioName, simulationSpeed]);

    const pauseSimulation = useCallback(() => {
        if (useBackend && wsRef.current) {
            wsRef.current.pauseSimulation();
        }
        setSimulationStatus("paused");
    }, [useBackend]);

    const stopSimulation = useCallback(() => {
        if (useBackend && wsRef.current) {
            wsRef.current.stopSimulation();
        }
        setSimulationStatus("idle");
        const now = new Date();
        setStartTime(now);
        setTimeHorizon(0);
        setVelocityHistory(generateHistoricalBaseline(now));
        setMetrics({ velocity: 12, confidence: 85, alerts: 0, peak_velocity: 0, time_to_critical: null, total_shares: 0 });
    }, [useBackend]);

    const selectScenario = useCallback((scenarioNameOrId) => {
        const scenario = scenarios.find(
            s => s.id === scenarioNameOrId || s.name === scenarioNameOrId
        );
        if (scenario) {
            setActiveScenario(scenario);
            setActiveScenarioName(scenario.name);
        } else {
            // Fallback for demo mode
            setActiveScenarioName(scenarioNameOrId);
        }
    }, [scenarios]);

    // Demo mode simulation loop (fallback when backend not available)
    useEffect(() => {
        if (useBackend || simulationStatus !== "running") return;

        const intervalMs = 1000 / simulationSpeed;
        const interval = setInterval(() => {
            setTimeHorizon(t => {
                const newTime = t + 1;

                setVelocityHistory(prev => {
                    const lastVelocity = prev[prev.length - 1]?.velocity || 12;
                    const growthFactor = Math.max(0.5, 8 - newTime * 0.15);
                    const increase = Math.random() * growthFactor + 1.5;
                    const newVelocity = Math.min(100, lastVelocity + increase);

                    return [
                        ...prev,
                        {
                            time: formatSimTime(startTime, newTime),
                            velocity: Math.round(newVelocity),
                            hour: newTime
                        }
                    ];
                });

                setMetrics(prev => {
                    const newVelocity = Math.min(100, prev.velocity + Math.random() * 4 + 1);
                    return {
                        ...prev,
                        velocity: newVelocity,
                        peak_velocity: Math.max(prev.peak_velocity, newVelocity),
                        alerts: newVelocity > 50 ? prev.alerts + (Math.random() > 0.6 ? 1 : 0) : prev.alerts
                    };
                });

                return newTime;
            });
        }, intervalMs);

        return () => clearInterval(interval);
    }, [useBackend, simulationStatus, simulationSpeed, startTime]);

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
    };

    return (
        <SimulationContext.Provider value={value}>
            {children}
        </SimulationContext.Provider>
    );
};
