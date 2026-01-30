import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useSimulation } from '../../context/SimulationContext';

export default function ContagionChart() {
    const { velocityHistory } = useSimulation();

    return (
        <Card className="col-span-4 bg-card/50 backdrop-blur">
            <CardHeader>
                <CardTitle>Risk Velocity Over Time</CardTitle>
                <CardDescription>
                    Predictive modeling of rumor spread over the next 4 hours.
                </CardDescription>
            </CardHeader>
            <CardContent className="pl-2">
                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                            data={velocityHistory}
                            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                        >
                            <defs>
                                <linearGradient id="colorVelocity" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                            <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} domain={[0, 100]} />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                            />
                            <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "Critical Threshold", fill: '#ef4444', fontSize: 10 }} />
                            <Area type="monotone" dataKey="velocity" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorVelocity)" animationDuration={500} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}
