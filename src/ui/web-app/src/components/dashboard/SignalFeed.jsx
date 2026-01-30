import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useSimulation } from '../../context/SimulationContext';

export default function SignalFeed() {
    const { signals } = useSimulation();

    return (
        <Card className="bg-card/50 backdrop-blur h-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Recent Detected Signals</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                    {signals.map((item, i) => (
                        <div key={i} className={`flex items-start space-x-4 border-l-2 pl-3 pb-3 last:pb-0 ${item.sentiment === 'Negative' ? 'border-l-destructive' :
                                item.sentiment === 'Positive' ? 'border-l-green-500' : 'border-l-muted'
                            }`}>
                            <div className="space-y-1 w-full">
                                <div className="flex justify-between">
                                    <p className="text-xs font-semibold text-primary">{item.source}</p>
                                    <span className="text-[10px] text-muted-foreground">{item.time}</span>
                                </div>
                                <p className="text-xs text-muted-foreground line-clamp-2">
                                    {item.text}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
