import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, Users, TrendingUp, AlertTriangle, ShieldCheck, CheckCircle, XCircle, BrainCircuit, ChevronRight, FileText, Download } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const data = [
    { time: '10:00', velocity: 12 },
    { time: '10:30', velocity: 19 },
    { time: '11:00', velocity: 35 },
    { time: '11:30', velocity: 68 },
    { time: '12:00', velocity: 84 },
    { time: '12:30', velocity: 92 },
    { time: '13:00', velocity: 88 },
];

const demographicsData = [
    { name: 'Gen-Z', value: 35 },
    { name: 'Millennials', value: 40 },
    { name: 'Boomers', value: 15 },
    { name: 'Corporates', value: 10 },
];
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042'];

export default function Dashboard() {
    const [activeScenario, setActiveScenario] = useState("Data Leak Rumor");

    return (
        <div className="space-y-6">
            {/* 1. Scenario Selection & Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Simulation Dashboard</h1>
                    <p className="text-muted-foreground mt-1">Live monitoring of reputational risk vectors.</p>
                </div>
                <div className="flex items-center gap-2 bg-card/50 p-2 rounded-lg border border-border/50 backdrop-blur">
                    <span className="text-sm font-medium text-muted-foreground px-2">Scenario:</span>
                    <select
                        className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer"
                        value={activeScenario}
                        onChange={(e) => setActiveScenario(e.target.value)}
                    >
                        <option>Data Leak Rumor</option>
                        <option>Service Outage</option>
                        <option>Executive Misconduct (Deepfake)</option>
                    </select>
                    <Button size="sm" variant="outline" className="ml-2 h-8 hidden lg:flex">
                        <Download className="mr-2 h-3.5 w-3.5" />
                        Export Briefing
                    </Button>
                    <Button size="sm" className="ml-2 h-8">
                        <Activity className="mr-2 h-3.5 w-3.5" />
                        Run Simulation
                    </Button>
                </div>
            </div>

            {/* 2. Key Metrics including Confidence */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-card/50 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Contagion Velocity</CardTitle>
                        <Activity className="h-4 w-4 text-destructive" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-destructive">84.2 / 100</div>
                        <p className="text-xs text-muted-foreground">+12% from last hour</p>
                    </CardContent>
                </Card>

                <Card className="bg-card/50 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Model Confidence</CardTitle>
                        <BrainCircuit className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-purple-500">85%</div>
                        <div className="flex items-center mt-1 space-x-1">
                            <ShieldCheck className="h-3 w-3 text-green-500" />
                            <p className="text-xs text-muted-foreground">Adversarial Validated</p>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-card/50 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Projected Impact</CardTitle>
                        <TrendingUp className="h-4 w-4 text-amber-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-amber-500">High</div>
                        <p className="text-xs text-muted-foreground">Sentiment Shift &gt; 15%</p>
                    </CardContent>
                </Card>

                <Card className="bg-card/50 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">3</div>
                        <p className="text-xs text-muted-foreground">Requires attention</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Main Chart */}
                <Card className="col-span-4 bg-card/50 backdrop-blur">
                    <CardHeader>
                        <CardTitle>Risk Velocity Over Time</CardTitle>
                        <CardDescription>
                            Predictive modeling of rumor spread over the next 4 hours.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pl-2">
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart
                                    data={data}
                                    margin={{
                                        top: 10,
                                        right: 30,
                                        left: 0,
                                        bottom: 0,
                                    }}
                                >
                                    <defs>
                                        <linearGradient id="colorVelocity" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                                    <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                        itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    />
                                    <Area type="monotone" dataKey="velocity" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorVelocity)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Demographics Chart (New) */}
                <Card className="col-span-3 lg:col-span-3 bg-card/50 backdrop-blur">
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">Agent Demographics</CardTitle>
                        <CardDescription>Simulated population breakdown</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[200px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={demographicsData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {demographicsData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                        itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    />
                                    <Legend
                                        layout="vertical"
                                        verticalAlign="middle"
                                        align="right"
                                        iconSize={8}
                                        wrapperStyle={{ fontSize: '10px' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* 3. Governance & Strategy Panel */}
                <div className="col-span-3 lg:col-span-4 space-y-4">
                    <Card className="bg-card/50 backdrop-blur border-l-4 border-l-amber-500">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg">Response Strategy</CardTitle>
                                <ShieldCheck className="h-5 w-5 text-amber-500" />
                            </div>
                            <CardDescription>AI Recommendation (Confidence: High)</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm font-medium">Issue proactive clarification on vendor security standards.</p>
                            <p className="text-xs text-muted-foreground mt-2">Reasoning: Signal cluster indicates specific technical fears regarding 3rd party API.</p>
                        </CardContent>
                        <CardFooter className="flex gap-2 justify-end">
                            <Button variant="outline" size="sm" className="text-destructive hover:bg-destructive/10">Reject</Button>
                            <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white">
                                <CheckCircle className="mr-2 h-4 w-4" /> Approve
                            </Button>
                        </CardFooter>
                    </Card>
                </div>

                <div className="col-span-3 lg:col-span-3">
                    <Card className="bg-card/50 backdrop-blur h-full">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium">Recent Detected Signals</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {[
                                    { source: 'Twitter/X', text: '@MashreqBot Is the app down? Cannot login...', sentiment: 'Negative', time: '2m ago' },
                                    { source: 'Reddit', text: 'Rumors of a data breach on r/CyberSecurity...', sentiment: 'Neutral', time: '5m ago' },
                                    { source: 'News', text: 'Central Bank announces new regulations...', sentiment: 'Positive', time: '12m ago' },
                                ].map((item, i) => (
                                    <div key={i} className="flex items-start space-x-4 border-b border-border/40 pb-3 last:border-0 last:pb-0">
                                        <div className="space-y-1 w-full">
                                            <div className="flex justify-between">
                                                <p className="text-xs font-semibold text-primary">{item.source}</p>
                                                <span className="text-[10px] text-muted-foreground">{item.time}</span>
                                            </div>
                                            <p className="text-xs text-muted-foreground line-clamp-2">
                                                {item.text}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
