import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShieldCheck, CheckCircle, XCircle } from "lucide-react";

export default function GovernancePanel() {
    const [status, setStatus] = useState("pending"); // pending, approved, rejected

    return (
        <Card className={`bg-card/50 backdrop-blur border-l-4 ${status === 'approved' ? 'border-l-green-500' :
                status === 'rejected' ? 'border-l-destructive' : 'border-l-amber-500'
            }`}>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Response Strategy</CardTitle>
                    <ShieldCheck className={`h-5 w-5 ${status === 'approved' ? 'text-green-500' :
                            status === 'rejected' ? 'text-destructive' : 'text-amber-500'
                        }`} />
                </div>
                <CardDescription>AI Recommendation (Confidence: High)</CardDescription>
            </CardHeader>
            <CardContent>
                <p className="text-sm font-medium">Issue proactive clarification on vendor security standards.</p>
                <p className="text-xs text-muted-foreground mt-2">Reasoning: Signal cluster indicates specific technical fears regarding 3rd party API.</p>

                {status === 'approved' && (
                    <div className="mt-4 p-2 bg-green-500/10 rounded border border-green-500/20 text-xs text-green-500 flex items-center">
                        <CheckCircle className="h-3 w-3 mr-2" /> Approved by Risk Officer
                    </div>
                )}
                {status === 'rejected' && (
                    <div className="mt-4 p-2 bg-destructive/10 rounded border border-destructive/20 text-xs text-destructive flex items-center">
                        <XCircle className="h-3 w-3 mr-2" /> Rejected by Risk Officer
                    </div>
                )}
            </CardContent>
            {status === 'pending' && (
                <CardFooter className="flex gap-2 justify-end">
                    <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => setStatus('rejected')}
                    >
                        Reject
                    </Button>
                    <Button
                        size="sm"
                        className="bg-amber-500 hover:bg-amber-600 text-white"
                        onClick={() => setStatus('approved')}
                    >
                        <CheckCircle className="mr-2 h-4 w-4" /> Approve
                    </Button>
                </CardFooter>
            )}
        </Card>
    );
}
