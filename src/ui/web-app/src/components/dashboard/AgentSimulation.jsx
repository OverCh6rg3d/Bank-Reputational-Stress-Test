import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { useSimulation } from '../../context/SimulationContext';
import { ResponsiveContainer, Tooltip as RechartsTooltip, PieChart, Pie, Cell, Legend } from 'recharts'; // Keeping pie chart as fallback/secondary view if needed

export default function AgentSimulation() {
    const { agents } = useSimulation();

    // Stats calculation
    const neutralCount = agents.filter(a => a.status === 'neutral').length;
    const infectedCount = agents.filter(a => a.status === 'infected').length;
    const spreadingCount = agents.filter(a => a.status === 'spreading').length;

    return (
        <Card className="col-span-3 lg:col-span-3 bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="text-sm font-medium">Agent Contagion Network</CardTitle>
                        <CardDescription>Real-time ABM Visualization</CardDescription>
                    </div>
                    <div className="flex gap-2 text-[10px]">
                        <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-slate-500"></div> Neutral</span>
                        <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-500"></div> Exposed</span>
                        <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500"></div> Spreading</span>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="relative h-[220px] w-full border border-border/30 rounded-md bg-black/20 overflow-hidden">
                    {/* Agent Particles */}
                    {agents.map((agent) => (
                        <div
                            key={agent.id}
                            className={`absolute w-2 h-2 rounded-full transition-colors duration-500 ease-in-out ${agent.status === 'neutral' ? 'bg-slate-500/50' :
                                    agent.status === 'infected' ? 'bg-amber-500 animate-pulse' :
                                        'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.6)]'
                                }`}
                            style={{
                                left: `${agent.x}%`,
                                top: `${agent.y}%`,
                            }}
                        />
                    ))}
                </div>
                <div className="flex justify-between mt-4 text-xs text-muted-foreground px-2">
                    <div>Population: {agents.length}</div>
                    <div className="text-destructive font-mono">Infection Rate: {Math.round(((infectedCount + spreadingCount) / agents.length) * 100)}%</div>
                </div>
            </CardContent>
        </Card>
    );
}
