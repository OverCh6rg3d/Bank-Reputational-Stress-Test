import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Loader2, RefreshCw } from "lucide-react";
import { api } from '@/services/api';

const FALLBACK_GUARDRAILS = {
    action_boundaries: [
        { id: 'no_public_action', description: 'System never posts to public social media' },
        { id: 'human_approval_required', description: 'All response strategies require human approval' },
        { id: 'no_customer_data', description: 'System never processes real customer PII' }
    ],
    non_action_boundaries: [
        { id: 'streisand_risk', description: 'Do not publicly acknowledge rumors with low reach' },
        { id: 'competitor_noise', description: 'Do not respond to low-severity competitor noise' },
        { id: 'bot_activity', description: 'Do not engage suspected bot networks' }
    ],
    confidence_thresholds: [
        { id: 'low_confidence_escalation', description: 'Predictions below 70% confidence require human review', threshold: 0.7 },
        { id: 'critical_severity_escalation', description: 'Critical severity always requires immediate escalation', severity: 'Critical' }
    ],
    socratic_questions: [
        'What is the worst-case scenario if this prediction is wrong?',
        'What evidence would falsify this conclusion?',
        'Which demographic segments might be disproportionately affected?',
        'What are the regulatory implications of this response?',
        'Is there potential for Streisand effect if we act on this?'
    ]
};

export function GovernanceAuditPanel() {
    const [guardrails, setGuardrails] = React.useState(FALLBACK_GUARDRAILS);
    const [auditEntries, setAuditEntries] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const loadGovernance = async () => {
        setLoading(true);
        setError(null);
        try {
            const [guardrailsResp, auditResp] = await Promise.all([
                api.getGuardrails(),
                api.getAuditLog(20)
            ]);
            setGuardrails(guardrailsResp.guardrails || FALLBACK_GUARDRAILS);
            setAuditEntries(auditResp.entries || []);
        } catch (e) {
            setError('Governance service unavailable. Using fallback guardrails.');
            setGuardrails(FALLBACK_GUARDRAILS);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        loadGovernance();
    }, []);

    return (
        <Card className="bg-card/50 backdrop-blur h-full">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <ShieldCheck className="h-4 w-4 text-cyan-400" />
                            Governance & Audit
                        </CardTitle>
                        <CardDescription>
                            Guardrails, non-action boundaries, and audit trail.
                        </CardDescription>
                    </div>
                    {loading && <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />}
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {error && (
                    <div className="text-xs text-destructive">{error}</div>
                )}

                <div>
                    <p className="text-xs text-muted-foreground mb-2">Non-Action Boundaries</p>
                    <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-1">
                        {(guardrails.non_action_boundaries || []).map((b) => (
                            <li key={b.id}>{b.description || b.id}</li>
                        ))}
                    </ul>
                </div>

                <div>
                    <p className="text-xs text-muted-foreground mb-2">Action Boundaries</p>
                    <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-1">
                        {(guardrails.action_boundaries || []).map((b) => (
                            <li key={b.id}>{b.description || b.id}</li>
                        ))}
                    </ul>
                </div>

                <div>
                    <p className="text-xs text-muted-foreground mb-2">Human Review Thresholds</p>
                    <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-1">
                        {(guardrails.confidence_thresholds || []).map((t) => (
                            <li key={t.id || t.description}>
                                {t.description || t.id}
                            </li>
                        ))}
                    </ul>
                </div>

                <div>
                    <p className="text-xs text-muted-foreground mb-2">Ethical Risk Questions</p>
                    <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-1">
                        {(guardrails.socratic_questions || []).map((q, idx) => (
                            <li key={`q-${idx}`}>{q}</li>
                        ))}
                    </ul>
                </div>

                <div>
                    <p className="text-xs text-muted-foreground mb-2">Escalation Paths</p>
                    {guardrails.escalation_paths ? (
                        <ul className="text-xs text-muted-foreground space-y-2">
                            {Object.entries(guardrails.escalation_paths).map(([level, path]) => (
                                <li key={level} className="border border-border/50 rounded p-2">
                                    <div className="font-medium text-foreground">{level}</div>
                                    <div className="text-[10px]">Initial: {path.initial_responder}</div>
                                    <div className="text-[10px]">Chain: {(path.escalation_chain || []).join(' → ') || 'None'}</div>
                                    <div className="text-[10px]">Max response: {path.max_response_time_minutes} mins</div>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-xs text-muted-foreground">No escalation paths configured.</p>
                    )}
                </div>

                <div>
                    <p className="text-xs text-muted-foreground mb-2">Audit Trail (latest)</p>
                    {auditEntries.length === 0 ? (
                        <p className="text-xs text-muted-foreground">No audit events recorded.</p>
                    ) : (
                        <ul className="text-xs text-muted-foreground space-y-2">
                            {auditEntries.map((entry, idx) => (
                                <li key={`audit-${idx}`} className="border border-border/50 rounded p-2">
                                    <div className="flex justify-between">
                                        <span className="font-medium text-foreground">{entry.action}</span>
                                        <span className="text-[10px]">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    {entry.details?.scenario && (
                                        <div className="text-[10px]">Scenario: {entry.details.scenario}</div>
                                    )}
                                    <div className="text-[10px]">Actor: {entry.actor}</div>
                                    {entry.details?.notes && (
                                        <div className="text-[10px]">Notes: {entry.details.notes}</div>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </CardContent>
            <CardFooter>
                <Button onClick={loadGovernance} disabled={loading} variant="outline" className="w-full gap-2">
                    {loading ? (
                        <>
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Refreshing...
                        </>
                    ) : (
                        <>
                            <RefreshCw className="h-3 w-3" />
                            Refresh Governance
                        </>
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
}
