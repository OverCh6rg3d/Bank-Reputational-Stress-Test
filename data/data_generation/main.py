"""
Main orchestration script for data generation
Runs all generators in sequence and validates output
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generators.archetype_generator import main as generate_archetypes
from generators.knowledge_base_generator import main as generate_knowledge_base
from generators.social_signal_generator import main as generate_social_signals
from generators.scenario_generator import main as generate_scenarios
from validators.schema_validator import run_all_validations


def print_banner(text: str):
    """Print a banner with text."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def main():
    """Main orchestration function."""
    print_banner("🚀 REPUTATIONAL STRESS-TEST SIMULATOR - DATA GENERATOR")
    
    print("This script will generate all synthetic datasets for the project.")
    print("Expected output:")
    print("  • agent_archetypes.csv (~120 personas)")
    print("  • bank_knowledge_base.csv (~75 facts)")
    print("  • social_signals_stream.csv (~5000 posts)")
    print("  • scenario_definitions.json (~12 scenarios)")
    print()
    
    # Step 1: Generate Agent Archetypes (dependencies: none)
    print_banner("📊 Step 1/5: Generating Agent Archetypes")
    archetypes = generate_archetypes()
    
    # Step 2: Generate Knowledge Base (dependencies: none)
    print_banner("📚 Step 2/5: Generating Bank Knowledge Base")
    knowledge = generate_knowledge_base()
    
    # Step 3: Generate Social Signals (dependencies: archetypes)
    print_banner("📱 Step 3/5: Generating Social Signals Stream")
    signals = generate_social_signals()
    
    # Step 4: Generate Scenarios (dependencies: none)
    print_banner("🎭 Step 4/5: Generating Scenario Definitions")
    scenarios = generate_scenarios()
    
    # Step 5: Validate All Datasets
    print_banner("✅ Step 5/5: Validating All Datasets")
    validation_passed = run_all_validations()
    
    # Final Summary
    print_banner("📋 GENERATION COMPLETE")
    
    print("Generated Datasets:")
    print(f"  ✓ {len(archetypes)} agent archetypes")
    print(f"  ✓ {len(knowledge)} knowledge base entries")
    print(f"  ✓ {len(signals)} social signals")
    print(f"  ✓ {len(scenarios)} scenario definitions")
    
    print()
    datasets_dir = Path(__file__).parent.parent / "datasets"
    print(f"Output location: {datasets_dir}")
    
    print()
    if validation_passed:
        print("🎉 All validations passed! Datasets are ready to use.")
    else:
        print("⚠️  Some validations had warnings. Review output above.")
    
    return {
        "archetypes": len(archetypes),
        "knowledge": len(knowledge),
        "signals": len(signals),
        "scenarios": len(scenarios),
        "validation_passed": validation_passed
    }


if __name__ == "__main__":
    main()
