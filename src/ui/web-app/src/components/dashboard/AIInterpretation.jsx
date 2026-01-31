import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, Search, AlertOctagon, Loader2, BrainCircuit, RefreshCw, BarChart3 } from "lucide-react";
import { useSimulation } from '../../context/SimulationContext';
import { api } from '@/services/api';

// Simple Badge component
const SimpleBadge = ({ children, variant = 'default', onClick }) => {
    const colors = {
        default: 'bg-primary text-primary-foreground',
        destructive: 'bg-destructive/10 text-destructive border-destructive/20',
        outline: 'text-foreground border-border',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer'
    };
    return (
        <span
            onClick={onClick}
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors ${colors[variant] || colors.default}`}
        >
            {children}
        </span>
    );
};

export default function AIInterpretation() {
    const { metrics, activeScenarioName, simulationStatus } = useSimulation();
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(false);
    const [lastUpdated, setLastUpdated] = useState(null);

    const fetchAnalysis = async () => {
        setLoading(true);
        try {
            const data = await api.getAIReasoning();
            if (data) {
                setAnalysis(data);
                setLastUpdated(new Date());
            }
        } catch (err) {
            console.error("Failed to load AI interpretation", err);
        } finally {
            setLoading(false);
        }
    };

    // Auto-fetch ONLY on initial scenario load, then manual
    useEffect(() => {
        if (activeScenarioName && !analysis) {
            fetchAnalysis();
        }
    }, [activeScenarioName]);

    if (!activeScenarioName) {
        return (
            <Card className="bg-card/50 backdrop-blur h-full border-l-4 border-l-slate-300">
                <CardContent className="flex flex-col items-center justify-center h-full text-muted-foreground p-6">
                    <BrainCircuit className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">Select a scenario to activate AI reasoning.</p>
                </CardContent>
            </Card>
        );
    }

    const confidenceScore = analysis?.confidence === 'High' ? 88 : analysis?.confidence === 'Moderate' ? 65 : 40;

    return (
        <Card className="bg-card/50 backdrop-blur h-full border-l-4 border-l-purple-500 transition-all duration-500 flex flex-col">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            Explainable AI Insight
                            {loading && <Loader2 className="h-3 w-3 animate-spin text-purple-400" />}
                        </CardTitle>
                        <CardDescription>Signal Interpretation Engine (Module B)</CardDescription>
                    </div>
                    <Activity className={`h-4 w-4 text-purple-500 ${simulationStatus === 'running' ? 'animate-pulse' : ''}`} />
                </div>
            </CardHeader>
            <CardContent className="space-y-4 flex-1">
                {/* Classification Section */}
                <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1 flex justify-between">
                        <span>Primary Classification</span>
                        {lastUpdated && <span className="text-[10px] opacity-70">Updated: {lastUpdated.toLocaleTimeString()}</span>}
                    </div>
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                        <span className="text-lg font-bold text-foreground">
                            {analysis?.classification || "Ready to Analyze"}
                        </span>
                    </div>

                    {/* Visual Confidence Meter */}
                    {analysis && (
                        <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground">
                                <span>Model Confidence</span>
                                <span>{confidenceScore}% ({analysis.confidence})</span>
                            </div>
                            <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-1000 ${confidenceScore > 80 ? 'bg-purple-500' : 'bg-amber-500'}`}
                                    style={{ width: `${confidenceScore}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Clusters Section */}
                <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-2">Detected Logic Clusters</div>
                    <div className="flex flex-wrap gap-1">
                        {!analysis ? (
                            <span className="text-xs text-muted-foreground italic">Waiting for analysis...</span>
                        ) : (
                            analysis.clusters.map((cluster, i) => (
                                <SimpleBadge key={i} variant={i === 0 ? 'destructive' : 'secondary'}>
                                    #{cluster.replace(/\s+/g, '_')}
                                </SimpleBadge>
                            ))
                        )}
                        {analysis?.clusters.length === 0 && !loading && analysis && (
                            <span className="text-xs text-muted-foreground">No significant patterns detected.</span>
                        )}
                    </div>
                </div>

                {/* Reasoning Trace */}
                <div className="p-3 bg-muted/30 rounded-md border border-border/50 animate-in fade-in zoom-in duration-300">
                    <div className="flex items-start gap-2">
                        <Search className="h-4 w-4 text-purple-400 mt-0.5 shrink-0" />
                        <div>
                            <p className="text-xs font-medium text-foreground">Reasoning Trace:</p>
                            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                                {analysis?.reasoning || "Click 'Analyze Live Signals' to process the current data stream."}
                            </p>
                        </div>
                    </div>
                </div>
            </CardContent>

            <CardFooter className="pt-2 pb-4">
                <Button
                    variant="outline"
                    size="sm"
                    className="w-full gap-2 border-purple-500/20 hover:bg-purple-500/10 hover:text-purple-400 transition-all font-medium"
                    onClick={fetchAnalysis}
                    disabled={loading}
                >
                    {loading ? (
                        <>
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Analyzing Stream...
                        </>
                    ) : (
                        <>
                            <RefreshCw className="h-3 w-3" />
                            Analyze Live Signals
                        </>
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
}
