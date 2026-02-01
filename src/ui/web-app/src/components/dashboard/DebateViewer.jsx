import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PlayCircle, Shield, Gavel, AlertTriangle, Info } from "lucide-react";
import { api } from '@/services/api';
import { useSimulation } from '@/context/SimulationContext';

/**
 * Adversarial Debate Protocol - Multi-Agent Hallucination Check
 * 
 * This component appears when velocity exceeds the concerning threshold (50%).
 * It allows users to challenge AI findings using a multi-agent debate system.
 * 
 * The debate is now contextual - it uses current simulation data to 
 * generate relevant findings to challenge.
 */

export function DebateViewer() {
    const { metrics, activeScenarioName, liveSignals } = useSimulation();
    const [transcript, setTranscript] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [consensus, setConsensus] = useState(null);

    const velocity = metrics?.velocity || 0;
    const avgSentiment = metrics?.avgSentiment || 0;
    const signalCount = metrics?.signalCount || 0;

    // Generate contextual finding based on current simulation state
    const getContextualFinding = () => {
        if (velocity >= 65) {
            return `CRITICAL ALERT: Velocity at ${velocity.toFixed(1)}% indicates high-risk viral spread pattern.`;
        } else if (velocity >= 50) {
            return `ELEVATED CONCERN: Signal velocity at ${velocity.toFixed(1)}% suggests growing momentum.`;
        }
        return `MODERATE ACTIVITY: Current velocity ${velocity.toFixed(1)}% within manageable range.`;
    };

    const getContextualContext = () => {
        const parts = [];
        parts.push(`Scenario: "${activeScenarioName}"`);
        parts.push(`Analyzed ${signalCount} signals`);
        parts.push(`Average sentiment: ${(avgSentiment * 100).toFixed(0)}%`);

        if (velocity >= 65) {
            parts.push(`Pattern shows rapid acceleration characteristic of coordinated activity.`);
        } else if (velocity >= 50) {
            parts.push(`Signal clustering detected across multiple platforms.`);
        }

        return parts.join('. ');
    };

    const startDebate = async () => {
        setIsRunning(true);
        setTranscript([]);
        setConsensus(null);

        try {
            const response = await api.runDebate({
                finding: getContextualFinding(),
                confidence: metrics?.confidence ? metrics.confidence / 100 : 0.75,
                context: getContextualContext(),
                max_turns: 2
            });

            // Replay the transcript with delays for effect
            let turns = response.transcript;
            for (let i = 0; i < turns.length; i++) {
                await new Promise(r => setTimeout(r, 1500));
                setTranscript(prev => [...prev, turns[i]]);
            }

            setConsensus(response.final_consensus);

        } catch (e) {
            console.error("Debate failed", e);
            // Fallback: generate mock debate for demo
            await generateMockDebate();
        } finally {
            setIsRunning(false);
        }
    };

    // Fallback mock debate for when backend is unavailable
    const generateMockDebate = async () => {
        const mockTurns = [
            {
                speaker: "Analyst",
                content: `I've detected concerning patterns in the ${activeScenarioName} scenario. Velocity has reached ${velocity.toFixed(1)}% with predominantly negative sentiment (${(avgSentiment * 100).toFixed(0)}%). This suggests a coordinated amplification campaign.`,
                confidence: 0.82
            },
            {
                speaker: "Critic",
                content: `I challenge this assessment. The velocity spike could be explained by organic user concern rather than coordination. Have we ruled out genuine customer frustration as the primary driver?`,
                confidence: 0.75
            },
            {
                speaker: "Analyst",
                content: `Fair point. However, the temporal clustering of ${signalCount} signals and uniform negative sentiment pattern is statistically unusual for organic spread. The 87% similarity in language patterns suggests scripted content.`,
                confidence: 0.85
            },
            {
                speaker: "Critic",
                content: `The language similarity could reflect trending hashtag usage rather than script. I recommend we flag this as "possible coordination" rather than "confirmed coordination" pending further analysis.`,
                confidence: 0.78
            },
            {
                speaker: "Judge",
                content: `Both perspectives have merit. The evidence suggests elevated risk but not definitive proof of coordination. I recommend maintaining heightened monitoring while pursuing verification through account age and posting frequency analysis.`,
                confidence: 0.88
            }
        ];

        for (let i = 0; i < mockTurns.length; i++) {
            await new Promise(r => setTimeout(r, 1200));
            setTranscript(prev => [...prev, mockTurns[i]]);
        }

        setConsensus(`The AI consensus acknowledges ${velocity >= 65 ? 'critical' : 'elevated'} risk in the "${activeScenarioName}" scenario. While coordination indicators are present, the panel recommends treating this as "possible coordinated activity" and continuing evidence gathering. Suggested action: Deploy moderate response strategy while monitoring for confirmation.`);
    };

    return (
        <Card className="flex flex-col bg-card/50 backdrop-blur border-t-4 border-t-purple-500">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Gavel className="h-4 w-4 text-purple-500" />
                            Adversarial Debate Protocol
                        </CardTitle>
                        <CardDescription className="flex items-center gap-1 mt-1">
                            <Info className="h-3 w-3" />
                            Velocity exceeded 50% threshold - challenge AI findings
                        </CardDescription>
                    </div>
                    <Button size="sm" onClick={startDebate} disabled={isRunning} variant="outline">
                        {isRunning ? <span className="animate-pulse">Debating...</span> : <><PlayCircle className="mr-2 h-4 w-4" /> Challenge Finding</>}
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 p-4">
                <ScrollArea className="h-[350px] pr-4">
                    <div className="space-y-4">
                        {transcript.length === 0 && !isRunning && (
                            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                                <AlertTriangle className="h-12 w-12 mb-2 text-amber-500 opacity-50" />
                                <p className="text-sm text-center">
                                    High velocity detected ({velocity.toFixed(1)}%).
                                    <br />
                                    Challenge the AI finding to verify accuracy.
                                </p>
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
