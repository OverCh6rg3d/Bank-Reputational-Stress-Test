import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, BrainCircuit, TrendingUp, AlertTriangle, ShieldCheck } from "lucide-react";
import { useSimulation } from '../../context/SimulationContext';

export default function RiskMetrics() {
    const { metrics } = useSimulation();
    const { velocity, confidence, impact, alerts } = metrics;

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="bg-card/50 backdrop-blur">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Contagion Velocity</CardTitle>
                    <Activity className={`h-4 w-4 ${velocity > 50 ? 'text-destructive' : 'text-muted-foreground'}`} />
                </CardHeader>
                <CardContent>
                    <div className={`text-2xl font-bold ${velocity > 50 ? 'text-destructive' : ''}`}>{velocity.toFixed(1)} / 100</div>
                    <p className="text-xs text-muted-foreground">Real-time spread rate</p>
                </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Model Confidence</CardTitle>
                    <BrainCircuit className="h-4 w-4 text-purple-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-purple-500">{confidence}%</div>
                    <div className="flex items-center mt-1 space-x-1">
                        <ShieldCheck className="h-3 w-3 text-green-500" />
                        <p className="text-xs text-muted-foreground">Adversarial Validated</p>
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Projected Impact</CardTitle>
                    <TrendingUp className="h-4 w-4 text-amber-500" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold text-amber-500">{impact}</div>
                    <p className="text-xs text-muted-foreground">Sentiment Shift Potential</p>
                </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
                    <AlertTriangle className={`h-4 w-4 ${alerts > 0 ? 'text-red-500 animate-pulse' : 'text-muted-foreground'}`} />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{alerts}</div>
                    <p className="text-xs text-muted-foreground">Requires attention</p>
                </CardContent>
            </Card>
        </div>
    );
}
