import React, { useEffect, useRef, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Twitter, MessageSquare, Newspaper, Radio, TrendingUp, Loader2, ShieldCheck } from "lucide-react";
import { useSimulation } from '@/context/SimulationContext';

/**
 * Live Signal Feed - ALWAYS LIVE with 3 behavior modes:
 * 
 * 1. PRE-SIMULATION: Calm baseline - only positive/neutral/low-virality signals
 * 2. DURING SIMULATION: Crisis escalation - scenario-specific high-risk signals
 * 3. POST-INTERVENTION: Recovery mode - slow feed with positive/recovery posts
 */

// Positive/recovery posts to show after intervention
const RECOVERY_POSTS = [
    { content_text: "Finally got through to support! They resolved my issue quickly. Thanks @MashreqBank 👍", platform_source: "X_Style", gt_sentiment: 0.75, gt_virality_potential: 12, gt_category: "Positive_Neutral", language: "en" },
    { content_text: "App is back up and running smoothly now. Appreciate the quick fix! 🙌", platform_source: "X_Style", gt_sentiment: 0.8, gt_virality_potential: 15, gt_category: "Positive_Neutral", language: "en" },
    { content_text: "Good to see the bank responding to customer concerns. That's how you build trust.", platform_source: "LinkedIn_Style", gt_sentiment: 0.65, gt_virality_potential: 18, gt_category: "Positive_Neutral", language: "en" },
    { content_text: "شكراً للبنك على التحديث السريع! الخدمة رجعت طبيعية الحين 🙏", platform_source: "X_Style", gt_sentiment: 0.7, gt_virality_potential: 10, gt_category: "Positive_Neutral", language: "ar" },
    { content_text: "The official statement from the bank was reassuring. Glad they addressed it quickly.", platform_source: "X_Style", gt_sentiment: 0.6, gt_virality_potential: 20, gt_category: "Positive_Neutral", language: "en" },
    { content_text: "Credit to their crisis management team - professional and transparent response.", platform_source: "LinkedIn_Style", gt_sentiment: 0.85, gt_virality_potential: 8, gt_category: "Positive_Neutral", language: "en" },
    { content_text: "الوضع تحسن كثير! البنك تعامل مع المشكلة بسرعة واحترافية 💪", platform_source: "X_Style", gt_sentiment: 0.75, gt_virality_potential: 14, gt_category: "Positive_Neutral", language: "ar" },
    { content_text: "Situation seems to be stabilizing. Good crisis communication from the bank.", platform_source: "Reddit_Style", gt_sentiment: 0.55, gt_virality_potential: 22, gt_category: "Positive_Neutral", language: "en" },
];

export function SignalFeed() {
    const {
        activeScenarioName,
        simulationStatus,
        simulationSpeed,
        metrics,
        liveSignals,
        currentSignal,
        injectSignal,
        strategyDeployed  // Check if intervention was applied
    } = useSimulation();

    const [datasetSignals, setDatasetSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isStreaming, setIsStreaming] = useState(false);
    const [feedMode, setFeedMode] = useState('baseline'); // baseline, crisis, recovery
    const injectionIntervalRef = useRef(null);
    const signalIndexRef = useRef(0);
    const recoveryIndexRef = useRef(0);

    // Load signals from dataset on mount
    useEffect(() => {
        fetch('/signals.json')
            .then(res => res.json())
            .then(data => {
                setDatasetSignals(data);
                setLoading(false);
                console.log(`Loaded ${data.length} signals from dataset`);
            })
            .catch(err => {
                console.error('Failed to load signals:', err);
                setLoading(false);
            });
    }, []);

    // Determine feed mode based on simulation state
    useEffect(() => {
        if (strategyDeployed) {
            setFeedMode('recovery');
        } else if (simulationStatus === 'running') {
            setFeedMode('crisis');
        } else {
            setFeedMode('baseline');
        }
    }, [simulationStatus, strategyDeployed]);

    // Get signals based on current mode
    const getFilteredSignals = () => {
        if (feedMode === 'recovery') {
            // Mix of positive signals from dataset + recovery posts
            const positiveFromDataset = datasetSignals.filter(s =>
                s.gt_sentiment > 0.2 || s.gt_category?.includes('Positive') || s.gt_category?.includes('Irrelevant')
            );
            return positiveFromDataset.length > 0 ? positiveFromDataset : RECOVERY_POSTS;
        }

        if (feedMode === 'baseline') {
            // Only low-risk signals: positive, neutral, or low virality (< 35)
            return datasetSignals.filter(s =>
                s.gt_sentiment > -0.2 ||
                s.gt_virality_potential < 35 ||
                s.gt_category?.includes('Positive') ||
                s.gt_category?.includes('Irrelevant')
            );
        }

        // Crisis mode - filter by scenario category
        const name = (activeScenarioName || '').toLowerCase();
        if (name.includes('leak') || name.includes('breach') || name.includes('data') || name.includes('fraud')) {
            return datasetSignals.filter(s => s.gt_category?.includes('Fraud'));
        } else if (name.includes('outage') || name.includes('down') || name.includes('atm') || name.includes('service')) {
            return datasetSignals.filter(s => s.gt_category?.includes('Outage'));
        }
        return datasetSignals;
    };

    // Calculate injection interval based on mode and velocity
    // Divide by simulationSpeed so 4x = 4x faster signals
    const getInjectionInterval = () => {
        const velocity = metrics?.velocity || 15;
        // Force 1x speed when simulation is IDLE to prevent fast signals persisting after stop
        const speed = (simulationStatus === 'idle') ? 1 : (simulationSpeed || 1);

        let baseInterval;
        if (feedMode === 'recovery') {
            // Recovery mode: very slow (6-10 seconds)
            baseInterval = 6000 + Math.random() * 4000;
        } else if (feedMode === 'baseline') {
            // Baseline: slow and calm (5-7 seconds)
            baseInterval = 5000 + Math.random() * 2000;
        } else if (velocity >= 65) {
            // Crisis mode: speed based on velocity
            baseInterval = 1000 + Math.random() * 500;
        } else if (velocity >= 30) {
            baseInterval = 2000 + Math.random() * 1000;
        } else {
            baseInterval = 3000 + Math.random() * 1500;
        }

        // Divide by speed so 4x simulation = 4x faster signals
        return Math.max(300, baseInterval / speed);
    };

    // Stream signals continuously with mode-aware behavior
    // Re-run when simulationSpeed changes to apply new speed immediately
    useEffect(() => {
        if (simulationStatus === 'complete') {
            setIsStreaming(false);
            if (injectionIntervalRef.current) {
                clearTimeout(injectionIntervalRef.current);
            }
            return;
        }

        if (datasetSignals.length > 0 && !loading) {
            setIsStreaming(true);

            const injectNextSignal = () => {
                // Skip injection when paused or complete
                if (simulationStatus === 'paused' || simulationStatus === 'complete') {
                    // Schedule retry after a short delay
                    injectionIntervalRef.current = setTimeout(injectNextSignal, 500);
                    return;
                }

                let signal;

                if (feedMode === 'recovery' && Math.random() > 0.4) {
                    // In recovery mode, 60% chance to show recovery posts
                    signal = RECOVERY_POSTS[recoveryIndexRef.current % RECOVERY_POSTS.length];
                    recoveryIndexRef.current++;
                } else {
                    const filtered = getFilteredSignals();
                    if (filtered.length === 0) {
                        // Fallback to recovery posts
                        signal = RECOVERY_POSTS[0];
                    } else {
                        signal = filtered[signalIndexRef.current % filtered.length];
                        signalIndexRef.current++;
                    }
                }

                // Inject the signal
                injectSignal({
                    content_text: signal.content_text,
                    platform_source: signal.platform_source,
                    gt_sentiment: signal.gt_sentiment,
                    gt_virality_potential: signal.gt_virality_potential,
                    language: signal.language,
                    gt_category: signal.gt_category,
                });

                // Schedule next injection with current speed
                const nextInterval = getInjectionInterval();
                injectionIntervalRef.current = setTimeout(injectNextSignal, nextInterval);
            };

            // Clear existing interval and start new one
            if (injectionIntervalRef.current) {
                clearTimeout(injectionIntervalRef.current);
            }
            // Start first signal quickly
            injectionIntervalRef.current = setTimeout(injectNextSignal, 500);

            return () => {
                if (injectionIntervalRef.current) {
                    clearTimeout(injectionIntervalRef.current);
                }
            };
        }
    }, [datasetSignals.length, loading, activeScenarioName, feedMode, simulationSpeed, simulationStatus]);

    // Reset signal index when scenario changes
    useEffect(() => {
        signalIndexRef.current = 0;
        recoveryIndexRef.current = 0;
    }, [activeScenarioName]);

    const getPlatformIcon = (platform) => {
        const p = (platform || '').toLowerCase().replace('_style', '');
        switch (p) {
            case 'x': case 'twitter': case 'x_style': return <Twitter className="h-4 w-4 text-blue-400" />;
            case 'reddit': case 'reddit_style': return <MessageSquare className="h-4 w-4 text-orange-500" />;
            case 'news': case 'news_portal': return <Newspaper className="h-4 w-4 text-slate-400" />;
            case 'linkedin': case 'linkedin_style': return <MessageSquare className="h-4 w-4 text-blue-600" />;
            default: return <MessageSquare className="h-4 w-4 text-muted-foreground" />;
        }
    };

    const getSentimentColor = (sentiment) => {
        if (sentiment > 0.3) return 'text-green-400';
        if (sentiment > -0.3) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getViralityBadge = (virality) => {
        if (virality > 70) return { text: 'HIGH RISK', class: 'bg-red-500/20 text-red-400 border-red-500/30' };
        if (virality > 40) return { text: 'MEDIUM', class: 'bg-amber-500/20 text-amber-400 border-amber-500/30' };
        return { text: 'LOW', class: 'bg-green-500/20 text-green-400 border-green-500/30' };
    };

    const getModeBadge = () => {
        switch (feedMode) {
            case 'recovery': return { text: 'RECOVERING', class: 'border-green-500/50 text-green-400', icon: <ShieldCheck className="h-3 w-3 mr-1" /> };
            case 'crisis': return { text: 'CRISIS MODE', class: 'border-red-500/50 text-red-400' };
            default: return { text: 'BASELINE', class: 'border-blue-500/50 text-blue-400' };
        }
    };

    const getCategoryBadge = (category) => {
        if (category?.includes('Fraud')) return { text: 'FRAUD', class: 'bg-red-500/20 text-red-400' };
        if (category?.includes('Outage')) return { text: 'OUTAGE', class: 'bg-amber-500/20 text-amber-400' };
        if (category?.includes('Positive')) return { text: 'POSITIVE', class: 'bg-green-500/20 text-green-400' };
        return { text: 'GENERAL', class: 'bg-muted text-muted-foreground' };
    };

    const modeBadge = getModeBadge();

    return (
        <Card className="h-full flex flex-col bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Radio className={`h-4 w-4 ${isStreaming ? 'text-red-500 animate-pulse' : 'text-muted-foreground'}`} />
                        Live Signal Feed
                    </CardTitle>
                    <div className="flex gap-2 items-center">
                        {isStreaming && (
                            <>
                                <span className="text-[10px] text-red-400 font-semibold animate-pulse">● LIVE</span>
                                <Badge variant="outline" className={`text-[9px] font-mono flex items-center ${modeBadge.class}`}>
                                    {modeBadge.icon}{modeBadge.text}
                                </Badge>
                            </>
                        )}
                        {metrics?.signalCount > 0 && (
                            <Badge variant="outline" className="text-[9px] font-mono">
                                {metrics.signalCount} signals
                            </Badge>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 p-0">
                <ScrollArea className="h-full px-4">
                    <div className="space-y-3 pb-4">
                        {loading && (
                            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                                <Loader2 className="h-8 w-8 mb-2 animate-spin text-purple-500" />
                                <p className="text-sm">Loading signal dataset...</p>
                            </div>
                        )}

                        {!loading && liveSignals.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                                <Radio className="h-8 w-8 mb-2 animate-pulse text-amber-500" />
                                <p className="text-sm">Initializing live stream...</p>
                                <p className="text-xs mt-1">{datasetSignals.length} signals ready</p>
                            </div>
                        )}

                        {liveSignals.map((signal, i) => {
                            const virality = getViralityBadge(signal.gt_virality_potential || 0);
                            const category = getCategoryBadge(signal.gt_category);
                            const isNew = currentSignal?.id === signal.id;
                            const isPositive = signal.gt_sentiment > 0.3;

                            return (
                                <div
                                    key={signal.id}
                                    className={`p-3 rounded-lg border transition-all duration-500 ${isNew
                                        ? isPositive
                                            ? 'ring-2 ring-green-500 bg-green-500/10 border-green-500/50'
                                            : 'ring-2 ring-amber-500 bg-amber-500/10 border-amber-500/50'
                                        : 'border-border/50 bg-background/50'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            {getPlatformIcon(signal.platform_source)}
                                            <span className="font-semibold text-xs text-muted-foreground capitalize">
                                                {(signal.platform_source || 'social').replace('_Style', '').replace('_', ' ')}
                                            </span>
                                            <Badge variant="outline" className={`text-[8px] px-1 py-0 ${category.class}`}>
                                                {category.text}
                                            </Badge>
                                            {signal.language && signal.language !== 'en' && (
                                                <Badge variant="outline" className="text-[8px] px-1 py-0 border-purple-500/50 text-purple-400">
                                                    {signal.language.toUpperCase()}
                                                </Badge>
                                            )}
                                            {isNew && (
                                                <Badge className={`text-[8px] px-1 py-0 animate-pulse ${isPositive ? 'bg-green-500 text-black' : 'bg-amber-500 text-black'}`}>
                                                    NEW
                                                </Badge>
                                            )}
                                        </div>
                                        <Badge variant="outline" className={`text-[9px] ${virality.class}`}>
                                            {virality.text}
                                        </Badge>
                                    </div>
                                    <p className="mb-2 leading-relaxed text-sm text-foreground/90 line-clamp-3" dir={signal.language === 'ar' ? 'rtl' : 'ltr'}>
                                        {signal.content_text}
                                    </p>
                                    <div className="flex items-center justify-between border-t border-border/30 pt-2">
                                        <div className="flex gap-4 text-[10px] text-muted-foreground">
                                            <span>Virality: <span className="font-mono font-bold">{Math.round(signal.gt_virality_potential || 0)}</span></span>
                                            <span>Sentiment: <span className={`font-mono ${getSentimentColor(signal.gt_sentiment || 0)}`}>
                                                {((signal.gt_sentiment || 0) * 100).toFixed(0)}%
                                            </span></span>
                                        </div>
                                        <span className="text-[9px] text-muted-foreground">
                                            {new Date(signal.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
