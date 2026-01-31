import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PlayCircle, Shield, AlertTriangle, User, Gavel } from "lucide-react";
import { api } from '@/services/api';

export function DebateViewer() {
    const [transcript, setTranscript] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [consensus, setConsensus] = useState(null);

    const startDebate = async () => {
        setIsRunning(true);
        setTranscript([]);
        setConsensus(null);

        try {
            // Simulate "typing" delay for effect
            const response = await api.runDebate({
                finding: "Detected Cluster shows signs of coordinated amplification.",
                confidence: 0.85,
                context: "Signal ID: 892-A shows high temporal clustering. Sentiment is uniformly negative (-0.9).",
                max_turns: 2
            });

            // Replay the transcript with delays
            let turns = response.transcript;
            for (let i = 0; i < turns.length; i++) {
                await new Promise(r => setTimeout(r, 1500)); // 1.5s delay per turn
                setTranscript(prev => [...prev, turns[i]]);
            }

            setConsensus(response.final_consensus);

        } catch (e) {
            console.error("Debate failed", e);
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <Card className="h-[500px] flex flex-col bg-card/50 backdrop-blur">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Gavel className="h-4 w-4 text-purple-500" />
                            Adversarial Debate Protocol
                        </CardTitle>
                        <CardDescription>Multi-Agent hallucination check</CardDescription>
                    </div>
                    <Button size="sm" onClick={startDebate} disabled={isRunning} variant="outline">
                        {isRunning ? <span className="animate-pulse">Debating...</span> : <><PlayCircle className="mr-2 h-4 w-4" /> Challenge Finding</>}
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 p-4">
                <ScrollArea className="h-full pr-4">
                    <div className="space-y-4">
                        {transcript.length === 0 && !isRunning && (
                            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground opacity-50">
                                <Shield className="h-12 w-12 mb-2" />
                                <p>No debate active. Challenge a finding to start.</p>
                            </div>
                        )}

                        {transcript.map((turn, i) => (
                            <div key={i} className={`flex gap-3 ${turn.speaker === 'Critic' ? 'flex-row-reverse' : ''}`}>
                                <Avatar className={`h-8 w-8 border ${turn.speaker === 'Critic' ? 'border-red-500 bg-red-500/10' :
                                        turn.speaker === 'Judge' ? 'border-purple-500 bg-purple-500/10' :
                                            'border-blue-500 bg-blue-500/10'
                                    }`}>
                                    <AvatarFallback className="text-[10px]">
                                        {turn.speaker[0]}
                                    </AvatarFallback>
                                </Avatar>
                                <div className={`flex flex-col max-w-[80%] ${turn.speaker === 'Critic' ? 'items-end' : ''}`}>
                                    <span className="text-[10px] text-muted-foreground mb-1">
                                        {turn.speaker} • Conf: {turn.confidence.toFixed(2)}
                                    </span>
                                    <div className={`p-3 rounded-lg text-sm ${turn.speaker === 'Critic' ? 'bg-red-950/30 border border-red-500/20 rounded-tr-none' :
                                            turn.speaker === 'Judge' ? 'bg-purple-950/30 border border-purple-500/20' :
                                                'bg-blue-950/30 border border-blue-500/20 rounded-tl-none'
                                        }`}>
                                        {turn.content}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </CardContent>
            {consensus && (
                <CardFooter className="bg-purple-900/10 border-t border-purple-500/20 p-4">
                    <div className="w-full">
                        <p className="text-xs font-semibold text-purple-400 mb-1">FINAL CONSENSUS</p>
                        <p className="text-sm">{consensus}</p>
                    </div>
                </CardFooter>
            )}
        </Card>
    );
}
