"""
Schema Validator
Validates generated datasets against the expected schema
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import sys


# Expected schemas based on dataset_schema.md
SCHEMAS = {
    "agent_archetypes": {
        "required_fields": [
            "agent_id", "archetype_name", "demographic_segment",
            "financial_literacy", "brand_loyalty", "skepticism_score",
            "network_influence", "activity_frequency", "preferred_platform", "core_values"
        ],
        "field_types": {
            "agent_id": str,
            "archetype_name": str,
            "demographic_segment": str,
            "financial_literacy": int,
            "brand_loyalty": int,
            "skepticism_score": int,
            "network_influence": int,
            "activity_frequency": float,
            "preferred_platform": str,
            "core_values": str  # JSON string
        },
        "valid_enums": {
            "demographic_segment": ["GenZ", "Millennial", "SME_Owner", "HNI", "Vulnerable"],
            "preferred_platform": ["X_Style", "Reddit_Style", "News_Portal", "LinkedIn_Style"]
        },
        "value_ranges": {
            "financial_literacy": (1, 10),
            "brand_loyalty": (0, 100),
            "skepticism_score": (1, 10),
            "network_influence": (1, 100),
            "activity_frequency": (0.1, 10.0)
        }
    },
    "bank_knowledge_base": {
        "required_fields": [
            "kb_id", "topic_area", "fact_statement", "public_url",
            "last_updated", "keywords"
        ],
        "field_types": {
            "kb_id": str,
            "topic_area": str,
            "fact_statement": str,
            "public_url": str,
            "last_updated": str,  # ISO datetime
            "keywords": str  # JSON string
        },
        "valid_enums": {
            "topic_area": ["Security", "Fees", "App_Status", "Products", "Compliance"]
        }
    },
    "social_signals_stream": {
        "required_fields": [
            "signal_id", "timestamp", "platform_source", "author_id",
            "content_text", "parent_id", "thread_id", "media_type",
            "language", "hashtags", "mentions", "gt_category",
            "gt_sentiment", "gt_is_misinformation", "gt_virality_potential"
        ],
        "field_types": {
            "signal_id": str,
            "timestamp": str,
            "platform_source": str,
            "author_id": str,  # Can be empty
            "content_text": str,
            "parent_id": str,  # Can be empty
            "thread_id": str,
            "media_type": str,
            "language": str,
            "hashtags": str,  # JSON string
            "mentions": str,  # JSON string
            "gt_category": str,
            "gt_sentiment": float,
            "gt_is_misinformation": bool,
            "gt_virality_potential": int
        },
        "valid_enums": {
            "platform_source": ["X_Style", "Reddit_Style", "News_Portal", "LinkedIn_Style"],
            "media_type": ["None", "Image", "Video_Link"],
            "language": ["en", "ar", "mix"],
            "gt_category": ["Fraud_Rumor", "Service_Outage", "Competitor_News", "Positive_Neutral", "Irrelevant"]
        },
        "value_ranges": {
            "gt_sentiment": (-1.0, 1.0),
            "gt_virality_potential": (0, 100)
        }
    },
    "detected_incidents": {
        "required_fields": [
            "incident_id", "related_scenario_id", "detected_severity", "status",
            "confidence_score", "ai_analysis", "proposed_response", "human_action"
        ],
        "field_types": {
            "incident_id": str,
            "related_scenario_id": str,
            "detected_severity": str,
            "status": str,
            "confidence_score": float,
            "ai_analysis": str,
            "proposed_response": str,
            "human_action": str
        },
        "valid_enums": {
            "detected_severity": ["Low", "Medium", "High", "Critical"],
            "status": ["Active", "Mitigated", "Resolved", "False_Positive"],
            "human_action": ["Pending_Review", "Approved", "Rejected", "Modified"]
        },
        "value_ranges": {
            "confidence_score": (0.0, 1.0)
        }
    }
}


class ValidationResult:
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.total_rows = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed = True
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.passed = False
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def summary(self) -> str:
        status = "✓ PASSED" if self.passed else "✗ FAILED"
        lines = [
            f"\n{'='*60}",
            f"Validation: {self.dataset_name}",
            f"{'='*60}",
            f"Status: {status}",
            f"Total Rows: {self.total_rows}",
            f"Errors: {len(self.errors)}",
            f"Warnings: {len(self.warnings)}"
        ]
        
        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors[:10]:  # Show first 10
                lines.append(f"  ✗ {err}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more errors")
        
        if self.warnings:
            lines.append("\nWarnings:")
            for warn in self.warnings[:5]:  # Show first 5
                lines.append(f"  ⚠ {warn}")
            if len(self.warnings) > 5:
                lines.append(f"  ... and {len(self.warnings) - 5} more warnings")
        
        return "\n".join(lines)


def parse_value(value: str, expected_type: type, field_name: str) -> Tuple[Any, str]:
    """Parse a string value to the expected type."""
    try:
        if expected_type == int:
            return int(float(value)), None
        elif expected_type == float:
            return float(value), None
        elif expected_type == bool:
            return value.lower() in ("true", "1", "yes"), None
        elif expected_type == str:
            return value, None
        else:
            return value, None
    except ValueError as e:
        return None, f"Cannot parse '{value}' as {expected_type.__name__} for field '{field_name}'"


def validate_csv(file_path: Path, schema_name: str) -> ValidationResult:
    """Validate a CSV file against its schema."""
    result = ValidationResult(schema_name)
    schema = SCHEMAS.get(schema_name)
    
    if not schema:
        result.add_error(f"No schema defined for '{schema_name}'")
        return result
    
    if not file_path.exists():
        result.add_error(f"File not found: {file_path}")
        return result
    
    required_fields = schema["required_fields"]
    field_types = schema["field_types"]
    valid_enums = schema.get("valid_enums", {})
    value_ranges = schema.get("value_ranges", {})
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        
        # Check required fields
        missing = set(required_fields) - set(headers)
        if missing:
            result.add_error(f"Missing required fields: {missing}")
        
        # Check each row
        seen_ids = set()
        for row_num, row in enumerate(reader, start=2):
            result.total_rows += 1
            
            # Check ID uniqueness
            id_field = None
            for field in ["agent_id", "kb_id", "signal_id"]:
                if field in row:
                    id_field = field
                    break
            
            if id_field and row.get(id_field):
                if row[id_field] in seen_ids:
                    result.add_error(f"Row {row_num}: Duplicate {id_field}: {row[id_field]}")
                seen_ids.add(row[id_field])
            
            # Validate each field
            for field, expected_type in field_types.items():
                if field not in row:
                    continue
                
                value = row[field]
                
                # Allow empty for optional fields
                if value == "" and field in ["author_id", "parent_id"]:
                    continue
                
                # Type check
                parsed, error = parse_value(value, expected_type, field)
                if error:
                    result.add_error(f"Row {row_num}: {error}")
                    continue
                
                # Enum check
                if field in valid_enums:
                    if parsed not in valid_enums[field]:
                        result.add_error(
                            f"Row {row_num}: Invalid value '{parsed}' for {field}. "
                            f"Expected one of: {valid_enums[field]}"
                        )
                
                # Range check
                if field in value_ranges:
                    min_val, max_val = value_ranges[field]
                    if not (min_val <= parsed <= max_val):
                        result.add_warning(
                            f"Row {row_num}: Value {parsed} for {field} outside expected range [{min_val}, {max_val}]"
                        )
                
                # JSON validation for list fields
                if field in ["core_values", "keywords", "hashtags", "mentions"]:
                    try:
                        json.loads(value)
                    except json.JSONDecodeError:
                        result.add_error(f"Row {row_num}: Invalid JSON in {field}: {value[:50]}...")
    
    return result


def validate_scenarios_json(file_path: Path) -> ValidationResult:
    """Validate scenarios JSON file."""
    result = ValidationResult("scenario_definitions")
    
    if not file_path.exists():
        result.add_error(f"File not found: {file_path}")
        return result
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            scenarios = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON: {e}")
        return result
    
    if not isinstance(scenarios, list):
        result.add_error("Scenarios should be a JSON array")
        return result
    
    result.total_rows = len(scenarios)
    
    required_fields = [
        "scenario_id", "scenario_name", "description", "trigger_category",
        "target_segment", "simulation_duration_hours", "severity_level"
    ]
    
    for i, scenario in enumerate(scenarios):
        for field in required_fields:
            if field not in scenario:
                result.add_error(f"Scenario {i}: Missing required field '{field}'")
    
    return result


def validate_referential_integrity(datasets_dir: Path) -> ValidationResult:
    """Check referential integrity between datasets."""
    result = ValidationResult("referential_integrity")
    
    # Load archetypes
    archetype_ids = set()
    archetypes_path = datasets_dir / "agent_archetypes.csv"
    if archetypes_path.exists():
        with open(archetypes_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                archetype_ids.add(row.get("agent_id", ""))
    
    # Check social signals reference valid archetypes
    signals_path = datasets_dir / "social_signals_stream.csv"
    if signals_path.exists():
        with open(signals_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            invalid_refs = 0
            for row in reader:
                result.total_rows += 1
                author_id = row.get("author_id", "")
                if author_id and author_id not in archetype_ids:
                    invalid_refs += 1
            
            if invalid_refs > 0:
                result.add_warning(f"{invalid_refs} signals reference non-existent author_ids")
    
    # Check thread consistency
    if signals_path.exists():
        with open(signals_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            threads = {}
            for row in reader:
                thread_id = row.get("thread_id", "")
                signal_id = row.get("signal_id", "")
                if thread_id:
                    if thread_id not in threads:
                        threads[thread_id] = []
                    threads[thread_id].append(signal_id)
            
            orphaned = 0
            for thread_id, signals in threads.items():
                if thread_id not in signals:
                    orphaned += 1
            
            if orphaned > 0:
                result.add_warning(f"{orphaned} threads have missing root signals")
    
    result.passed = len(result.errors) == 0
    return result


def run_all_validations(datasets_dir: Path = None) -> bool:
    """Run all validations and print results."""
    if datasets_dir is None:
        datasets_dir = Path(__file__).parent.parent.parent / "datasets"
    
    print("=" * 60)
    print("Dataset Schema Validator")
    print("=" * 60)
    print(f"Datasets directory: {datasets_dir}")
    
    all_passed = True
    
    # Validate each CSV
    csv_files = [
        ("agent_archetypes.csv", "agent_archetypes"),
        ("bank_knowledge_base.csv", "bank_knowledge_base"),
        ("social_signals_stream.csv", "social_signals_stream"),
        ("detected_incidents.csv", "detected_incidents")
    ]
    
    for filename, schema_name in csv_files:
        file_path = datasets_dir / filename
        result = validate_csv(file_path, schema_name)
        print(result.summary())
        all_passed = all_passed and result.passed
    
    # Validate scenarios JSON
    scenarios_path = datasets_dir / "scenario_definitions.json"
    result = validate_scenarios_json(scenarios_path)
    print(result.summary())
    all_passed = all_passed and result.passed
    
    # Validate referential integrity
    result = validate_referential_integrity(datasets_dir)
    print(result.summary())
    all_passed = all_passed and result.passed
    
    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
    else:
        print("✗ SOME VALIDATIONS FAILED")
    print("=" * 60)
    
    return all_passed


def main():
    """Main entry point."""
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_all_validations()
        else:
            datasets_dir = Path(sys.argv[1])
            run_all_validations(datasets_dir)
    else:
        run_all_validations()


if __name__ == "__main__":
    main()
