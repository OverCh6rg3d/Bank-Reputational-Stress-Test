import React from 'react';
import { ShieldAlert, Activity, FileText, Settings, Menu, Bell } from 'lucide-react';
import { Button } from "@/components/ui/button";

export default function Layout({ children }) {
    return (
        <div className="min-h-screen bg-background text-foreground flex">
            {/* Sidebar */}
            <aside className="w-64 border-r border-border bg-card/50 hidden md:flex flex-col">
                <div className="p-6 flex items-center gap-2 border-b border-border/50">
                    <ShieldAlert className="h-6 w-6 text-primary" />
                    <span className="font-bold text-lg tracking-tight">StressTest.ai</span>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <Button variant="ghost" className="w-full justify-start gap-2 bg-accent/50 text-accent-foreground">
                        <Activity className="h-4 w-4" />
                        Simulation Run
                    </Button>
                    <Button variant="ghost" className="w-full justify-start gap-2">
                        <FileText className="h-4 w-4" />
                        Scenarios
                    </Button>
                    <Button variant="ghost" className="w-full justify-start gap-2">
                        <Settings className="h-4 w-4" />
                        Configuration
                    </Button>
                </nav>

                <div className="p-4 border-t border-border/50">
                    <div className="rounded-lg bg-muted/50 p-3 text-xs">
                        <p className="font-semibold text-primary">System Status</p>
                        <div className="flex items-center gap-2 mt-2 text-muted-foreground">
                            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                            Signal Monitor Active
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col">
                <header className="h-16 border-b border-border/50 flex items-center justify-between px-6 bg-background/50 backdrop-blur-sm sticky top-0 z-10">
                    <div className="flex items-center gap-4 md:hidden">
                        <Button variant="ghost" size="icon">
                            <Menu className="h-5 w-5" />
                        </Button>
                    </div>

                    <div className="ml-auto flex items-center gap-4">
                        <Button variant="outline" size="sm" className="hidden sm:flex">
                            Wait-Mode: Active
                        </Button>
                        <Button variant="ghost" size="icon" className="relative">
                            <Bell className="h-5 w-5" />
                            <span className="absolute top-2 right-2 h-2 w-2 bg-destructive rounded-full"></span>
                        </Button>
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
