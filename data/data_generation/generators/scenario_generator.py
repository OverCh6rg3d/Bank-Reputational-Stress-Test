"""
Scenario Generator
Creates pre-packaged stress test scenarios for the Reputational Stress-Test Simulator
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


# Pre-defined scenario templates
SCENARIO_TEMPLATES = [
    {
        "scenario_name": "Data Leak Panic",
        "description": "A rumor spreads that customer data has been leaked from a third-party vendor. High fear, rapid spread.",
        "trigger_category": "Fraud_Rumor",
        "target_segment": "All",
        "simulation_duration_hours": 24,
        "severity_level": "Critical",
        "expected_velocity_peak": 85,
        "recommended_response_time_hours": 2,
        "key_narratives": [
            "Customer database leaked on dark web",
            "Third-party vendor breach",
            "Personal information for sale"
        ],
        "monitoring_keywords": ["leak", "breach", "data", "hacked", "dark web", "personal info", "sold"],
        "potential_impact": {
            "trust_erosion": "High",
            "customer_churn_risk": "Medium-High",
            "regulatory_attention": "High",
            "media_coverage": "Likely"
        }
    },
    {
        "scenario_name": "OTP Bypass Exploit",
        "description": "Technical claims about OTP security vulnerability spread among tech-savvy users.",
        "trigger_category": "Fraud_Rumor",
        "target_segment": "HNI",
        "simulation_duration_hours": 12,
        "severity_level": "Critical",
        "expected_velocity_peak": 90,
        "recommended_response_time_hours": 1,
        "key_narratives": [
            "OTP intercept vulnerability discovered",
            "Hackers bypassing 2FA",
            "SS7 attack on banking OTPs"
        ],
        "monitoring_keywords": ["OTP", "bypass", "hack", "2FA", "vulnerability", "SS7", "intercept"],
        "potential_impact": {
            "trust_erosion": "Critical",
            "customer_churn_risk": "Medium",
            "regulatory_attention": "Very High",
            "media_coverage": "Very Likely"
        }
    },
    {
        "scenario_name": "App Outage Cascade",
        "description": "Extended app downtime during salary week causes mass complaints and competitor comparisons.",
        "trigger_category": "Service_Outage",
        "target_segment": "GenZ,Millennial",
        "simulation_duration_hours": 6,
        "severity_level": "High",
        "expected_velocity_peak": 75,
        "recommended_response_time_hours": 0.5,
        "key_narratives": [
            "App down during salary credits",
            "Can't access money for bills",
            "Moving to competitor"
        ],
        "monitoring_keywords": ["app down", "not working", "can't login", "salary", "bills", "switch bank"],
        "potential_impact": {
            "trust_erosion": "Medium",
            "customer_churn_risk": "High",
            "regulatory_attention": "Low",
            "media_coverage": "Possible"
        }
    },
    {
        "scenario_name": "Fee Increase Backlash",
        "description": "Rumors about hidden fee increases spread, amplified by competitor marketing.",
        "trigger_category": "Competitor_News",
        "target_segment": "SME_Owner",
        "simulation_duration_hours": 48,
        "severity_level": "Medium",
        "expected_velocity_peak": 55,
        "recommended_response_time_hours": 4,
        "key_narratives": [
            "Hidden fee increases without notice",
            "Competitor offers better rates",
            "Business account charges doubled"
        ],
        "monitoring_keywords": ["fees", "hidden", "charges", "expensive", "switch", "competitor", "better"],
        "potential_impact": {
            "trust_erosion": "Medium",
            "customer_churn_risk": "High",
            "regulatory_attention": "Low",
            "media_coverage": "Unlikely"
        }
    },
    {
        "scenario_name": "Phishing Wave",
        "description": "Coordinated phishing campaign targets customers with convincing fake communications.",
        "trigger_category": "Fraud_Rumor",
        "target_segment": "Vulnerable",
        "simulation_duration_hours": 18,
        "severity_level": "High",
        "expected_velocity_peak": 70,
        "recommended_response_time_hours": 1,
        "key_narratives": [
            "Realistic phishing emails circulating",
            "Customers losing money to scams",
            "Bank not warning customers fast enough"
        ],
        "monitoring_keywords": ["phishing", "email", "fake", "scam", "lost money", "warning", "alert"],
        "potential_impact": {
            "trust_erosion": "High",
            "customer_churn_risk": "Medium",
            "regulatory_attention": "High",
            "media_coverage": "Likely"
        }
    },
    {
        "scenario_name": "Customer Service Meltdown",
        "description": "Multiple customers report long wait times and unresolved issues simultaneously.",
        "trigger_category": "Service_Outage",
        "target_segment": "All",
        "simulation_duration_hours": 12,
        "severity_level": "Medium",
        "expected_velocity_peak": 60,
        "recommended_response_time_hours": 2,
        "key_narratives": [
            "Hours on hold with no response",
            "Issues not resolved after multiple calls",
            "Inconsistent information from agents"
        ],
        "monitoring_keywords": ["customer service", "no response", "hours", "waiting", "not resolved", "useless"],
        "potential_impact": {
            "trust_erosion": "Medium",
            "customer_churn_risk": "Medium",
            "regulatory_attention": "Low",
            "media_coverage": "Unlikely"
        }
    },
    {
        "scenario_name": "Competitor Viral Campaign",
        "description": "A competitor launches aggressive marketing highlighting gaps in your services.",
        "trigger_category": "Competitor_News",
        "target_segment": "GenZ,Millennial",
        "simulation_duration_hours": 72,
        "severity_level": "Low",
        "expected_velocity_peak": 40,
        "recommended_response_time_hours": 12,
        "key_narratives": [
            "Competitor offering cashback for switching",
            "Side-by-side comparison going viral",
            "Influencers promoting competitor"
        ],
        "monitoring_keywords": ["switch", "better", "cashback", "promo", "influencer", "comparison"],
        "potential_impact": {
            "trust_erosion": "Low",
            "customer_churn_risk": "Medium",
            "regulatory_attention": "None",
            "media_coverage": "Unlikely"
        }
    },
    {
        "scenario_name": "International Transfer Freeze",
        "description": "Customers report international transfers stuck or reversed, causing panic.",
        "trigger_category": "Service_Outage",
        "target_segment": "HNI,SME_Owner",
        "simulation_duration_hours": 8,
        "severity_level": "High",
        "expected_velocity_peak": 70,
        "recommended_response_time_hours": 1,
        "key_narratives": [
            "International transfers failing",
            "Money stuck in limbo for days",
            "Business payments not reaching suppliers"
        ],
        "monitoring_keywords": ["international", "transfer", "stuck", "failed", "payment", "abroad", "supplier"],
        "potential_impact": {
            "trust_erosion": "High",
            "customer_churn_risk": "High",
            "regulatory_attention": "Medium",
            "media_coverage": "Possible"
        }
    },
    {
        "scenario_name": "Coordinated Bot Attack",
        "description": "Suspected bot network flooding social media with negative content.",
        "trigger_category": "Fraud_Rumor",
        "target_segment": "All",
        "simulation_duration_hours": 4,
        "severity_level": "Medium",
        "expected_velocity_peak": 95,
        "recommended_response_time_hours": 0.5,
        "key_narratives": [
            "Sudden spike in identical complaints",
            "Suspicious new accounts posting",
            "Coordinated negative campaign"
        ],
        "monitoring_keywords": ["multiple", "same", "suspicious", "accounts", "coordinated", "attack"],
        "potential_impact": {
            "trust_erosion": "Low-Medium",
            "customer_churn_risk": "Low",
            "regulatory_attention": "Low",
            "media_coverage": "Unlikely"
        }
    },
    {
        "scenario_name": "Positive Viral Campaign",
        "description": "Organic positive sentiment following product launch or customer success story.",
        "trigger_category": "Positive_Neutral",
        "target_segment": "All",
        "simulation_duration_hours": 24,
        "severity_level": "Positive",
        "expected_velocity_peak": 50,
        "recommended_response_time_hours": 4,
        "key_narratives": [
            "Customer success story going viral",
            "New feature praised by users",
            "Community appreciation post"
        ],
        "monitoring_keywords": ["love", "amazing", "great", "thank you", "recommend", "best"],
        "potential_impact": {
            "trust_erosion": "Negative (Improvement)",
            "customer_churn_risk": "Low",
            "regulatory_attention": "None",
            "media_coverage": "Possible (Positive)"
        }
    },
    {
        "scenario_name": "Insider Threat Rumor",
        "description": "Claims of employee involvement in fraud or data theft spread online.",
        "trigger_category": "Fraud_Rumor",
        "target_segment": "HNI",
        "simulation_duration_hours": 36,
        "severity_level": "Critical",
        "expected_velocity_peak": 80,
        "recommended_response_time_hours": 2,
        "key_narratives": [
            "Employee selling customer data",
            "Internal access misused",
            "Former employee with grudge leaking info"
        ],
        "monitoring_keywords": ["employee", "insider", "internal", "selling data", "access", "corrupt"],
        "potential_impact": {
            "trust_erosion": "Critical",
            "customer_churn_risk": "Medium-High",
            "regulatory_attention": "Very High",
            "media_coverage": "Very Likely"
        }
    },
    {
        "scenario_name": "ATM Network Failure",
        "description": "Widespread ATM outages across the city during peak hours.",
        "trigger_category": "Service_Outage",
        "target_segment": "All",
        "simulation_duration_hours": 4,
        "severity_level": "High",
        "expected_velocity_peak": 65,
        "recommended_response_time_hours": 0.5,
        "key_narratives": [
            "All ATMs showing out of order",
            "Can't withdraw cash for emergency",
            "No alternative payment options"
        ],
        "monitoring_keywords": ["ATM", "out of order", "cash", "withdraw", "emergency", "down"],
        "potential_impact": {
            "trust_erosion": "Medium",
            "customer_churn_risk": "Low",
            "regulatory_attention": "Low",
            "media_coverage": "Possible"
        }
    }
]


def generate_scenarios() -> List[Dict[str, Any]]:
    """Generate all pre-packaged scenarios with unique IDs."""
    scenarios = []
    
    for template in SCENARIO_TEMPLATES:
        scenario = {
            "scenario_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            **template
        }
        scenarios.append(scenario)
    
    return scenarios


def save_scenarios_json(scenarios: List[Dict[str, Any]], output_path: Path):
    """Save scenarios to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(scenarios)} scenarios to {output_path}")


def main():
    """Main entry point for scenario generation."""
    print("=" * 60)
    print("Scenario Definitions Generator")
    print("=" * 60)
    
    # Generate scenarios
    scenarios = generate_scenarios()
    
    # Save to datasets folder
    output_dir = Path(__file__).parent.parent.parent / "datasets"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "scenario_definitions.json"
    save_scenarios_json(scenarios, output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Generated Scenarios:")
    print("=" * 60)
    
    for scenario in scenarios:
        severity = scenario.get("severity_level", "Unknown")
        duration = scenario.get("simulation_duration_hours", 0)
        print(f"  • {scenario['scenario_name']} ({severity}, {duration}h)")
    
    print(f"\nTotal: {len(scenarios)} scenarios generated")
    return scenarios


if __name__ == "__main__":
    main()
