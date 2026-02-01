import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Loader2, RefreshCw } from "lucide-react";
import { useSimulation } from '@/context/SimulationContext';
import { api } from '@/services/api';

export function ExecutiveBriefingPanel() {
    const { activeScenarioName, activeScenario, metrics, liveSignals } = useSimulation();
    const [briefing, setBriefing] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [lastUpdated, setLastUpdated] = React.useState(null);

    const renderMarkdown = (text) => {
        if (!text) return '';
        const escaped = String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        const bolded = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        return bolded.replace(/\n/g, '<br />');
    };

    const generateBriefing = async () => {
        setLoading(true);
        setError(null);
        try {
            const recentSignals = (liveSignals || []).slice(0, 5).map(s => s.content_text || '').filter(Boolean);
            const data = await api.generateBriefing(activeScenarioName, activeScenario?.id || null, {
                metrics: {
                    velocity: metrics?.velocity ?? null,
                    confidence: metrics?.confidence ?? null,
                    time_to_critical: metrics?.time_to_critical ?? null,
                    total_shares: metrics?.total_shares ?? null,
                    reach_percent: metrics?.exposedPercent ?? null,
                    avg_sentiment: metrics?.avgSentiment ?? null,
                    signal_count: metrics?.signalCount ?? null,
                },
                recent_signals: recentSignals,
            });
            setBriefing(data.briefing || null);
            setLastUpdated(new Date());
        } catch (e) {
            setError('Briefing service unavailable.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="bg-card/50 backdrop-blur h-full">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <FileText className="h-4 w-4 text-emerald-400" />
                            Executive Briefing
                        </CardTitle>
                        <CardDescription>
                            C-suite summary with confidence and recommended actions.
                        </CardDescription>
                    </div>
                    {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />}
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {!briefing && !loading && (
                    <div className="text-sm text-muted-foreground">
                        Generate a briefing for the active scenario.
                    </div>
                )}

                {error && (
                    <div className="text-xs text-destructive">
                        {error}
                    </div>
                )}

                {briefing && (
                    <div className="space-y-3">
                        <div>
                            <p className="text-xs text-muted-foreground">Summary</p>
                            <p
                                className="text-sm leading-relaxed"
                                dangerouslySetInnerHTML={{ __html: renderMarkdown(briefing.summary) }}
                            />
                        </div>
                        <div className="grid gap-2 md:grid-cols-2">
                            <div className="text-xs text-muted-foreground">
                                Risk Level: <span className="text-foreground font-medium">{briefing.metrics?.risk_level || 'N/A'}</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                                Confidence: <span className="text-foreground font-medium">{Math.round((briefing.metrics?.confidence || 0) * 100)}%</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                                Velocity: <span className="text-foreground font-medium">{Math.round(briefing.metrics?.velocity || 0)}</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                                Time to Critical: <span className="text-foreground font-medium">{briefing.metrics?.time_to_critical ?? 'N/A'}</span>
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Recommended Action</p>
                            <p className="text-sm font-medium">{briefing.recommendation?.action || 'N/A'}</p>
                            <p
                                className="text-xs text-muted-foreground mt-1"
                                dangerouslySetInnerHTML={{ __html: renderMarkdown(briefing.recommendation?.reasoning || '') }}
                            />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Uncertainties</p>
                            <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-1">
                                {(briefing.uncertainties?.data_gaps || []).map((gap, idx) => (
                                    <li key={`gap-${idx}`}>{gap}</li>
                                ))}
                            </ul>
                        </div>
                        {activeScenario?.potential_impact && (
                            <div>
                                <p className="text-xs text-muted-foreground">Potential Impact</p>
                                <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-1">
                                    {Object.entries(activeScenario.potential_impact || {}).map(([key, value]) => (
                                        <li key={key}>{key.replace(/_/g, ' ')}: {String(value)}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {activeScenario?.target_segment && (
                            <div>
                                <p className="text-xs text-muted-foreground">Affected Segments</p>
                                <p className="text-xs text-muted-foreground">
                                    {String(activeScenario.target_segment).split(',').map(s => s.trim()).join(', ')}
                                </p>
                            </div>
                        )}
                        {lastUpdated && (
                            <div className="text-[10px] text-muted-foreground">
                                Updated: {lastUpdated.toLocaleTimeString()}
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
            <CardFooter>
                <Button onClick={generateBriefing} disabled={loading} variant="outline" className="w-full gap-2">
                    {loading ? (
                        <>
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Generating...
                        </>
                    ) : (
                        <>
                            <RefreshCw className="h-3 w-3" />
                            Generate Briefing
                        </>
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
}
