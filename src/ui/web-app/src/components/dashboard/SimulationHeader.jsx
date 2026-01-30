import React from 'react';
import { Button } from "@/components/ui/button";
import { Download, Activity, Play, Square } from "lucide-react";
import { useSimulation } from '../../context/SimulationContext';

export default function SimulationHeader() {
    const { activeScenario, setActiveScenario, runSimulation, stopSimulation, simulationStatus } = useSimulation();

    return (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Simulation Dashboard</h1>
                <p className="text-muted-foreground mt-1">Live monitoring of reputational risk vectors.</p>
            </div>
            <div className="flex items-center gap-2 bg-card/50 p-2 rounded-lg border border-border/50 backdrop-blur">
                <span className="text-sm font-medium text-muted-foreground px-2">Scenario:</span>
                <select
                    className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
                    value={activeScenario}
                    onChange={(e) => setActiveScenario(e.target.value)}
                    disabled={simulationStatus === 'running'}
                >
                    <option>Data Leak Rumor</option>
                    <option>Service Outage</option>
                    <option>Executive Misconduct (Deepfake)</option>
                </select>
                <Button size="sm" variant="outline" className="ml-2 h-8 hidden lg:flex">
                    <Download className="mr-2 h-3.5 w-3.5" />
                    Export Briefing
                </Button>

                {simulationStatus === 'running' ? (
                    <Button size="sm" onClick={stopSimulation} variant="destructive" className="ml-2 h-8">
                        <Square className="mr-2 h-3.5 w-3.5 fill-current" />
                        Stop
                    </Button>
                ) : (
                    <Button size="sm" onClick={runSimulation} className="ml-2 h-8">
                        <Play className="mr-2 h-3.5 w-3.5 fill-current" />
                        Run Simulation
                    </Button>
                )}

            </div>
        </div>
    );
}
