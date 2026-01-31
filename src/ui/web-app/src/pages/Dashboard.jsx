import React from 'react';
import { SimulationProvider, useSimulation } from '../context/SimulationContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, BrainCircuit, AlertTriangle, ShieldCheck, CheckCircle, Play, Pause, RotateCcw, Clock } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

// --- HEADER COMPONENT ---
function SimulationHeader() {
    const {
        scenarios,
        activeScenarioName,
        setActiveScenario,
        runSimulation,
        pauseSimulation,
        stopSimulation,
        simulationStatus,
        simulationSpeed,
        setSimulationSpeed,
        timeHorizon
    } = useSimulation();

    const speedOptions = [1, 2, 4, 8, 16]; // Higher speeds for 72h simulation
    const isActive = simulationStatus === 'running' || simulationStatus === 'paused';

    // Format time as Day X, HH:00 for better 72h readability
    const formatTimeDisplay = (hours) => {
        const day = Math.floor(hours / 24) + 1;
        const hourOfDay = hours % 24;
        return `Day ${day}, ${hourOfDay}h`;
    };

    return (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Crisis Simulator</h1>
                <p className="text-muted-foreground mt-1">72-hour stress test • Predict the storm before it hits.</p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
                {/* Time & Speed Controls (visible when running or paused) */}
                {isActive && (
                    <>
                        <div className={`flex items-center gap-2 text-sm ${simulationStatus === 'running' ? 'text-amber-400 animate-pulse' : 'text-muted-foreground'}`}>
                            <Clock className="h-4 w-4" />
                            <span className="font-mono">{formatTimeDisplay(timeHorizon)}</span>
                            {simulationStatus === 'paused' && (
                                <span className="text-xs bg-muted px-2 py-0.5 rounded">PAUSED</span>
                            )}
                        </div>
                        {/* Speed Controls */}
                        <div className="flex items-center gap-1 bg-muted/50 rounded-md p-1">
                            <span className="text-xs text-muted-foreground px-1">Speed:</span>
                            {speedOptions.map(speed => (
                                <button
                                    key={speed}
                                    onClick={() => setSimulationSpeed(speed)}
                                    className={`px-2 py-1 text-xs rounded transition-colors ${simulationSpeed === speed
                                        ? 'bg-primary text-primary-foreground'
                                        : 'hover:bg-muted text-muted-foreground'
                                        }`}
                                >
                                    {speed}x
                                </button>
                            ))}
                        </div>
                    </>
                )}

                {/* Scenario Selector */}
                <select
                    className="bg-card border border-border rounded-md px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary"
                    value={activeScenarioName}
                    onChange={(e) => setActiveScenario(e.target.value)}
                    disabled={isActive}
                >
                    {scenarios && scenarios.length > 0 ? (
                        scenarios.map(scenario => (
                            <option key={scenario.id} value={scenario.name}>
                                {scenario.name}
                            </option>
                        ))
                    ) : (
                        <>
                            <option>Data Leak Rumor</option>
                            <option>Service Outage</option>
                            <option>Executive Misconduct (Deepfake)</option>
                        </>
                    )}
                </select>

                {/* Control Buttons based on status */}
                {simulationStatus === 'idle' && (
                    <Button onClick={runSimulation}>
                        <Play className="mr-2 h-4 w-4 fill-current" /> Run Simulation
                    </Button>
                )}
                {simulationStatus === 'running' && (
                    <>
                        <Button onClick={pauseSimulation} variant="secondary">
                            <Pause className="mr-2 h-4 w-4 fill-current" /> Pause
                        </Button>
                        <Button onClick={stopSimulation} variant="outline" size="icon" title="Reset">
                            <RotateCcw className="h-4 w-4" />
                        </Button>
                    </>
                )}
                {simulationStatus === 'paused' && (
                    <>
                        <Button onClick={runSimulation}>
                            <Play className="mr-2 h-4 w-4 fill-current" /> Resume
                        </Button>
                        <Button onClick={stopSimulation} variant="outline" size="icon" title="Reset">
                            <RotateCcw className="h-4 w-4" />
                        </Button>
                    </>
                )}
                {simulationStatus === 'complete' && (
                    <>
                        <div className="flex items-center gap-2 text-sm text-green-400">
                            <CheckCircle className="h-4 w-4" />
                            <span className="font-mono">{formatTimeDisplay(timeHorizon)}</span>
                            <span className="text-xs bg-green-500/20 px-2 py-0.5 rounded">COMPLETED</span>
                        </div>
                        <Button onClick={stopSimulation} variant="outline">
                            <RotateCcw className="mr-2 h-4 w-4" /> Reset
                        </Button>
                        <Button onClick={runSimulation}>
                            <Play className="mr-2 h-4 w-4 fill-current" /> New Simulation
                        </Button>
                    </>
                )}
            </div>
        </div>
    );
}

// --- METRICS ROW (Simplified to 3) ---
function KeyMetrics() {
    const { metrics, simulationStatus } = useSimulation();
    const { velocity, confidence, alerts } = metrics;

    return (
        <div className="grid gap-4 md:grid-cols-3">
            <Card className={`bg-card/50 backdrop-blur ${velocity > 80 ? 'border-destructive' : ''}`}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Velocity of Contagion</CardTitle>
                    <Activity className={`h-4 w-4 ${velocity > 50 ? 'text-destructive' : 'text-muted-foreground'}`} />
                </CardHeader>
                <CardContent>
                    <div className={`text-3xl font-bold tabular-nums ${velocity > 80 ? 'text-destructive' : velocity > 50 ? 'text-amber-500' : ''}`}>
                        {velocity.toFixed(0)}
                        <span className="text-lg text-muted-foreground">/100</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                        {velocity > 80 ? '⚠️ Critical threshold breached' : velocity > 50 ? 'Elevated risk' : 'Within normal range'}
                    </p>
                </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Model Confidence</CardTitle>
                    <BrainCircuit className="h-4 w-4 text-purple-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-3xl font-bold text-purple-400 tabular-nums">{confidence}%</div>
                    <div className="flex items-center mt-1 gap-1">
                        <ShieldCheck className="h-3 w-3 text-green-500" />
                        <p className="text-xs text-muted-foreground">Adversarial Validated</p>
                    </div>
                </CardContent>
            </Card>

            <Card className={`bg-card/50 backdrop-blur ${alerts > 0 ? 'border-amber-500/50' : ''}`}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
                    <AlertTriangle className={`h-4 w-4 ${alerts > 0 ? 'text-amber-500 animate-pulse' : 'text-muted-foreground'}`} />
                </CardHeader>
                <CardContent>
                    <div className="text-3xl font-bold tabular-nums">{alerts}</div>
                    <p className="text-xs text-muted-foreground mt-1">
                        {alerts > 0 ? 'Immediate action required' : 'No pending alerts'}
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}

// --- MAIN CHART (The Core Visual) ---
function VelocityChart() {
    const { velocityHistory, simulationStatus, metrics } = useSimulation();

    return (
        <Card className="bg-card/50 backdrop-blur">
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle>Risk Trajectory</CardTitle>
                        <CardDescription>
                            {simulationStatus === 'running'
                                ? 'Simulating rumor spread in real-time...'
                                : 'Click "Run Simulation" to see the predicted impact.'}
                        </CardDescription>
                    </div>
                    {metrics.velocity > 80 && (
                        <span className="text-xs bg-destructive/20 text-destructive px-2 py-1 rounded-full">
                            Threshold Breached
                        </span>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <div className="h-[280px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={velocityHistory} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorVelocity" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="time" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                            <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                labelStyle={{ color: 'hsl(var(--muted-foreground))' }}
                                formatter={(value) => [`${value}`, 'Velocity']}
                            />
                            {/* Critical threshold line */}
                            <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "Critical", fill: '#ef4444', fontSize: 10, position: 'right' }} />

                            {/* Day markers (vertical lines at 24h and 48h) */}
                            {velocityHistory.some(p => p.hour >= 24) && (
                                <ReferenceLine
                                    x={velocityHistory.find(p => p.hour === 24)?.time}
                                    stroke="#6366f1"
                                    strokeDasharray="3 3"
                                    label={{ value: "Day 2", fill: '#6366f1', fontSize: 10, position: 'top' }}
                                />
                            )}
                            {velocityHistory.some(p => p.hour >= 48) && (
                                <ReferenceLine
                                    x={velocityHistory.find(p => p.hour === 48)?.time}
                                    stroke="#8b5cf6"
                                    strokeDasharray="3 3"
                                    label={{ value: "Day 3", fill: '#8b5cf6', fontSize: 10, position: 'top' }}
                                />
                            )}

                            <Area type="monotone" dataKey="velocity" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorVelocity)" animationDuration={300} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

// --- STRATEGY OPTIONS PER SCENARIO TYPE ---
// Each scenario includes a "Do Nothing" option to observe natural crisis trajectory
const SCENARIO_STRATEGIES = {
    "Data Leak": [
        {
            id: "do_nothing",
            action: "Do Nothing - Monitor Situation",
            reasoning: "Allow the situation to develop naturally while gathering more information. Risk: Crisis may escalate without intervention.",
            effectiveness: 0, // No velocity reduction - crisis unfolds naturally
            risk: "critical"
        },
        {
            id: "transparency",
            action: "Issue proactive security clarification",
            reasoning: "Signal cluster indicates customer anxiety about data practices. Early transparency recommended.",
            effectiveness: 0.7,
            risk: "low"
        },
        {
            id: "investigation",
            action: "Launch internal investigation before public statement",
            reasoning: "Gather facts first to avoid premature statements that may need correction.",
            effectiveness: 0.4,
            risk: "medium"
        },
        {
            id: "third_party",
            action: "Engage third-party security auditor for public verification",
            reasoning: "External validation builds stronger trust than internal assurances.",
            effectiveness: 0.85,
            risk: "low"
        }
    ],
    "Outage": [
        {
            id: "do_nothing",
            action: "Do Nothing - Monitor Situation",
            reasoning: "Allow the situation to develop naturally. Risk: Customer frustration may compound without communication.",
            effectiveness: 0,
            risk: "critical"
        },
        {
            id: "status_updates",
            action: "Post real-time status updates on official channels",
            reasoning: "High volume of 'app down' mentions detected. Transparency reduces panic.",
            effectiveness: 0.6,
            risk: "low"
        },
        {
            id: "compensation",
            action: "Announce service credit compensation proactively",
            reasoning: "Preemptive goodwill gesture can turn negative sentiment to positive.",
            effectiveness: 0.75,
            risk: "medium"
        }
    ],
    "Deepfake": [
        {
            id: "do_nothing",
            action: "Do Nothing - Monitor Situation",
            reasoning: "Allow the situation to develop naturally. Risk: Misinformation may spread unchecked without response.",
            effectiveness: 0,
            risk: "critical"
        },
        {
            id: "legal_denial",
            action: "Prepare legal statement denying video authenticity",
            reasoning: "Deepfake indicators detected. Swift denial critical for stock stability.",
            effectiveness: 0.5,
            risk: "medium"
        },
        {
            id: "technical_proof",
            action: "Release technical analysis proving video manipulation",
            reasoning: "Forensic evidence is more convincing than verbal denial.",
            effectiveness: 0.8,
            risk: "low"
        },
        {
            id: "executive_live",
            action: "Schedule live executive appearance to contrast with fake",
            reasoning: "Real-time presence counters deepfake narrative effectively.",
            effectiveness: 0.9,
            risk: "high"
        }
    ]
};

// --- DECISION PANEL (AI Insight + Governance Combined) ---
function DecisionPanel() {
    const {
        activeScenarioName,
        simulationStatus,
        metrics,
        applyIntervention,
        interventionMessage,
        strategyDeployed,
        interventionHour,
        connected,
        useBackend
    } = useSimulation();

    const [status, setStatus] = React.useState("pending"); // pending, approved
    const [selectedStrategyId, setSelectedStrategyId] = React.useState(null);

    // Get strategies for current scenario
    const getStrategies = () => {
        if (activeScenarioName.includes("Data Leak")) {
            return SCENARIO_STRATEGIES["Data Leak"];
        } else if (activeScenarioName.includes("Outage")) {
            return SCENARIO_STRATEGIES["Outage"];
        } else {
            return SCENARIO_STRATEGIES["Deepfake"];
        }
    };

    const strategies = getStrategies();
    const selectedStrategy = strategies.find(s => s.id === selectedStrategyId) || strategies[0];

    // Reset status when scenario changes or simulation restarts
    React.useEffect(() => {
        setStatus("pending");
        setSelectedStrategyId(strategies[0]?.id || null);
    }, [activeScenarioName]);

    // Reset when simulation restarts (idle state)
    React.useEffect(() => {
        if (simulationStatus === 'idle') {
            setStatus("pending");
        }
    }, [simulationStatus]);

    // Sync with context strategyDeployed state
    React.useEffect(() => {
        if (strategyDeployed && status === 'pending') {
            setStatus('approved');
        }
    }, [strategyDeployed]);

    const handleApprove = async () => {
        // Check if simulation is running
        if (simulationStatus !== 'running') {
            alert('Please start the simulation first before deploying a strategy.');
            return;
        }

        try {
            // Call backend API
            if (useBackend && connected) {
                await api.recordDecision("inc-001", "APPROVE", "user-1", selectedStrategy.action);
            }

            // Apply local intervention
            const success = applyIntervention(selectedStrategy.effectiveness);
            if (success) {
                setStatus('approved');
            }
        } catch (e) {
            console.error("Failed to record decision:", e);
            const success = applyIntervention(selectedStrategy.effectiveness);
            if (success) {
                setStatus('approved');
            }
        }
    };

    const getRiskBadgeColor = (risk) => {
        switch (risk) {
            case 'low': return 'bg-green-500/20 text-green-400';
            case 'medium': return 'bg-amber-500/20 text-amber-400';
            case 'high': return 'bg-destructive/20 text-destructive';
            case 'critical': return 'bg-red-600/30 text-red-400 border border-red-500/50';
            default: return 'bg-muted text-muted-foreground';
        }
    };

    return (
        <Card className={`bg-card/50 backdrop-blur border-l-4 ${status === 'approved' ? 'border-l-green-500' : 'border-l-purple-500'}`}>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">AI Recommendation</CardTitle>
                    <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full">
                        {metrics.confidence}% confidence
                    </span>
                </div>
                <CardDescription>Human-in-the-Loop Governance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Strategy Selection */}
                {status === 'pending' && strategies.length > 1 && (
                    <div className="space-y-2">
                        <p className="text-xs font-medium text-muted-foreground">Select Response Strategy:</p>
                        <div className="space-y-2">
                            {strategies.map((strategy) => (
                                <div
                                    key={strategy.id}
                                    onClick={() => setSelectedStrategyId(strategy.id)}
                                    className={`p-3 rounded-md border cursor-pointer transition-all ${selectedStrategyId === strategy.id
                                        ? 'border-purple-500 bg-purple-500/10'
                                        : 'border-border/50 bg-muted/20 hover:bg-muted/40'
                                        }`}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <p className="text-sm font-medium">{strategy.action}</p>
                                        <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${getRiskBadgeColor(strategy.risk)}`}>
                                            {strategy.risk} risk
                                        </span>
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">{strategy.reasoning}</p>
                                    <p className="text-xs text-purple-400 mt-1">
                                        Effectiveness: {Math.round(strategy.effectiveness * 100)}% velocity reduction
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Single strategy display when only one option */}
                {status === 'pending' && strategies.length === 1 && (
                    <div className="p-3 bg-muted/30 rounded-md border border-border/50">
                        <p className="text-sm font-medium">{selectedStrategy.action}</p>
                        <p className="text-xs text-muted-foreground mt-2">
                            <strong>Reasoning:</strong> {selectedStrategy.reasoning}
                        </p>
                    </div>
                )}

                {/* Approved state */}
                {status === 'approved' && (
                    <div className="space-y-3">
                        <div className={`p-3 rounded border text-sm flex items-center gap-2 ${selectedStrategy.id === 'do_nothing'
                            ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                            : 'bg-green-500/10 border-green-500/30 text-green-400'
                            }`}>
                            <CheckCircle className="h-4 w-4" />
                            {selectedStrategy.id === 'do_nothing'
                                ? 'Observing natural crisis trajectory.'
                                : `Strategy deployed${interventionHour !== null ? ` at hour ${interventionHour}` : ''}. Effect building gradually.`
                            }
                        </div>
                        <div className="p-2 bg-muted/30 rounded text-xs">
                            <p className="font-medium text-foreground">Active Strategy:</p>
                            <p className="text-muted-foreground">{selectedStrategy.action}</p>
                            <p className="text-purple-400 mt-1">
                                {selectedStrategy.id === 'do_nothing'
                                    ? 'No velocity dampening - crisis unfolds naturally'
                                    : (interventionMessage || `Target: ${Math.round(selectedStrategy.effectiveness * 100)}% velocity reduction (gradual effect)`)
                                }
                            </p>
                            {interventionHour !== null && interventionHour <= 8 && selectedStrategy.id !== 'do_nothing' && (
                                <p className="text-green-400 mt-1 text-xs">✓ Early intervention bonus active</p>
                            )}
                        </div>
                    </div>
                )}

            </CardContent>
            {status === 'pending' && (
                <CardFooter className="flex justify-end border-t border-border/30 pt-4">
                    <Button onClick={handleApprove} className={selectedStrategy.id === 'do_nothing' ? 'bg-amber-600 hover:bg-amber-700' : ''}>
                        <CheckCircle className="mr-2 h-4 w-4" /> Deploy Strategy
                    </Button>
                </CardFooter>
            )}
        </Card>
    );
}
import { api } from '../services/api';

import { SignalFeed } from '../components/dashboard/SignalFeed';
import { DebateViewer } from '../components/dashboard/DebateViewer';
import { ExplainabilityPanel } from '../components/dashboard/ExplainabilityPanel';

// --- MAIN DASHBOARD ---
export default function Dashboard() {
    return (
        <SimulationProvider>
            <div className="space-y-6 pb-8">
                <SimulationHeader />
                <KeyMetrics />

                {/* Top Row: Main Chart & Signals */}
                <div className="grid gap-6 lg:grid-cols-5">
                    <div className="lg:col-span-3 space-y-6">
                        <VelocityChart />
                        <DebateViewer />
                    </div>
                    <div className="lg:col-span-2 space-y-6">
                        <DecisionPanel />
                        <SignalFeed />
                        <ExplainabilityPanel />
                    </div>
                </div>
            </div>
        </SimulationProvider>
    );
}
