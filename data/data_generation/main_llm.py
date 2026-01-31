"""
Main orchestration script for LLM-enhanced data generation
Uses GPT-4o for high-quality synthetic data
"""

import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generators.llm_client import test_connection
from generators.llm_archetype_generator import main as generate_archetypes_llm
from generators.llm_social_generator import main as generate_social_signals_llm
from generators.knowledge_base_generator import main as generate_knowledge_base
from generators.scenario_generator import main as generate_scenarios
from validators.schema_validator import run_all_validations


def print_banner(text: str):
    """Print a banner with text."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def main(
    archetype_count: int = 150,
    signal_count: int = 5000
):
    """Main orchestration function for LLM-enhanced generation."""
    start_time = time.time()
    
    print_banner("🚀 LLM-ENHANCED DATA GENERATOR (GPT-4o)")
    
    print("This script uses OpenAI GPT-4o to generate high-quality synthetic data.")
    print("Expected output:")
    print(f"  • agent_archetypes.csv (~{archetype_count} rich personas with backstories)")
    print(f"  • bank_knowledge_base.csv (~77 facts)")
    print(f"  • social_signals_stream.csv (~{signal_count} unique LLM-generated posts)")
    print(f"  • scenario_definitions.json (~12 scenarios)")
    print()
    
    # Test OpenAI connection
    print_banner("🔌 Step 0/5: Testing OpenAI Connection")
    if not test_connection():
        print("❌ Failed to connect to OpenAI. Check your API key in .env")
        return None
    
    # Step 1: Generate Agent Archetypes with LLM
    print_banner("📊 Step 1/5: Generating Agent Archetypes (LLM)")
    archetypes = generate_archetypes_llm(target_count=archetype_count)
    
    # Step 2: Generate Knowledge Base (template-based, no LLM needed)
    print_banner("📚 Step 2/5: Generating Bank Knowledge Base")
    knowledge = generate_knowledge_base()
    
    # Step 3: Generate Social Signals with LLM
    print_banner("📱 Step 3/5: Generating Social Signals (LLM)")
    signals = generate_social_signals_llm(target_count=signal_count)
    
    # Step 4: Generate Scenarios (template-based)
    print_banner("🎭 Step 4/5: Generating Scenario Definitions")
    scenarios = generate_scenarios()
    
    # Step 5: Validate All Datasets
    print_banner("✅ Step 5/5: Validating All Datasets")
    validation_passed = run_all_validations()
    
    # Calculate time
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Final Summary
    print_banner("📋 GENERATION COMPLETE")
    
    print("Generated Datasets:")
    print(f"  ✓ {len(archetypes)} agent archetypes (with LLM-generated backstories)")
    print(f"  ✓ {len(knowledge)} knowledge base entries")
    print(f"  ✓ {len(signals)} social signals (all unique, LLM-generated)")
    print(f"  ✓ {len(scenarios)} scenario definitions")
    
    print()
    datasets_dir = Path(__file__).parent.parent / "datasets"
    print(f"Output location: {datasets_dir}")
    
    print(f"\n⏱️  Total time: {int(hours)}h {int(minutes)}m {int(seconds)}s")
    
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
        "validation_passed": validation_passed,
        "elapsed_time": elapsed_time
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-Enhanced Data Generator")
    parser.add_argument("--archetypes", type=int, default=150, help="Number of archetypes to generate")
    parser.add_argument("--signals", type=int, default=5000, help="Number of social signals to generate")
    parser.add_argument("--test", action="store_true", help="Run small test batch (50 archetypes, 100 signals)")
    
    args = parser.parse_args()
    
    if args.test:
        main(archetype_count=50, signal_count=100)
    else:
        main(archetype_count=args.archetypes, signal_count=args.signals)
