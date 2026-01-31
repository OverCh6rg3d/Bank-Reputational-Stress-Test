import React, { useEffect, useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Twitter, MessageSquare, Newspaper, AlertOctagon } from "lucide-react";
import { api } from '@/services/api';
import { useSimulation } from '@/context/SimulationContext';

export function SignalFeed() {
    const { activeScenarioName, simulationStatus } = useSimulation();
    const [signals, setSignals] = useState([]);
    const scrollRef = useRef(null);

    // Poll for new signals when simulation is running
    useEffect(() => {
        let interval;

        const fetchSignals = async () => {
            try {
                // In real app, we might pass a timestamp to get only new ones
                const newSignals = await api.getSignals(10);
                setSignals(prev => {
                    // Simple dedupe based on content (since IDs might be unstable in demo)
                    const existing = new Set(prev.map(s => s.content_text));
                    const uniqueNew = newSignals.filter(s => !existing.has(s.content_text));
                    return [...uniqueNew, ...prev].slice(0, 50); // Keep last 50
                });
            } catch (err) {
                console.error("Failed to fetch signals", err);
            }
        };

        if (simulationStatus === 'running') {
            fetchSignals(); // Initial fetch
            interval = setInterval(fetchSignals, 5000); // Poll every 5s
        } else {
            // Initial load even if idle
            fetchSignals();
        }

        return () => clearInterval(interval);
    }, [simulationStatus, activeScenarioName]);

    const getPlatformIcon = (platform) => {
        switch (platform?.toLowerCase()) {
            case 'x_style': return <Twitter className="h-4 w-4 text-blue-400" />;
            case 'reddit_style': return <MessageSquare className="h-4 w-4 text-orange-500" />;
            case 'news_portal': return <Newspaper className="h-4 w-4 text-slate-500" />;
            default: return <MessageSquare className="h-4 w-4" />;
        }
    };

    return (
        <Card className="h-[400px] flex flex-col bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <AlertOctagon className="h-4 w-4 text-red-500" />
                        Live Signal Feed
                    </CardTitle>
                    <Badge variant="outline" className="text-[10px] font-mono border-blue-500/50 text-blue-400">
                        SYNTHETIC DATA ONLY
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 p-0">
                <ScrollArea className="h-full px-4">
                    <div className="space-y-3 pb-4">
                        {signals.length === 0 ? (
                            <div className="text-center text-muted-foreground py-8 text-sm">
                                Waiting for signals...
                            </div>
                        ) : (
                            signals.map((signal, i) => (
                                <div key={i} className="p-3 rounded-lg border border-border/50 bg-background/50 text-sm">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            {getPlatformIcon(signal.platform_source)}
                                            <span className="font-semibold text-xs text-muted-foreground">
                                                {signal.platform_source?.replace('_style', '') || 'Social'}
                                            </span>
                                        </div>
                                        <span className="text-[10px] text-muted-foreground font-mono">
                                            {new Date(signal.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <p className="mb-2 leading-relaxed text-foreground/90">
                                        {signal.content_text}
                                    </p>
                                    <div className="flex gap-2">
                                        {signal.hashtags?.map(tag => (
                                            <span key={tag} className="text-[10px] text-blue-400">#{tag}</span>
                                        ))}
                                    </div>
                                    <div className="mt-2 flex items-center justify-between border-t border-border/30 pt-2">
                                        <div className="flex gap-4 text-[10px] text-muted-foreground">
                                            <span>Risk: {Math.round(signal.gt_virality_potential || 0)}/100</span>
                                            <span>Sentiment: {Math.round((signal.gt_sentiment || 0) * 100)}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
