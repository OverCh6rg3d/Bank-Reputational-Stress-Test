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

    const speedOptions = [0.5, 1, 2, 4];
    const isActive = simulationStatus === 'running' || simulationStatus === 'paused';

    return (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Crisis Simulator</h1>
                <p className="text-muted-foreground mt-1">Predict the storm before it hits.</p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
                {/* Time & Speed Controls (visible when running or paused) */}
                {isActive && (
                    <>
                        <div className={`flex items-center gap-2 text-sm ${simulationStatus === 'running' ? 'text-amber-400 animate-pulse' : 'text-muted-foreground'}`}>
                            <Clock className="h-4 w-4" />
                            <span className="font-mono">T+{timeHorizon}h</span>
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

                {/* Control Buttons */}
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
                            />
                            <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "Critical", fill: '#ef4444', fontSize: 10, position: 'right' }} />
                            <Area type="monotone" dataKey="velocity" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorVelocity)" animationDuration={300} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

// --- DECISION PANEL (AI Insight + Governance Combined) ---
function DecisionPanel() {
    const { activeScenarioName, simulationStatus, metrics } = useSimulation();
    const [status, setStatus] = React.useState("pending");

    // Reset status when scenario changes or simulation restarts
    React.useEffect(() => {
        setStatus("pending");
    }, [activeScenarioName, simulationStatus]);

    const getRecommendation = () => {
        if (activeScenarioName.includes("Data Leak")) {
            return {
                action: "Issue proactive security clarification",
                reasoning: "Signal cluster indicates customer anxiety about data practices. Early transparency recommended."
            };
        } else if (activeScenarioName.includes("Outage")) {
            return {
                action: "Post real-time status updates on official channels.",
                reasoning: "High volume of 'app down' mentions detected. Transparency reduces panic."
            };
        } else {
            return {
                action: "Prepare legal statement denying video authenticity.",
                reasoning: "Deepfake indicators detected. Swift denial critical for stock stability."
            };
        }
    };

    const rec = getRecommendation();

    const handleApprove = async () => {
        try {
            await api.recordDecision("inc-001", "APPROVE", "user-1", rec.action);
            setStatus('approved');
        } catch (e) {
            console.error("Failed to record decision:", e);
        }
    };

    return (
        <Card className={`bg-card/50 backdrop-blur border-l-4 ${status === 'approved' ? 'border-l-green-500' :
            status === 'rejected' ? 'border-l-destructive' : 'border-l-purple-500'
            }`}>
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
                <div className="p-3 bg-muted/30 rounded-md border border-border/50">
                    <p className="text-sm font-medium">{rec.action}</p>
                    <p className="text-xs text-muted-foreground mt-2">
                        <strong>Reasoning:</strong> {rec.reasoning}
                    </p>
                </div>

                {status === 'approved' && (
                    <div className="p-3 bg-green-500/10 rounded border border-green-500/30 text-sm text-green-400 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" /> Strategy approved. Mitigation active.
                    </div>
                )}
                {status === 'rejected' && (
                    <div className="p-3 bg-destructive/10 rounded border border-destructive/30 text-sm text-destructive">
                        Strategy rejected. Awaiting alternative approach.
                    </div>
                )}
            </CardContent>
            {status === 'pending' && (
                <CardFooter className="flex gap-2 justify-end border-t border-border/30 pt-4">
                    <Button
                        variant="outline"
                        onClick={() => setStatus('rejected')}
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    >
                        Reject
                    </Button>
                    <Button onClick={handleApprove}>
                        <CheckCircle className="mr-2 h-4 w-4" /> Approve Strategy
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
