import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlusCircle, Zap } from "lucide-react";
import { useSimulation } from '../../context/SimulationContext';

export default function SignalInjection() {
    const { injectSignal } = useSimulation();
    const [isOpen, setIsOpen] = useState(false);
    const [text, setText] = useState("");
    const [platform, setPlatform] = useState("Twitter/X");

    const handleInject = () => {
        if (!text) return;
        injectSignal({
            id: Date.now(),
            source: platform,
            text: text,
            sentiment: "Negative",
            time: "Just now",
            platform: platform.toLowerCase()
        });
        setText("");
        setIsOpen(false);
    };

    if (!isOpen) {
        return (
            <Button variant="outline" className="w-full border-dashed border-2 h-[100px] flex flex-col gap-2 hover:bg-accent/50" onClick={() => setIsOpen(true)}>
                <Zap className="h-6 w-6 text-primary" />
                <span>Inject Synthetic Signal</span>
            </Button>
        );
    }

    return (
        <Card className="bg-card/50 backdrop-blur w-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Inject Synthetic Signal</CardTitle>
                <CardDescription>Manually trigger a stress vector</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
                <select
                    className="w-full bg-background border border-input rounded px-3 py-1 text-sm focus:outline-none"
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                >
                    <option>Twitter/X</option>
                    <option>Reddit</option>
                    <option>News Portal</option>
                </select>
                <textarea
                    className="w-full h-20 bg-background border border-input rounded p-2 text-sm focus:outline-none resize-none"
                    placeholder="Enter rumor text..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />
            </CardContent>
            <CardFooter className="flex justify-between pt-0">
                <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>Cancel</Button>
                <Button size="sm" onClick={handleInject} disabled={!text}>Inject</Button>
            </CardFooter>
        </Card>
    );
}
