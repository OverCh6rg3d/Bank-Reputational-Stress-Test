import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Activity, Search, AlertOctagon } from "lucide-react";
import { useSimulation } from '../../context/SimulationContext';

// Simple Badge component if not present in UI lib yet, but assuming standard shadcn structure
const SimpleBadge = ({ children, variant = 'default' }) => {
    const colors = {
        default: 'bg-primary text-primary-foreground',
        destructive: 'bg-destructive/10 text-destructive border-destructive/20',
        outline: 'text-foreground border-border',
        secondary: 'bg-secondary text-secondary-foreground'
    };
    return (
        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${colors[variant] || colors.default}`}>
            {children}
        </span>
    );
};

export default function AIInterpretation() {
    const { metrics, activeScenario } = useSimulation();

    return (
        <Card className="bg-card/50 backdrop-blur h-full border-l-4 border-l-purple-500">
            <CardHeader className="pb-2">
                <div className="flex justify-between">
                    <CardTitle className="text-sm font-medium">Explainable AI Insight</CardTitle>
                    <Activity className="h-4 w-4 text-purple-500" />
                </div>
                <CardDescription>Signal Interpretation Engine (Module B)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">Primary Classification</div>
                    <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-foreground">Reputational Risk / Integrity</span>
                        <SimpleBadge variant="destructive">High Confidence</SimpleBadge>
                    </div>
                </div>

                <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-2">Detected Clusters & Keywords</div>
                    <div className="flex flex-wrap gap-1">
                        {activeScenario.includes("Data Leak") ? (
                            <>
                                <SimpleBadge variant="secondary">#DataBreach</SimpleBadge>
                                <SimpleBadge variant="secondary">vendor_security</SimpleBadge>
                                <SimpleBadge variant="secondary">API_exposed</SimpleBadge>
                                <SimpleBadge variant="destructive"> panic_selling </SimpleBadge>
                            </>
                        ) : activeScenario.includes("Outage") ? (
                            <>
                                <SimpleBadge variant="secondary">#AppDown</SimpleBadge>
                                <SimpleBadge variant="secondary">503_Error</SimpleBadge>
                                <SimpleBadge variant="destructive"> login_failed </SimpleBadge>
                            </>
                        ) : (
                            <>
                                <SimpleBadge variant="secondary">#Deepfake</SimpleBadge>
                                <SimpleBadge variant="secondary">CEO_video</SimpleBadge>
                                <SimpleBadge variant="destructive"> stock_manipulation </SimpleBadge>
                            </>
                        )}
                    </div>
                </div>

                <div className="p-3 bg-muted/30 rounded-md border border-border/50">
                    <div className="flex items-start gap-2">
                        <Search className="h-4 w-4 text-purple-400 mt-0.5" />
                        <div>
                            <p className="text-xs font-medium text-foreground">Reasoning Trace:</p>
                            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                                The system detected a <strong>450% spike</strong> in semantic clusters relating to "unauthorized access" originating from high-authority accounts.
                                Cross-referencing with <span className="text-purple-400 font-mono">Bank_Knowledge_Base</span> confirmed no scheduled maintenance, elevating probability of authentic incident.
                            </p>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
