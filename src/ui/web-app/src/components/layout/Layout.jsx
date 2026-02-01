import React, { useState } from 'react';
import { ShieldAlert, Activity, FileText, Settings, Menu, Bell } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { useSimulation } from '../../context/SimulationContext';

export default function Layout({ children }) {
    const { criticalAlerts } = useSimulation();
    const [alertsOpen, setAlertsOpen] = useState(false);
    const orderedAlerts = [...criticalAlerts].reverse();

    return (
        <div className="min-h-screen bg-background text-foreground flex">

            {/* Main Content */}
            <main className="flex-1 flex flex-col">
                <header className="h-16 border-b border-border/50 flex items-center justify-between px-6 bg-background/50 backdrop-blur-sm sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Button variant="ghost" size="icon" className="md:hidden">
                                <Menu className="h-5 w-5" />
                            </Button>
                            <img
                                src="/logo.png"
                                alt="Reputational Stress Test Simulator"
                                className="h-8 w-8 rounded-sm"
                            />
                            <span className="hidden sm:inline text-sm font-semibold tracking-tight">
                                Reputational Stress Test
                            </span>
                        </div>
                    </div>

                    <div className="ml-auto flex items-center gap-4">
                        <div className="relative">
                            <Button
                                variant="ghost"
                                size="icon"
                                className="relative"
                                onClick={() => setAlertsOpen((open) => !open)}
                                aria-expanded={alertsOpen}
                                aria-haspopup="true"
                                aria-label="Critical alerts"
                            >
                                <Bell className="h-5 w-5" />
                                {criticalAlerts.length > 0 && (
                                    <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-destructive text-destructive-foreground text-[10px] rounded-full flex items-center justify-center">
                                        {criticalAlerts.length > 9 ? '9+' : criticalAlerts.length}
                                    </span>
                                )}
                            </Button>

                            {alertsOpen && (
                                <div className="absolute right-0 mt-2 w-80 rounded-md border border-border bg-card shadow-lg z-20">
                                    <div className="px-3 py-2 border-b border-border text-sm font-semibold">
                                        Critical Alerts
                                    </div>
                                    <div className="max-h-72 overflow-auto">
                                        {orderedAlerts.length === 0 ? (
                                            <div className="px-3 py-3 text-xs text-muted-foreground">
                                                No critical alerts
                                            </div>
                                        ) : (
                                            orderedAlerts.map(alert => (
                                                <div key={alert.id} className="px-3 py-2 border-b border-border/60 last:border-b-0">
                                                    <div className="text-xs text-muted-foreground">{alert.time}</div>
                                                    <div className="text-sm font-medium text-destructive">{alert.message}</div>
                                                    <div className="text-xs text-muted-foreground">
                                                        Velocity: {typeof alert.velocity === 'number' ? `${alert.velocity}%` : 'N/A'}
                                                    </div>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center border border-primary/50">
                            <span className="font-bold text-xs">AD</span>
                        </div>
                    </div>
                </header>

                <div className="flex-1 p-6 overflow-auto">
                    {children}
                </div>
            </main>
        </div>
    );
}
