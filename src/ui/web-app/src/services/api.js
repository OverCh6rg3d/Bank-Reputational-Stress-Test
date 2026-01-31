/**
 * API Service for the Reputational Stress-Test Simulator
 * Provides REST and WebSocket connections to the backend
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';

/**
 * REST API client
 */
export const api = {
    /**
     * Get all scenarios
     */
    async getScenarios() {
        const response = await fetch(`${API_BASE}/api/scenarios`);
        if (!response.ok) throw new Error('Failed to fetch scenarios');
        return response.json();
    },

    /**
     * Get a specific scenario
     */
    async getScenario(id) {
        const response = await fetch(`${API_BASE}/api/scenarios/${id}`);
        if (!response.ok) throw new Error('Failed to fetch scenario');
        return response.json();
    },

    /**
     * Get signals with optional filtering
     */
    async getSignals(limit = 50, category = null) {
        const params = new URLSearchParams({ limit });
        if (category) params.append('category', category);

        const response = await fetch(`${API_BASE}/api/signals?${params}`);
        if (!response.ok) throw new Error('Failed to fetch signals');
        return response.json();
    },

    /**
     * Get agent archetypes
     */
    async getAgents(limit = 20) {
        const response = await fetch(`${API_BASE}/api/agents?limit=${limit}`);
        if (!response.ok) throw new Error('Failed to fetch agents');
        return response.json();
    },

    /**
     * Run signal detection
     */
    async detectSignals() {
        const response = await fetch(`${API_BASE}/api/detect`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to run detection');
        return response.json();
    },

    /**
     * Run adversarial debate
     */
    async runDebate(params) {
        const response = await fetch(`${API_BASE}/api/analysis/debate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        if (!response.ok) throw new Error('Failed to run debate');
        return response.json();
    },

    /**
     * Record governance decision
     */
    async recordDecision(incidentId, decision, reviewerId, notes = '') {
        const response = await fetch(`${API_BASE}/api/governance/decision`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                incident_id: incidentId,
                decision,
                reviewer_id: reviewerId,
                notes,
            }),
        });
        if (!response.ok) throw new Error('Failed to record decision');
        return response.json();
    }
};

/**
 * WebSocket connection manager for real-time simulation
 */
export class SimulationWebSocket {
    constructor(onMessage, onError, onClose) {
        this.ws = null;
        this.onMessage = onMessage;
        this.onError = onError;
        this.onClose = onClose;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(`${WS_BASE}/ws/simulation`);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.reconnectAttempts = 0;
                    resolve(this);
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.onMessage?.(data);
                    } catch (e) {
                        console.error('Failed to parse WebSocket message:', e);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.onError?.(error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket closed');
                    this.onClose?.();
                    this.attemptReconnect();
                };
            } catch (error) {
                reject(error);
            }
        });
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            setTimeout(() => this.connect().catch(() => { }), 2000 * this.reconnectAttempts);
        }
    }

    send(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    startSimulation(scenarioId, scenarioName, speed = 1.0, duration = 24) {
        this.send({
            action: 'start',
            scenario_id: scenarioId,
            scenario_name: scenarioName,
            speed,
            duration,
        });
    }

    pauseSimulation() {
        this.send({ action: 'pause' });
    }

    stopSimulation() {
        this.send({ action: 'stop' });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

/**
 * Create a simulation WebSocket connection
 */
export function createSimulationSocket(handlers) {
    return new SimulationWebSocket(
        handlers.onMessage,
        handlers.onError,
        handlers.onClose
    );
}

export default api;
