import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

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
    const [activeScenario, setActiveScenario] = useState("Data Leak Rumor");
    const [simulationStatus, setSimulationStatus] = useState("idle"); // idle, running, paused
    const [simulationSpeed, setSimulationSpeed] = useState(1); // 0.5x, 1x, 2x, 4x
    const [timeHorizon, setTimeHorizon] = useState(0); // Hours elapsed in simulation (T+X)

    // Store the start time when simulation begins
    const [startTime, setStartTime] = useState(() => new Date());

    // Risk Metrics
    const [metrics, setMetrics] = useState({
        velocity: 12,
        confidence: 85,
        alerts: 0
    });

    // Initial chart data with historical baseline
    const [velocityHistory, setVelocityHistory] = useState(() => generateHistoricalBaseline(new Date()));



    // Actions
    const runSimulation = useCallback(() => {
        if (simulationStatus === 'paused') {
            // Resume from pause
            setSimulationStatus("running");
            return;
        }
        // Fresh start
        const now = new Date();
        setStartTime(now);
        setTimeHorizon(0);
        setVelocityHistory(generateHistoricalBaseline(now));
        setMetrics({ velocity: 12, confidence: 85, alerts: 0 });
        setSimulationStatus("running");
    }, [simulationStatus]);

    const pauseSimulation = useCallback(() => {
        setSimulationStatus("paused");
    }, []);

    const stopSimulation = useCallback(() => {
        setSimulationStatus("idle");
        // Reset to current time with fresh historical data
        const now = new Date();
        setStartTime(now);
        setTimeHorizon(0);
        setVelocityHistory(generateHistoricalBaseline(now));
        setMetrics({ velocity: 12, confidence: 85, alerts: 0 });
    }, []);

    // Simulation Loop
    useEffect(() => {
        let interval;
        if (simulationStatus === "running") {
            const intervalMs = 1000 / simulationSpeed;

            interval = setInterval(() => {
                setTimeHorizon(t => {
                    const newTime = t + 1;

                    // Update velocity history with new data point
                    setVelocityHistory(prev => {
                        const lastVelocity = prev[prev.length - 1]?.velocity || 12;
                        // Velocity increases with diminishing returns over time
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

                    return newTime;
                });

                // Update Metrics
                setMetrics(prev => {
                    const newVelocity = Math.min(100, prev.velocity + Math.random() * 4 + 1);
                    return {
                        ...prev,
                        velocity: newVelocity,
                        alerts: newVelocity > 50 ? prev.alerts + (Math.random() > 0.6 ? 1 : 0) : prev.alerts
                    };
                });

            }, intervalMs);
        }
        return () => clearInterval(interval);
    }, [simulationStatus, simulationSpeed, startTime]);

    const value = {
        activeScenario,
        setActiveScenario,
        simulationStatus,
        simulationSpeed,
        setSimulationSpeed,
        runSimulation,
        pauseSimulation,
        stopSimulation,
        metrics,
        velocityHistory,
        timeHorizon
    };

    return (
        <SimulationContext.Provider value={value}>
            {children}
        </SimulationContext.Provider>
    );
};
