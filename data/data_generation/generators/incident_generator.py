"""
Detected Incident Generator
Generates sample 'Governance Layer' data for the simulator.
Creates realistic detection/response records linked to defined scenarios.
"""

import csv
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any
import random

DATASETS_DIR = Path(__file__).parent.parent.parent / "datasets"

# Pre-defined outcomes for scenarios to simulate "AI Detection"
INCIDENT_TEMPLATES = {
    "Data Leak Panic": {
        "detected_severity": "Critical",
        "status": "Active",
        "confidence_score": 0.94,
        "ai_analysis": "Unusual spike in 'data breach' keywords (velocity +400%). Sentiment -0.8. Cross-referenced with similar 2024 incident. High probability of coordinated FUD (Fear/Uncertainty/Doubt).",
        "proposed_response": "1. Activate Crisis Protocol A. 2. Verify internal logs immediately. 3. Prepare 'No Breach' statement if false. 4. Flag accounts for bot behavior.",
        "human_action": "Pending_Review",
        "human_notes": ""
    },
    "OTP Bypass Exploit": {
        "detected_severity": "Critical",
        "status": "Active",
        "confidence_score": 0.88,
        "ai_analysis": "Cluster of 50+ claims regarding OTP bypass. Geolocation concentrated in Dubai. Keywords match known phishing scripts. Potential zero-day social engineering campaign.",
        "proposed_response": "1. Temporarily restrict high-value transfers. 2. Send push notification warning about OTP sharing. 3. Investigate specific affected UIDs.",
        "human_action": "Approved",
        "human_notes": "Acting CISO approved temporary limit."
    },
    "App Outage Cascade": {
        "detected_severity": "High",
        "status": "Mitigated",
        "confidence_score": 0.99,
        "ai_analysis": "Volume spike (300%) detected for 'login failed'. Correlates with server error rate > 5%. Sentiment -0.6 (frustration, not panic).",
        "proposed_response": "1. Acknowledge issue via X/Twitter support account. 2. Update status page. 3. ETA for fix: 30 mins.",
        "human_action": "Approved",
        "human_notes": "Comms team deployed status update."
    },
    "Fee Increase Backlash": {
        "detected_severity": "Medium",
        "status": "Active",
        "confidence_score": 0.72,
        "ai_analysis": "Negative sentiment trend (-0.4) related to 'annual fees'. Velocity is slowly increasing. Influencer account @DubaiFinanceGuy amplified the complaint.",
        "proposed_response": "1. Monitor sentiment velocity. 2. Prepare FAQ about fee structure value add. 3. Consider fee waiver for high-value segments if churn risk increases.",
        "human_action": "Pending_Review",
        "human_notes": "Waiting to see if it trends further."
    },
    "Insider Threat Rumor": {
        "detected_severity": "Critical",
        "status": "False_Positive",
        "confidence_score": 0.65,
        "ai_analysis": "Rumors of internal fraud detected. Source appears to be a single low-credibility account. No corroboration in transaction logs.",
        "proposed_response": "1. Monitor for spread. 2. Do not engage publicly (Streisand effect risk). 3. Conduct silent internal audit.",
        "human_action": "Rejected",
        "human_notes": "Verified as false. Marked as False Positive to silence alerts."
    },
    "Competitor Viral Campaign": {
        "detected_severity": "Low",
        "status": "Active",
        "confidence_score": 0.81,
        "ai_analysis": "Positive sentiment spike for competitor ENBD. Slight negative comparison drift for Mashreq. No operational risk.",
        "proposed_response": "1. No action required. 2. Marketing team notified for competitive analysis.",
        "human_action": "Pending_Review",
        "human_notes": ""
    }
}

def load_scenarios() -> List[Dict[str, Any]]:
    """Load scenarios from JSON file."""
    path = DATASETS_DIR / "scenario_definitions.json"
    if not path.exists():
        print("Scenarios file not found because it hasn't been generated yet.")
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_incidents() -> List[Dict[str, Any]]:
    """Generate detection records based on scenarios."""
    scenarios = load_scenarios()
    incidents = []
    
    print(f"Generating detection records for {len(scenarios)} scenarios...")
    
    for scenario in scenarios:
        name = scenario["scenario_name"]
        
        # Find matching template or generic fallback
        template = INCIDENT_TEMPLATES.get(name)
        if not template:
            # Fallback for scenarios not explicitly in template list
            severity = scenario.get("severity_level", "Medium")
            template = {
                "detected_severity": severity,
                "status": "Active",
                "confidence_score": round(random.uniform(0.7, 0.95), 2),
                "ai_analysis": f"Detected anomaly matching {name} profile. Severity level {severity}.",
                "proposed_response": "1. Acknowledge. 2. Investigate. 3. Mitigate.",
                "human_action": "Pending_Review",
                "human_notes": ""
            }
        
        incident = {
            "incident_id": str(uuid.uuid4()),
            "related_scenario_id": scenario["scenario_id"],
            **template
        }
        incidents.append(incident)
        
    return incidents

def save_incidents_csv(incidents: List[Dict[str, Any]]):
    """Save to CSV."""
    if not incidents:
        return
        
    path = DATASETS_DIR / "detected_incidents.csv"
    fieldnames = [
        "incident_id", "related_scenario_id", "detected_severity", "status",
        "confidence_score", "ai_analysis", "proposed_response",
        "human_action", "human_notes"
    ]
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(incidents)
        
    print(f"✓ Saved {len(incidents)} detected incidents to {path}")

def main():
    incidents = generate_incidents()
    save_incidents_csv(incidents)
    return incidents

if __name__ == "__main__":
    main()
