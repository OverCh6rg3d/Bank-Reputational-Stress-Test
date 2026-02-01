import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Brain, ArrowRight, Activity, TrendingDown, Bot, Shield, Loader2 } from "lucide-react";
import { useSimulation } from '@/context/SimulationContext';

/**
 * AI Reasoning Engine - Shows REAL computed metrics from the simulation
 * 
 * Values are derived from:
 * - Velocity Score: Current simulation velocity
 * - Sentiment Analysis: Average sentiment from live signals
 * - Signal Volume: Total signals processed
 * - Confidence Level: Model's certainty (inversely related to velocity)
 */

export function ExplainabilityPanel() {
    const { metrics, simulationStatus, activeScenarioName, liveSignals } = useSimulation();

    const velocity = metrics?.velocity || 0;
    const confidence = metrics?.confidence || 0;
    const avgSentiment = metrics?.avgSentiment || 0;
    const signalCount = metrics?.signalCount || 0;
    const alerts = metrics?.alerts || 0;

    // Compute real factors from simulation data
    const factors = [
        {
            name: "Velocity Score",
            value: Math.min(100, velocity),
            impact: velocity > 65 ? "High" : velocity > 30 ? "Medium" : "Low",
            icon: Activity
        },
        {
            name: "Sentiment Analysis",
            // Convert sentiment from -1 to 1 range to 0-100 impact
            value: Math.round(Math.abs(avgSentiment) * 100),
            impact: avgSentiment < -0.6 ? "High" : avgSentiment < -0.3 ? "Medium" : "Low",
            icon: TrendingDown
        },
        {
            name: "Signal Volume",
            // Signal volume tracks velocity directly (Issue 5)
            // Higher velocity = higher volume, lower velocity = stable value
            value: Math.min(100, Math.round(velocity)),
            impact: velocity >= 65 ? "High" : velocity >= 30 ? "Medium" : "Low",
            icon: Bot
        },
        {
            name: "Model Confidence",
            value: confidence,
            impact: confidence > 70 ? "High" : confidence > 40 ? "Medium" : "Low",
            icon: Shield
        }
    ];

    // Generate reasoning text based on actual metrics
    const generateReasoning = () => {
        if (simulationStatus === 'idle') {
            return "Awaiting simulation start. Run a scenario to begin AI analysis.";
        }

        if (signalCount < 3) {
            return "Collecting initial signals... Need more data points for confident analysis.";
        }

        const parts = [];

        // Velocity analysis
        if (velocity > 65) {
            parts.push(`CRITICAL: Velocity at ${velocity.toFixed(1)}% indicates rapid viral spread.`);
        } else if (velocity > 30) {
            parts.push(`ELEVATED: Velocity at ${velocity.toFixed(1)}% shows growing momentum.`);
        } else {
            parts.push(`LOW: Velocity at ${velocity.toFixed(1)}% suggests contained spread.`);
        }

        // Sentiment analysis
        if (avgSentiment < -0.6) {
            parts.push(`Sentiment extremely negative (${(avgSentiment * 100).toFixed(0)}%), suggesting high emotional amplification.`);
        } else if (avgSentiment < -0.3) {
            parts.push(`Sentiment moderately negative (${(avgSentiment * 100).toFixed(0)}%).`);
        } else {
            parts.push(`Sentiment relatively neutral (${(avgSentiment * 100).toFixed(0)}%).`);
        }

        // Signal volume
        parts.push(`Analyzed ${signalCount} signals across platforms.`);

        // Confidence statement
        if (confidence > 70) {
            parts.push(`High model confidence (${confidence}%) based on consistent signal patterns.`);
        } else if (confidence > 40) {
            parts.push(`Moderate confidence (${confidence}%). Recommend monitoring closely.`);
        } else {
            parts.push(`Low confidence (${confidence}%). Early stage - more data needed.`);
        }

        return parts.join(' ');
    };

    // Generate summary based on scenario and velocity
    const getSummary = () => {
        if (simulationStatus === 'idle') {
            return "Waiting for simulation to begin...";
        }

        if (velocity > 65) {
            return `Risk Level: CRITICAL due to rapid velocity in "${activeScenarioName}" scenario.`;
        } else if (velocity > 30) {
            return `Risk Level: ELEVATED - Monitoring "${activeScenarioName}" scenario closely.`;
        } else {
            return `Risk Level: LOW - "${activeScenarioName}" scenario under control.`;
        }
    };

    const getProgressColor = (impact) => {
        switch (impact) {
            case 'High': return 'bg-red-500';
            case 'Medium': return 'bg-amber-500';
            case 'Low': return 'bg-green-500';
            default: return 'bg-blue-500';
        }
    };

    const getImpactColor = (impact) => {
        switch (impact) {
            case 'High': return 'text-red-400';
            case 'Medium': return 'text-amber-400';
            case 'Low': return 'text-green-400';
            default: return 'text-blue-400';
        }
    };

    return (
        <Card className="bg-card/50 backdrop-blur h-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="h-4 w-4 text-cyan-500" />
                    AI Reasoning Engine
                    {simulationStatus === 'running' && (
                        <Loader2 className="h-3 w-3 animate-spin text-cyan-400 ml-auto" />
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className={`text-sm font-medium mb-4 ${velocity > 65 ? 'text-red-400' :
                    velocity > 30 ? 'text-amber-400' :
                        'text-green-400'
                    }`}>
                    {getSummary()}
                </p>

                <div className="space-y-4 mb-6">
                    {factors.map(f => {
                        const IconComponent = f.icon;
                        return (
                            <div key={f.name} className="space-y-1">
                                <div className="flex justify-between items-center text-xs">
                                    <span className="text-muted-foreground flex items-center gap-1.5">
                                        <IconComponent className="h-3 w-3" />
                                        {f.name}
                                    </span>
                                    <span className={getImpactColor(f.impact)}>
                                        {f.value}% • {f.impact}
                                    </span>
                                </div>
                                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-500 ${getProgressColor(f.impact)}`}
                                        style={{ width: `${f.value}%` }}
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="bg-muted/50 rounded-lg p-3 border border-border/50">
                    <p className="text-xs font-semibold text-muted-foreground mb-1 flex items-center gap-1">
                        <ArrowRight className="h-3 w-3" /> LOGICAL TRACE
                    </p>
                    <p className="text-xs leading-relaxed opacity-80 font-mono">
                        {generateReasoning()}
                    </p>
                </div>
            </CardContent>
        </Card>
    );
}
