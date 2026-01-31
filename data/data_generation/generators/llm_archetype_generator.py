"""
LLM-Enhanced Archetype Generator
Generates high-quality, detailed customer personas using GPT-4o
"""

import json
import uuid
import random
import csv
from pathlib import Path
from typing import Dict, List, Any

from .llm_client import generate_json_completion, SYSTEM_PROMPTS

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def load_distributions() -> Dict[str, Any]:
    """Load value distributions from JSON template."""
    with open(TEMPLATE_DIR / "value_distributions.json", "r") as f:
        return json.load(f)


# Detailed demographic contexts for rich persona generation
DEMOGRAPHIC_CONTEXTS = {
    "GenZ": {
        "age_range": "18-25",
        "description": "Young adults in the UAE, digital natives, first-time banking customers",
        "common_occupations": [
            "university student", "intern", "junior developer", "barista", 
            "content creator", "delivery driver", "retail staff", "freelance designer"
        ],
        "financial_situations": [
            "living off part-time income", "supported by parents", 
            "first real job", "building credit history", "learning to budget"
        ],
        "banking_concerns": [
            "mobile app usability", "instant transfers", "no hidden fees",
            "crypto-friendly services", "social payments", "student offers"
        ]
    },
    "Millennial": {
        "age_range": "26-42",
        "description": "Established professionals in the UAE, family-focused, tech-savvy",
        "common_occupations": [
            "software engineer", "marketing manager", "accountant", "teacher",
            "nurse", "project manager", "entrepreneur", "HR professional"
        ],
        "financial_situations": [
            "saving for home", "paying off car loan", "building family savings",
            "investing for future", "managing household budget", "dual income family"
        ],
        "banking_concerns": [
            "mortgage rates", "family accounts", "education savings",
            "investment options", "insurance bundles", "rewards programs"
        ]
    },
    "SME_Owner": {
        "age_range": "28-55",
        "description": "Small and medium business owners in UAE, managing business finances",
        "common_occupations": [
            "restaurant owner", "e-commerce seller", "contractor", "consultant",
            "trading company owner", "retail shop owner", "services provider", "manufacturer"
        ],
        "financial_situations": [
            "managing cash flow", "seasonal business", "expanding operations",
            "paying staff salaries", "dealing with suppliers", "tax compliance"
        ],
        "banking_concerns": [
            "business loans", "POS systems", "international transfers",
            "multi-currency accounts", "trade finance", "merchant services"
        ]
    },
    "HNI": {
        "age_range": "35-65",
        "description": "High Net Worth Individuals, executives, investors, established wealth",
        "common_occupations": [
            "CEO", "real estate investor", "private equity partner", "family business heir",
            "retired executive", "portfolio manager", "serial entrepreneur", "consultant"
        ],
        "financial_situations": [
            "managing investment portfolio", "wealth preservation", "estate planning",
            "international investments", "tax optimization", "philanthropy"
        ],
        "banking_concerns": [
            "private banking", "wealth management", "priority service",
            "exclusive benefits", "confidentiality", "global access"
        ]
    },
    "Vulnerable": {
        "age_range": "20-70",
        "description": "Customers in vulnerable situations - financial distress, elderly, new migrants",
        "common_occupations": [
            "domestic worker", "construction laborer", "recently unemployed", "retired pensioner",
            "new migrant worker", "gig economy driver", "elderly dependent", "temporary worker"
        ],
        "financial_situations": [
            "living paycheck to paycheck", "supporting family abroad", "debt problems",
            "limited savings", "unfamiliar with banking", "fixed pension income"
        ],
        "banking_concerns": [
            "low fees", "simple interface", "multilingual support",
            "remittance services", "basic savings", "avoiding fraud"
        ]
    }
}


def generate_archetype_prompt(segment: str, index: int) -> str:
    """Build the prompt for generating an archetype."""
    context = DEMOGRAPHIC_CONTEXTS[segment]
    
    prompt = f"""Create a unique, realistic customer persona for a UAE bank stress-test simulation.

DEMOGRAPHIC SEGMENT: {segment}
- Age range: {context["age_range"]}
- Description: {context["description"]}

Example occupations for this segment: {", ".join(context["common_occupations"])}
Example financial situations: {", ".join(context["financial_situations"])}
Main banking concerns: {", ".join(context["banking_concerns"])}

Generate persona #{index + 1} for this segment. Make them feel like a REAL person in the UAE.
Include their specific backstory, personality quirks, and how they would react in a banking crisis.

Return as JSON with these exact fields:
{{
    "archetype_name": "A descriptive 2-4 word name like 'Anxious First-Time Investor' or 'Tech-Averse Retiree'",
    "backstory": "A 2-3 sentence backstory making them feel real",
    "financial_literacy": 1-10 (how well they understand banking/finance),
    "brand_loyalty": 0-100 (how loyal to their current bank),
    "skepticism_score": 1-10 (how skeptical of banking news/claims),
    "network_influence": 1-100 (social media reach/influence),
    "activity_frequency": 0.1-10.0 (posts per day on social media),
    "preferred_platform": "X_Style" or "Reddit_Style" or "LinkedIn_Style" or "News_Portal",
    "core_values": ["list of 2-4 values from: Security, Speed, Transparency, Ethics, Innovation, Trust, Convenience, Privacy, Stability, Growth, Family, Independence, Community, Wealth, Simplicity, Technology, Tradition, Flexibility, Status, Fairness"],
    "crisis_reaction": "How they would typically react to negative banking news (1 sentence)"
}}"""
    
    return prompt


def generate_all_archetypes_llm(target_count: int = 150) -> List[Dict[str, Any]]:
    """Generate all archetypes using LLM."""
    distributions = load_distributions()
    archetypes = []
    
    segments = distributions["demographic_segments"]
    
    print("Generating archetypes using GPT-4o...")
    
    for segment_name, segment_config in segments.items():
        segment_count = max(15, int(target_count * segment_config["distribution_weight"]))
        
        print(f"\n📊 Generating {segment_count} archetypes for {segment_name}...")
        
        for i in range(segment_count):
            if (i + 1) % 5 == 0:
                print(f"  Generated {i + 1}/{segment_count}...")
            
            prompt = generate_archetype_prompt(segment_name, i)
            
            try:
                response = generate_json_completion(
                    system_prompt=SYSTEM_PROMPTS["archetype"],
                    user_prompt=prompt,
                    temperature=0.9,
                    max_tokens=600
                )
                
                # Build the archetype record
                archetype = {
                    "agent_id": str(uuid.uuid4()),
                    "archetype_name": response.get("archetype_name", f"{segment_name} Type {i+1}"),
                    "demographic_segment": segment_name,
                    "financial_literacy": max(1, min(10, int(response.get("financial_literacy", 5)))),
                    "brand_loyalty": max(0, min(100, int(response.get("brand_loyalty", 50)))),
                    "skepticism_score": max(1, min(10, int(response.get("skepticism_score", 5)))),
                    "network_influence": max(1, min(100, int(response.get("network_influence", 50)))),
                    "activity_frequency": max(0.1, min(10.0, float(response.get("activity_frequency", 2.0)))),
                    "preferred_platform": response.get("preferred_platform", "X_Style"),
                    "core_values": json.dumps(response.get("core_values", ["Trust", "Security"])),
                    "backstory": response.get("backstory", ""),
                    "crisis_reaction": response.get("crisis_reaction", "")
                }
                
                archetypes.append(archetype)
                
            except Exception as e:
                print(f"  Warning: Failed to generate archetype: {e}")
                # Fallback to basic archetype
                archetypes.append({
                    "agent_id": str(uuid.uuid4()),
                    "archetype_name": f"{segment_name} Type {i+1}",
                    "demographic_segment": segment_name,
                    "financial_literacy": 5,
                    "brand_loyalty": 50,
                    "skepticism_score": 5,
                    "network_influence": 50,
                    "activity_frequency": 2.0,
                    "preferred_platform": "X_Style",
                    "core_values": json.dumps(["Trust", "Security"]),
                    "backstory": "",
                    "crisis_reaction": ""
                })
    
    return archetypes


def save_archetypes_csv(archetypes: List[Dict[str, Any]], output_path: Path):
    """Save archetypes to CSV file."""
    if not archetypes:
        print("No archetypes to save!")
        return
    
    fieldnames = [
        "agent_id", "archetype_name", "demographic_segment",
        "financial_literacy", "brand_loyalty", "skepticism_score",
        "network_influence", "activity_frequency", "preferred_platform",
        "core_values", "backstory", "crisis_reaction"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(archetypes)
    
    print(f"✓ Saved {len(archetypes)} archetypes to {output_path}")


def main(target_count: int = 150):
    """Main entry point for LLM archetype generation."""
    print("=" * 60)
    print("LLM-Enhanced Archetype Generator (GPT-4o)")
    print("=" * 60)
    
    # Generate archetypes
    archetypes = generate_all_archetypes_llm(target_count=target_count)
    
    # Save to datasets folder
    output_dir = Path(__file__).parent.parent.parent / "datasets"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "agent_archetypes.csv"
    save_archetypes_csv(archetypes, output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Generation Summary:")
    print("=" * 60)
    
    from collections import Counter
    segment_counts = Counter(a["demographic_segment"] for a in archetypes)
    for segment, count in sorted(segment_counts.items()):
        print(f"  {segment}: {count} archetypes")
    
    print(f"\nTotal: {len(archetypes)} archetypes generated")
    
    # Show samples
    print("\nSample archetypes:")
    for a in random.sample(archetypes, min(3, len(archetypes))):
        print(f"  • {a['archetype_name']} ({a['demographic_segment']})")
        if a.get('backstory'):
            print(f"    {a['backstory'][:80]}...")
    
    return archetypes


if __name__ == "__main__":
    main(target_count=50)  # Small test batch
