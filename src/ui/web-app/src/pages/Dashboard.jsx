import React from 'react';
import { useSimulation } from '../context/SimulationContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, BrainCircuit, AlertTriangle, ShieldCheck, CheckCircle, Play, Pause, RotateCcw, Clock, Brain, Shield, MessageSquare, Users, Zap, TrendingDown, Loader2 } from "lucide-react";
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

// --- DECISION PANEL (AI-Powered Recommendations) ---
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
        useBackend,
        liveSignals
    } = useSimulation();

    const [status, setStatus] = React.useState("pending"); // pending, approved
    const [selectedStrategyIdx, setSelectedStrategyIdx] = React.useState(0);
    const [aiStrategies, setAiStrategies] = React.useState([]);
    const [aiReasoning, setAiReasoning] = React.useState("");
    const [loading, setLoading] = React.useState(false);
    const [isAiGenerated, setIsAiGenerated] = React.useState(false);
    const lastFetchSignalCount = React.useRef(0); // Track last fetch point (Issue 2)

    const velocity = metrics?.velocity || 0;
    const confidence = metrics?.confidence || 0;
    const signalCount = metrics?.signalCount || 0;
    const avgSentiment = metrics?.avgSentiment || 0;

    // Get urgency level based on current velocity
    const getUrgency = () => {
        if (velocity >= 65) return { level: 'CRITICAL', color: 'text-red-400', bg: 'bg-red-500/20' };
        if (velocity >= 30) return { level: 'ELEVATED', color: 'text-amber-400', bg: 'bg-amber-500/20' };
        return { level: 'MONITORING', color: 'text-green-400', bg: 'bg-green-500/20' };
    };
    const urgency = getUrgency();

    // Fallback strategies if API fails with dynamic effectiveness
    const getFallbackStrategies = () => [
        { title: "Issue Official Statement", description: "Release transparent communication addressing concerns.", effectiveness: Math.floor(70 + Math.random() * 15), icon: "message" },
        { title: "Activate Crisis Team", description: "Deploy dedicated response team for real-time monitoring.", effectiveness: Math.floor(65 + Math.random() * 15), icon: "users" },
        { title: "Engage Key Influencers", description: "Coordinate with trusted voices to counter misinformation.", effectiveness: Math.floor(60 + Math.random() * 10), icon: "trending-down" }
    ];
    const FALLBACK_STRATEGIES = getFallbackStrategies();

    // Fetch AI recommendations - refetch every 5 signals (Issue 2)
    React.useEffect(() => {
        const fetchRecommendations = async () => {
            if (simulationStatus !== 'running') return;
            if (signalCount < 3) return; // Wait for initial signals

            // Only refetch every 10 signals after first fetch (User Request)
            const shouldFetch = lastFetchSignalCount.current === 0 ||
                (signalCount - lastFetchSignalCount.current >= 10);
            if (!shouldFetch) return;

            setLoading(true);
            lastFetchSignalCount.current = signalCount;

            try {
                const recentSignalTexts = liveSignals.slice(0, 5).map(s => s.content_text || '');

                const response = await fetch('http://localhost:8000/api/recommendations/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        scenario_name: activeScenarioName,
                        velocity: velocity,
                        sentiment: avgSentiment,
                        signal_count: signalCount,
                        recent_signals: recentSignalTexts
                    })
                });

                const data = await response.json();

                if (data.strategies && data.strategies.length > 0) {
                    setAiStrategies(data.strategies);
                    setAiReasoning(data.ai_reasoning || "");
                    setIsAiGenerated(data.generated === true);
                } else {
                    setAiStrategies(getFallbackStrategies());
                    setAiReasoning("Using default strategies.");
                    setIsAiGenerated(false);
                }
            } catch (error) {
                console.error("Failed to fetch AI recommendations:", error);
                setAiStrategies(getFallbackStrategies());
                setAiReasoning("AI service unavailable - using default strategies.");
                setIsAiGenerated(false);
            } finally {
                setLoading(false);
            }
        };

        fetchRecommendations();
    }, [simulationStatus, signalCount, activeScenarioName, velocity, avgSentiment, liveSignals]);

    // Reset when scenario changes
    React.useEffect(() => {
        setStatus("pending");
        setSelectedStrategyIdx(0);
        setAiStrategies([]);
        setAiReasoning("");
        lastFetchSignalCount.current = 0;
    }, [activeScenarioName]);

    // Reset when simulation stops (Issue 4)
    React.useEffect(() => {
        if (simulationStatus === 'idle') {
            setStatus("pending");
            setAiStrategies([]);
            setAiReasoning("");
            setIsAiGenerated(false);
            lastFetchSignalCount.current = 0;
        }
    }, [simulationStatus]);

    // Sync with context strategyDeployed state
    React.useEffect(() => {
        if (strategyDeployed && status === 'pending') {
            setStatus('approved');
        }
    }, [strategyDeployed]);

    const selectedStrategy = aiStrategies[selectedStrategyIdx] || FALLBACK_STRATEGIES[0];

    const handleApprove = async () => {
        if (simulationStatus !== 'running') {
            alert('Please start the simulation first before deploying a strategy.');
            return;
        }

        try {
            if (useBackend && connected) {
                await api.recordDecision("inc-001", "APPROVE", "user-1", selectedStrategy.title);
            }

            // Convert effectiveness from percentage to decimal
            const effDecimal = (selectedStrategy.effectiveness || 70) / 100;
            const success = applyIntervention(effDecimal);
            if (success) {
                setStatus('approved');
            }
        } catch (e) {
            console.error("Failed to record decision:", e);
            const effDecimal = (selectedStrategy.effectiveness || 70) / 100;
            const success = applyIntervention(effDecimal);
            if (success) {
                setStatus('approved');
            }
        }
    };

    const getIconComponent = (iconName) => {
        switch (iconName) {
            case 'shield': return Shield;
            case 'message': return MessageSquare;
            case 'users': return Users;
            case 'alert': return AlertTriangle;
            case 'zap': return Zap;
            case 'trending-down': return TrendingDown;
            default: return Shield;
        }
    };

    return (
        <Card className={`bg-card/50 backdrop-blur border-l-4 h-full ${status === 'approved' ? 'border-l-green-500' : 'border-l-purple-500'}`}>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <CardTitle className="text-lg">AI Recommendation</CardTitle>
                        {isAiGenerated && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-mono">
                                GPT-4o
                            </span>
                        )}
                        {simulationStatus === 'running' && (
                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${urgency.bg} ${urgency.color}`}>
                                {urgency.level}
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {signalCount > 0 && (
                            <span className="text-[10px] text-muted-foreground">
                                {signalCount} signals analyzed
                            </span>
                        )}
                        <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full">
                            {confidence}% confidence
                        </span>
                    </div>
                </div>
                <CardDescription>
                    {simulationStatus === 'idle'
                        ? 'Run simulation to generate AI recommendations'
                        : loading
                            ? 'Generating AI recommendations...'
                            : velocity >= 65
                                ? '⚠️ Immediate action recommended'
                                : velocity >= 30
                                    ? 'Consider deploying response strategy'
                                    : 'Monitoring situation - action optional'
                    }
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Loading state */}
                {loading && (
                    <div className="flex items-center justify-center py-8 text-muted-foreground">
                        <Loader2 className="h-6 w-6 animate-spin mr-2" />
                        <span className="text-sm">Analyzing signals with GPT-4o...</span>
                    </div>
                )}

                {/* AI Reasoning */}
                {!loading && aiReasoning && status === 'pending' && (
                    <div className="p-3 bg-cyan-500/10 rounded-md border border-cyan-500/30">
                        <p className="text-xs font-semibold text-cyan-400 mb-1 flex items-center gap-1">
                            <Brain className="h-3 w-3" /> AI Analysis
                        </p>
                        <p className="text-xs text-muted-foreground">{aiReasoning}</p>
                    </div>
                )}

                {/* Strategy Selection */}
                {status === 'pending' && aiStrategies.length > 0 && !loading && (
                    <div className="space-y-2">
                        <p className="text-xs font-medium text-muted-foreground">Select Response Strategy:</p>
                        <div className="space-y-2">
                            {aiStrategies.map((strategy, idx) => {
                                const IconComp = getIconComponent(strategy.icon);
                                return (
                                    <div
                                        key={idx}
                                        onClick={() => setSelectedStrategyIdx(idx)}
                                        className={`p-3 rounded-md border cursor-pointer transition-all ${selectedStrategyIdx === idx
                                            ? 'border-purple-500 bg-purple-500/10'
                                            : 'border-border/50 bg-muted/20 hover:bg-muted/40'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex items-center gap-2">
                                                <IconComp className="h-4 w-4 text-purple-400" />
                                                <p className="text-sm font-medium">{strategy.title}</p>
                                            </div>
                                            <span className="text-xs px-2 py-0.5 rounded-full shrink-0 bg-purple-500/20 text-purple-400">
                                                {strategy.effectiveness}% effective
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1 ml-6">{strategy.description}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Waiting for simulation */}
                {simulationStatus === 'idle' && !loading && aiStrategies.length === 0 && (
                    <div className="py-6 text-center text-muted-foreground">
                        <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Run simulation to generate AI recommendations</p>
                    </div>
                )}

                {/* Approved state */}
                {status === 'approved' && (
                    <div className="space-y-3">
                        <div className="p-3 rounded border text-sm flex items-center gap-2 bg-green-500/10 border-green-500/30 text-green-400">
                            <CheckCircle className="h-4 w-4" />
                            Strategy deployed{interventionHour !== null ? ` at hour ${interventionHour}` : ''}. Effect building gradually.
                        </div>
                        <div className="p-2 bg-muted/30 rounded text-xs">
                            <p className="font-medium text-foreground">Active Strategy:</p>
                            <p className="text-muted-foreground">{selectedStrategy.title}</p>
                            <p className="text-purple-400 mt-1">
                                {interventionMessage || `Target: ${selectedStrategy.effectiveness}% velocity reduction (gradual effect)`}
                            </p>
                            {interventionHour !== null && interventionHour <= 8 && (
                                <p className="text-green-400 mt-1 text-xs">✓ Early intervention bonus active</p>
                            )}
                        </div>
                    </div>
                )}

            </CardContent>
            {status === 'pending' && aiStrategies.length > 0 && !loading && (
                <CardFooter className="flex justify-end border-t border-border/30 pt-4">
                    <Button onClick={handleApprove}>
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

// Wrapper to conditionally show DebateViewer based on velocity
// Once triggered, it stays visible for the rest of the simulation
function ConditionalDebateViewer() {
    const { metrics, simulationStatus } = useSimulation();
    const velocity = metrics?.velocity || 0;
    const [debateTriggered, setDebateTriggered] = React.useState(false);

    // Trigger debate when velocity crosses 50
    React.useEffect(() => {
        if (velocity >= 50 && !debateTriggered) {
            setDebateTriggered(true);
        }
    }, [velocity, debateTriggered]);

    // Reset trigger when simulation resets
    React.useEffect(() => {
        if (simulationStatus === 'idle') {
            setDebateTriggered(false);
        }
    }, [simulationStatus]);

    // Show debate viewer if triggered
    if (!debateTriggered) {
        return null;
    }

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <DebateViewer />
        </div>
    );
}

// --- MAIN DASHBOARD ---
export default function Dashboard() {
    return (
        <div className="space-y-6 pb-8">
            <SimulationHeader />
            <KeyMetrics />

            {/* Top Row: Chart + Live Signal Feed side-by-side */}
            <div className="grid gap-6 lg:grid-cols-5">
                <div className="lg:col-span-3">
                    <VelocityChart />
                </div>
                <div className="lg:col-span-2 h-[450px]">
                    <SignalFeed />
                </div>
            </div>

            {/* Second Row: Decision Panel + AI Reasoning */}
            <div className="grid gap-6 lg:grid-cols-2">
                <DecisionPanel />
                <ExplainabilityPanel />
            </div>

            {/* Debate Viewer - appears when velocity exceeds threshold */}
            <ConditionalDebateViewer />
        </div>
    );
}
