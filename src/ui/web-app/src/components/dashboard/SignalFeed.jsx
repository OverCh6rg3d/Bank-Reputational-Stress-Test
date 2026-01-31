import React, { useEffect, useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Twitter, MessageSquare, Newspaper, AlertOctagon, Radio } from "lucide-react";
import { useSimulation } from '@/context/SimulationContext';

/**
 * Live Signal Feed with Velocity-Based Signal Selection
 * 
 * Displays signals organized by velocity level:
 * - Low (< 30): Confusion phase - questions, mild concern, some defenders  
 * - Medium (30-65): Frustration phase - validated complaints
 * - High (> 65): Outrage phase - anger, calls to action
 */

// Comprehensive signal templates organized by scenario AND velocity level
const SCENARIO_SIGNALS = {
    "Data Leak": {
        low: [
            { content_text: "Is anyone else having trouble logging into Mashreq today? Getting weird errors 🤔", platform_source: "x_style", gt_sentiment: -0.3, gt_virality_potential: 22, author_type: "customer" },
            { content_text: "My Mashreq app is asking me to reverify my account - is this normal or should I be worried?", platform_source: "x_style", gt_sentiment: -0.25, gt_virality_potential: 28, author_type: "customer" },
            { content_text: "Heard something about Mashreq security issues? Anyone know what's going on?", platform_source: "x_style", gt_sentiment: -0.35, gt_virality_potential: 30, author_type: "customer" },
            { content_text: "Works fine for me. Try clearing your cache?", platform_source: "x_style", gt_sentiment: 0.1, gt_virality_potential: 12, author_type: "customer" },
            { content_text: "r/dubai - Anyone experiencing issues with Mashreq online banking today?", platform_source: "reddit_style", gt_sentiment: -0.2, gt_virality_potential: 25, author_type: "customer" },
            { content_text: "Just got a weird SMS about my Mashreq account. Might be phishing, might be legit? 🤷‍♂️", platform_source: "x_style", gt_sentiment: -0.4, gt_virality_potential: 35, author_type: "customer" },
        ],
        medium: [
            { content_text: "Ok this is definitely a real issue. Third person I know affected by the Mashreq situation. @MashreqBank what's going on?", platform_source: "x_style", gt_sentiment: -0.55, gt_virality_potential: 52, author_type: "customer" },
            { content_text: "Multiple reports of Mashreq accounts being compromised. Changed my password and enabled 2FA just in case.", platform_source: "x_style", gt_sentiment: -0.5, gt_virality_potential: 48, author_type: "customer" },
            { content_text: "This is the second time Mashreq has had security issues this year. Starting to lose trust.", platform_source: "x_style", gt_sentiment: -0.65, gt_virality_potential: 55, author_type: "customer" },
            { content_text: "r/dubai - Megathread: Mashreq Bank Security Concerns - Share your experience", platform_source: "reddit_style", gt_sentiment: -0.5, gt_virality_potential: 60, author_type: "customer" },
            { content_text: "Been on hold with Mashreq support for 45 minutes now. The wait time alone tells you something is very wrong.", platform_source: "x_style", gt_sentiment: -0.7, gt_virality_potential: 58, author_type: "customer" },
            { content_text: "Cybersecurity analyst here: If the reports are true, Mashreq customers should freeze their cards immediately.", platform_source: "x_style", gt_sentiment: -0.6, gt_virality_potential: 70, author_type: "influencer" },
        ],
        high: [
            { content_text: "UNACCEPTABLE @MashreqBank! My personal data may be exposed and you've said NOTHING for 6 hours?? #MashreqFail #DataBreach", platform_source: "x_style", gt_sentiment: -0.9, gt_virality_potential: 82, author_type: "customer" },
            { content_text: "Everyone affected by the Mashreq breach should report to @CBUAE immediately. This is a regulatory matter now! #BankingCrisis", platform_source: "x_style", gt_sentiment: -0.85, gt_virality_potential: 88, author_type: "influencer" },
            { content_text: "BREAKING: Major UAE bank faces potential data breach affecting thousands of customers. Official response pending.", platform_source: "news_portal", gt_sentiment: -0.7, gt_virality_potential: 92, author_type: "journalist" },
            { content_text: "Time to move my money. If Mashreq can't protect basic customer data, they don't deserve my business. #SwitchBanks", platform_source: "x_style", gt_sentiment: -0.95, gt_virality_potential: 78, author_type: "customer" },
            { content_text: "Class action lawsuit against Mashreq? DM me if you're affected and want to join. We need accountability! 💪", platform_source: "x_style", gt_sentiment: -0.88, gt_virality_potential: 85, author_type: "influencer" },
            { content_text: "My elderly mother is panicking about her savings at Mashreq. This is what happens when banks cut corners on security. SHAMEFUL.", platform_source: "x_style", gt_sentiment: -0.92, gt_virality_potential: 80, author_type: "customer" },
        ],
    },
    "Outage": {
        low: [
            { content_text: "Mashreq app not loading for me. Anyone else? 🤔", platform_source: "x_style", gt_sentiment: -0.2, gt_virality_potential: 20, author_type: "customer" },
            { content_text: "Can't check my balance on Mashreq. Is it maintenance or something?", platform_source: "x_style", gt_sentiment: -0.25, gt_virality_potential: 22, author_type: "customer" },
            { content_text: "Works fine on my end. Try restarting your phone?", platform_source: "x_style", gt_sentiment: 0.1, gt_virality_potential: 10, author_type: "customer" },
            { content_text: "Getting 'server error' on Mashreq app. Probably just a glitch, will try later.", platform_source: "x_style", gt_sentiment: -0.15, gt_virality_potential: 18, author_type: "customer" },
            { content_text: "r/dubai - PSA: Mashreq online banking seems slow today. Anyone else?", platform_source: "reddit_style", gt_sentiment: -0.2, gt_virality_potential: 25, author_type: "customer" },
        ],
        medium: [
            { content_text: "Mashreq down for 2 hours now. This is getting ridiculous. I have bills to pay!", platform_source: "x_style", gt_sentiment: -0.6, gt_virality_potential: 55, author_type: "customer" },
            { content_text: "Had an important rent payment to make and Mashreq is completely down. Thanks a lot @MashreqBank 😤", platform_source: "x_style", gt_sentiment: -0.7, gt_virality_potential: 58, author_type: "customer" },
            { content_text: "Third outage this month. Mashreq seriously needs to invest in their infrastructure.", platform_source: "x_style", gt_sentiment: -0.65, gt_virality_potential: 52, author_type: "customer" },
            { content_text: "Even the ATMs aren't working. This is a complete system failure. #MashreqDown", platform_source: "x_style", gt_sentiment: -0.7, gt_virality_potential: 62, author_type: "customer" },
            { content_text: "r/dubai - Mashreq Bank outage thread. Post updates here. Apparently ATMs down across Dubai.", platform_source: "reddit_style", gt_sentiment: -0.55, gt_virality_potential: 65, author_type: "customer" },
        ],
        high: [
            { content_text: "8 HOURS without access to MY MONEY! @MashreqBank this should be illegal! What if I had an emergency?? #MashreqDown #BankingFail", platform_source: "x_style", gt_sentiment: -0.92, gt_virality_potential: 85, author_type: "customer" },
            { content_text: "Filing formal complaint with @CBUAE. This level of service failure is unacceptable for a major bank. #Accountability", platform_source: "x_style", gt_sentiment: -0.88, gt_virality_potential: 82, author_type: "influencer" },
            { content_text: "BREAKING: Mashreq Bank reports major system failure affecting thousands across UAE. Services restoration time unknown.", platform_source: "news_portal", gt_sentiment: -0.65, gt_virality_potential: 90, author_type: "journalist" },
            { content_text: "My business lost AED 50,000 today because I couldn't process payments. Mashreq will be hearing from my lawyer.", platform_source: "x_style", gt_sentiment: -0.95, gt_virality_potential: 78, author_type: "customer" },
            { content_text: "Moving ALL my accounts to Emirates NBD first thing tomorrow. Mashreq is a joke. #SwitchBanks #NeverAgain", platform_source: "x_style", gt_sentiment: -0.9, gt_virality_potential: 75, author_type: "customer" },
        ],
    },
    "Deepfake": {
        low: [
            { content_text: "Did anyone see that Mashreq CEO video going around? Looks kinda sus to me 🤔", platform_source: "x_style", gt_sentiment: -0.3, gt_virality_potential: 35, author_type: "customer" },
            { content_text: "What's this video about Mashreq circulating on WhatsApp groups?", platform_source: "x_style", gt_sentiment: -0.2, gt_virality_potential: 30, author_type: "customer" },
            { content_text: "Could be deepfake but idk, the video looks pretty real. What do you guys think?", platform_source: "x_style", gt_sentiment: -0.35, gt_virality_potential: 40, author_type: "customer" },
            { content_text: "r/dubai - Viral video allegedly showing Mashreq executive. Real or fake?", platform_source: "reddit_style", gt_sentiment: -0.25, gt_virality_potential: 45, author_type: "customer" },
            { content_text: "I'm skeptical about that Mashreq video. The lip sync looks off at some points.", platform_source: "x_style", gt_sentiment: -0.2, gt_virality_potential: 38, author_type: "customer" },
        ],
        medium: [
            { content_text: "Whether that Mashreq video is real or fake, this is a PR disaster. The bank needs to respond NOW.", platform_source: "x_style", gt_sentiment: -0.6, gt_virality_potential: 65, author_type: "influencer" },
            { content_text: "Tech friends analyzing the CEO video say it has classic deepfake markers. But damage might already be done.", platform_source: "x_style", gt_sentiment: -0.55, gt_virality_potential: 62, author_type: "customer" },
            { content_text: "Mashreq stock dropping after that viral video. Company MUST respond ASAP to clarify.", platform_source: "x_style", gt_sentiment: -0.65, gt_virality_potential: 70, author_type: "journalist" },
            { content_text: "Media literacy reminder: Do NOT share unverified videos. Wait for official confirmation.", platform_source: "x_style", gt_sentiment: -0.3, gt_virality_potential: 55, author_type: "influencer" },
            { content_text: "r/dubai - Megathread: Analysis of the Mashreq CEO video - evidence compilation", platform_source: "reddit_style", gt_sentiment: -0.5, gt_virality_potential: 68, author_type: "customer" },
        ],
        high: [
            { content_text: "SHOCKING: Mashreq CEO video going viral! If this is real, it's over for them. If fake, WHO made it and WHY? #MashreqScandal", platform_source: "x_style", gt_sentiment: -0.9, gt_virality_potential: 92, author_type: "influencer" },
            { content_text: "If this is a deepfake attack on Mashreq, why hasn't the bank said ANYTHING? The silence is damning! #Transparency", platform_source: "x_style", gt_sentiment: -0.85, gt_virality_potential: 85, author_type: "customer" },
            { content_text: "BREAKING: Viral video allegedly showing Mashreq Bank executive in compromising situation. Authenticity unconfirmed.", platform_source: "news_portal", gt_sentiment: -0.7, gt_virality_potential: 95, author_type: "journalist" },
            { content_text: "Withdrew all my savings from Mashreq this morning. Not taking any chances until this is resolved. Trust = GONE.", platform_source: "x_style", gt_sentiment: -0.92, gt_virality_potential: 80, author_type: "customer" },
            { content_text: "This deepfake tech is getting scary. If the Mashreq video is fake, how do we trust ANY video now? Terrifying implications.", platform_source: "x_style", gt_sentiment: -0.75, gt_virality_potential: 88, author_type: "influencer" },
        ],
    },
};

// Get scenario key from name
function getScenarioKey(scenarioName) {
    if (!scenarioName) return 'Data Leak';
    const name = scenarioName.toLowerCase();
    if (name.includes('leak') || name.includes('breach') || name.includes('data')) return 'Data Leak';
    if (name.includes('outage') || name.includes('down')) return 'Outage';
    if (name.includes('deepfake') || name.includes('video') || name.includes('executive')) return 'Deepfake';
    return 'Data Leak';
}

// Get velocity level
function getVelocityLevel(velocity) {
    if (velocity >= 65) return 'high';
    if (velocity >= 30) return 'medium';
    return 'low';
}

export function SignalFeed() {
    const { activeScenarioName, simulationStatus, metrics, timeHorizon } = useSimulation();
    const [displayedSignals, setDisplayedSignals] = useState([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const rotationIndexRef = useRef({ low: 0, medium: 0, high: 0 });
    const lastUpdateRef = useRef(0);

    // Update signals based on velocity and time
    useEffect(() => {
        const scenarioKey = getScenarioKey(activeScenarioName);
        const scenarioSignals = SCENARIO_SIGNALS[scenarioKey] || SCENARIO_SIGNALS['Data Leak'];
        const velocity = metrics?.velocity || 15;
        const level = getVelocityLevel(velocity);
        const pool = scenarioSignals[level] || [];

        if (pool.length === 0) return;

        // Rotate signals every ~2 simulation hours
        const currentHour = Math.floor(timeHorizon);
        if (currentHour !== lastUpdateRef.current || displayedSignals.length === 0) {
            lastUpdateRef.current = currentHour;

            // Advance rotation index
            const idx = rotationIndexRef.current;
            const startIdx = idx[level];
            idx[level] = (idx[level] + 1) % pool.length;

            // Get 5 signals with rotation
            const signals = [];
            for (let i = 0; i < Math.min(5, pool.length); i++) {
                const signal = { ...pool[(startIdx + i) % pool.length] };
                // Add unique ID and timestamp
                signal.id = `${scenarioKey}-${level}-${i}-${currentHour}`;
                signal.timestamp = new Date(Date.now() - i * 180000).toISOString();
                // Add slight random variation to make it feel dynamic
                signal.gt_virality_potential = Math.round(signal.gt_virality_potential + (Math.random() - 0.5) * 10);
                signal.gt_sentiment = Math.max(-1, Math.min(0.5, signal.gt_sentiment + (Math.random() - 0.5) * 0.15));
                signals.push(signal);
            }

            // Sort by virality (most viral first)
            signals.sort((a, b) => b.gt_virality_potential - a.gt_virality_potential);

            setDisplayedSignals(signals);

            if (simulationStatus === 'running') {
                setIsStreaming(true);
                setTimeout(() => setIsStreaming(false), 400);
            }
        }
    }, [activeScenarioName, simulationStatus, metrics?.velocity, Math.floor(timeHorizon)]);

    // Reset when scenario changes
    useEffect(() => {
        rotationIndexRef.current = { low: 0, medium: 0, high: 0 };
        lastUpdateRef.current = -1; // Force update
    }, [activeScenarioName]);

    const getPlatformIcon = (platform) => {
        const p = (platform || '').toLowerCase().replace('_style', '');
        switch (p) {
            case 'x': case 'twitter': return <Twitter className="h-4 w-4 text-blue-400" />;
            case 'reddit': return <MessageSquare className="h-4 w-4 text-orange-500" />;
            case 'news': case 'news_portal': return <Newspaper className="h-4 w-4 text-slate-400" />;
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

    const getLevelBadge = () => {
        const velocity = metrics?.velocity || 15;
        const level = getVelocityLevel(velocity);
        const labels = { low: 'CONFUSION', medium: 'FRUSTRATION', high: 'OUTRAGE' };
        const colors = {
            low: 'border-blue-500/50 text-blue-400',
            medium: 'border-amber-500/50 text-amber-400',
            high: 'border-red-500/50 text-red-400'
        };
        return { text: labels[level], class: colors[level] };
    };

    return (
        <Card className="h-[400px] flex flex-col bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-lg flex items-center gap-2">
                        {simulationStatus === 'running' ? (
                            <Radio className={`h-4 w-4 text-red-500 ${isStreaming ? 'animate-ping' : 'animate-pulse'}`} />
                        ) : (
                            <AlertOctagon className="h-4 w-4 text-red-500" />
                        )}
                        Live Signal Feed
                    </CardTitle>
                    <div className="flex gap-2 items-center">
                        {simulationStatus === 'running' && (
                            <>
                                <span className="text-[10px] text-amber-400 animate-pulse">● LIVE</span>
                                <Badge variant="outline" className={`text-[9px] font-mono ${getLevelBadge().class}`}>
                                    {getLevelBadge().text}
                                </Badge>
                            </>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 p-0">
                <ScrollArea className="h-full px-4">
                    <div className="space-y-3 pb-4">
                        {displayedSignals.map((signal, i) => {
                            const virality = getViralityBadge(signal.gt_virality_potential || 0);
                            const hashtags = (signal.content_text.match(/#\w+/g) || []).map(h => h.slice(1));

                            return (
                                <div
                                    key={signal.id}
                                    className={`p-3 rounded-lg border border-border/50 bg-background/50 text-sm transition-all duration-300 ${i === 0 && isStreaming ? 'ring-2 ring-amber-500/50 bg-amber-500/5' : ''
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            {getPlatformIcon(signal.platform_source)}
                                            <span className="font-semibold text-xs text-muted-foreground capitalize">
                                                {(signal.platform_source || 'social').replace('_style', '').replace('_', ' ')}
                                            </span>
                                            {signal.author_type && signal.author_type !== 'customer' && (
                                                <Badge variant="outline" className="text-[8px] px-1 py-0 border-purple-500/50 text-purple-400">
                                                    {signal.author_type}
                                                </Badge>
                                            )}
                                        </div>
                                        <Badge variant="outline" className={`text-[9px] ${virality.class}`}>
                                            {virality.text}
                                        </Badge>
                                    </div>
                                    <p className="mb-2 leading-relaxed text-foreground/90">
                                        {signal.content_text}
                                    </p>
                                    {hashtags.length > 0 && (
                                        <div className="flex gap-2 flex-wrap mb-2">
                                            {hashtags.slice(0, 3).map((tag, idx) => (
                                                <span key={idx} className="text-[10px] text-blue-400">#{tag}</span>
                                            ))}
                                        </div>
                                    )}
                                    <div className="flex items-center justify-between border-t border-border/30 pt-2">
                                        <div className="flex gap-4 text-[10px] text-muted-foreground">
                                            <span>Risk: <span className="font-mono font-bold">{Math.round(signal.gt_virality_potential || 0)}</span></span>
                                            <span>Sentiment: <span className={`font-mono ${getSentimentColor(signal.gt_sentiment || 0)}`}>
                                                {((signal.gt_sentiment || 0) * 100).toFixed(0)}%
                                            </span></span>
                                        </div>
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
