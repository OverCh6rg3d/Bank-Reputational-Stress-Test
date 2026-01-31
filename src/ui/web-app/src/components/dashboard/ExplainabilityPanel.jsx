import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Brain, ArrowRight } from "lucide-react";

export function ExplainabilityPanel() {
    // Mocking the explanation data for demo (since we don't have a specific endpoint for it just yet)
    // In real integration, this would come from api.getExplanation()
    const explanation = {
        summary: "Risk Level: High due to rapid velocity and coordinated signaling.",
        factors: [
            { name: "Velocity Score", value: 85, impact: "High" },
            { name: "Sentiment Check", value: 92, impact: "High" },
            { name: "Bot Probability", value: 65, impact: "Medium" },
            { name: "Source Credibility", value: 20, impact: "Low" }
        ],
        reasoning: "The system detected a 300% spike in mentions of 'hacked' within 15 minutes. 70% of accounts are <30 days old, suggesting a coordinated botnet. Sentiment is universally negative."
    };

    return (
        <Card className="bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="h-4 w-4 text-cyan-500" />
                    AI Reasoning Engine
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-sm font-medium mb-4">{explanation.summary}</p>

                <div className="space-y-4 mb-6">
                    {explanation.factors.map(f => (
                        <div key={f.name} className="space-y-1">
                            <div className="flex justify-between text-xs">
                                <span className="text-muted-foreground">{f.name}</span>
                                <span className={f.impact === 'High' ? 'text-red-400' : 'text-blue-400'}>
                                    {f.value}% impact
                                </span>
                            </div>
                            <Progress value={f.value} className="h-1.5" indicatorClassName={f.impact === 'High' ? 'bg-red-500' : 'bg-blue-500'} />
                        </div>
                    ))}
                </div>

                <div className="bg-muted/50 rounded-lg p-3 border border-border/50">
                    <p className="text-xs font-semibold text-muted-foreground mb-1 flex items-center gap-1">
                        <ArrowRight className="h-3 w-3" /> LOGICAL TRACE
                    </p>
                    <p className="text-xs leading-relaxed opacity-80 font-mono">
                        {explanation.reasoning}
                    </p>
                </div>
            </CardContent>
        </Card>
    );
}
