"""
Agent Archetype Generator
Generates diverse customer personas for the Reputational Stress-Test Simulator
"""

import json
import uuid
import random
from pathlib import Path
from typing import Dict, List, Any
import csv

# Load distribution templates
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

def load_distributions() -> Dict[str, Any]:
    """Load value distributions from JSON template."""
    with open(TEMPLATE_DIR / "value_distributions.json", "r") as f:
        return json.load(f)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value within range."""
    return max(min_val, min(max_val, value))

def sample_from_distribution(dist: Dict[str, float]) -> float:
    """Sample a value from a normal distribution specification."""
    mean = dist["mean"]
    std = dist["std"]
    return random.gauss(mean, std)

def select_platform(platform_weights: Dict[str, float]) -> str:
    """Select a platform based on weights."""
    platforms = list(platform_weights.keys())
    weights = list(platform_weights.values())
    return random.choices(platforms, weights=weights, k=1)[0]

def select_core_values(segment: str, distributions: Dict[str, Any], num_values: int = 3) -> List[str]:
    """Select core values based on segment correlations."""
    correlated_values = distributions["value_correlations"].get(segment, [])
    all_values = distributions["core_values_pool"]
    
    # 70% chance to pick from correlated values, 30% from any
    selected = []
    for _ in range(num_values):
        if random.random() < 0.7 and correlated_values:
            value = random.choice(correlated_values)
        else:
            value = random.choice(all_values)
        if value not in selected:
            selected.append(value)
    
    return selected

# Archetype name templates by segment
ARCHETYPE_NAMES = {
    "GenZ": [
        "Tech-Savvy Student", "First-Time Worker", "Crypto Enthusiast", 
        "Social Media Native", "Gaming Streamer", "Gig Economy Hustler",
        "Digital Nomad Aspirant", "Influencer Wannabe", "Anxious Graduate",
        "Sustainability Advocate", "Side Hustle King", "Meme Account Runner",
        "Part-Time Trader", "TikTok Finance Fan", "New Investor"
    ],
    "Millennial": [
        "Young Professional", "First-Time Parent", "Startup Founder",
        "Freelancer", "Career Changer", "Remote Worker", "Home Buyer",
        "Financial Planner", "Tech Industry Veteran", "Anxious Saver",
        "Travel Enthusiast", "Side Project Builder", "MBA Graduate",
        "Corporate Climber", "Work-Life Balance Seeker", "Debt Reducer"
    ],
    "SME_Owner": [
        "Restaurant Owner", "E-commerce Seller", "Contractor", 
        "Boutique Retailer", "Consulting Firm Founder", "Import/Export Trader",
        "Tech Startup CEO", "Family Business Manager", "Franchise Owner",
        "Real Estate Developer", "Service Provider", "Manufacturing SME",
        "Digital Agency Owner", "Healthcare Practice Owner", "F&B Entrepreneur"
    ],
    "HNI": [
        "Real Estate Investor", "Corporate Executive", "Retired Professional",
        "Family Office Manager", "Angel Investor", "Serial Entrepreneur",
        "Private Banker Client", "Wealth Preserver", "Legacy Planner",
        "Luxury Consumer", "International Investor", "Business Mogul",
        "Portfolio Diversifier", "Tax Optimizer", "Multi-Generational Wealth"
    ],
    "Vulnerable": [
        "Financially Distressed Individual", "Elderly Tech-Averse User",
        "Expatriate New to UAE", "Hostile Burned Customer", "First-Time Migrant Worker",
        "Recently Divorced Single Parent", "Medical Emergency Victim",
        "Job Loss Survivor", "Debt Spiral Victim", "Scam Survivor",
        "Fixed Income Retiree", "Language Barrier Client", "Digital Literacy Gap",
        "Overextended Borrower", "Trust-Eroded Customer"
    ]
}


def generate_archetype(segment: str, distributions: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Generate a single agent archetype."""
    segment_config = distributions["demographic_segments"][segment]
    
    # Select archetype name
    names = ARCHETYPE_NAMES[segment]
    archetype_name = names[index % len(names)]
    
    # Add variation to name if we've cycled through
    if index >= len(names):
        variation = index // len(names) + 1
        archetype_name = f"{archetype_name} Type {variation}"
    
    # Generate stats with clamping
    financial_literacy = int(clamp(
        sample_from_distribution(segment_config["financial_literacy"]), 1, 10
    ))
    brand_loyalty = int(clamp(
        sample_from_distribution(segment_config["brand_loyalty"]), 0, 100
    ))
    skepticism_score = int(clamp(
        sample_from_distribution(segment_config["skepticism_score"]), 1, 10
    ))
    network_influence = int(clamp(
        sample_from_distribution(segment_config["network_influence"]), 1, 100
    ))
    activity_frequency = round(clamp(
        sample_from_distribution(segment_config["activity_frequency"]), 0.1, 10
    ), 2)
    
    # Select platform and values
    preferred_platform = select_platform(segment_config["preferred_platforms"])
    core_values = select_core_values(segment, distributions)
    
    return {
        "agent_id": str(uuid.uuid4()),
        "archetype_name": archetype_name,
        "demographic_segment": segment,
        "financial_literacy": financial_literacy,
        "brand_loyalty": brand_loyalty,
        "skepticism_score": skepticism_score,
        "network_influence": network_influence,
        "activity_frequency": activity_frequency,
        "preferred_platform": preferred_platform,
        "core_values": json.dumps(core_values)  # Store as JSON string for CSV
    }


def generate_all_archetypes(target_count: int = 120) -> List[Dict[str, Any]]:
    """Generate all agent archetypes based on distribution weights."""
    distributions = load_distributions()
    archetypes = []
    
    segments = distributions["demographic_segments"]
    
    for segment_name, segment_config in segments.items():
        # Calculate count for this segment based on weight
        segment_count = int(target_count * segment_config["distribution_weight"])
        # Ensure at least 10 per segment
        segment_count = max(10, segment_count)
        
        print(f"Generating {segment_count} archetypes for {segment_name}...")
        
        for i in range(segment_count):
            archetype = generate_archetype(segment_name, distributions, i)
            archetypes.append(archetype)
    
    return archetypes


def save_archetypes_csv(archetypes: List[Dict[str, Any]], output_path: Path):
    """Save archetypes to CSV file."""
    if not archetypes:
        print("No archetypes to save!")
        return
    
    fieldnames = list(archetypes[0].keys())
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(archetypes)
    
    print(f"✓ Saved {len(archetypes)} archetypes to {output_path}")


def main():
    """Main entry point for archetype generation."""
    print("=" * 60)
    print("Agent Archetype Generator")
    print("=" * 60)
    
    # Generate archetypes
    archetypes = generate_all_archetypes(target_count=120)
    
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
    return archetypes


if __name__ == "__main__":
    main()
