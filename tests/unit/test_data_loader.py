"""
Unit tests for the Data Loader module.

Tests CSV parsing, JSON loading, and singleton behavior.
"""

import pytest
from datetime import datetime
from pathlib import Path
from uuid import UUID

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestListFieldParsing:
    """Tests for parsing list fields from CSV strings."""
    
    def test_parses_python_list_syntax(self):
        """Test parsing Python list syntax."""
        from backend.data.data_loader import DataLoader
        
        loader = DataLoader()
        result = loader._parse_list_field("['Security', 'Trust', 'Speed']")
        
        assert result == ["Security", "Trust", "Speed"]
    
    def test_parses_empty_list(self):
        """Test parsing empty list."""
        from backend.data.data_loader import DataLoader
        
        loader = DataLoader()
        result = loader._parse_list_field("[]")
        
        assert result == []
    
    def test_handles_nan_values(self):
        """Test handling NaN/None values."""
        from backend.data.data_loader import DataLoader
        import pandas as pd
        
        loader = DataLoader()
        result = loader._parse_list_field(pd.NA)
        
        assert result == []
    
    def test_parses_comma_separated_fallback(self):
        """Test fallback to comma-separated parsing."""
        from backend.data.data_loader import DataLoader
        
        loader = DataLoader()
        # Invalid Python syntax, should fall back to CSV
        result = loader._parse_list_field("one, two, three")
        
        assert result == ["one", "two", "three"]


class TestScenarioLoading:
    """Tests for scenario JSON loading."""
    
    @pytest.fixture
    def data_loader(self):
        from backend.data.data_loader import DataLoader
        # Reset singleton for clean test
        DataLoader._instance = None
        DataLoader._initialized = False
        return DataLoader()
    
    def test_load_scenarios_returns_list(self, data_loader):
        """Test that scenarios are loaded as list."""
        scenarios = data_loader.load_scenarios()
        
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
    
    def test_scenario_has_required_fields(self, data_loader):
        """Test that scenarios have all required fields."""
        scenarios = data_loader.load_scenarios()
        scenario = scenarios[0]
        
        assert hasattr(scenario, "scenario_id")
        assert hasattr(scenario, "scenario_name")
        assert hasattr(scenario, "severity_level")
        assert hasattr(scenario, "target_segment")
    
    def test_get_scenario_by_id(self, data_loader):
        """Test finding scenario by ID."""
        scenarios = data_loader.load_scenarios()
        target_id = scenarios[0].scenario_id
        
        found = data_loader.get_scenario_by_id(target_id)
        
        assert found is not None
        assert found.scenario_id == target_id
    
    def test_get_scenario_by_name(self, data_loader):
        """Test finding scenario by name."""
        scenarios = data_loader.load_scenarios()
        target_name = scenarios[0].scenario_name
        
        # Use partial name match
        partial_name = target_name.split()[0]  # First word
        found = data_loader.get_scenario_by_name(partial_name)
        
        assert found is not None


class TestSignalLoading:
    """Tests for signal CSV loading."""
    
    @pytest.fixture
    def data_loader(self):
        from backend.data.data_loader import DataLoader
        DataLoader._instance = None
        DataLoader._initialized = False
        return DataLoader()
    
    def test_load_signals_with_limit(self, data_loader):
        """Test loading limited number of signals."""
        signals = data_loader.load_signals(limit=10)
        
        assert len(signals) <= 10
    
    def test_signal_has_ground_truth(self, data_loader):
        """Test that signals have ground truth fields."""
        signals = data_loader.load_signals(limit=5)
        signal = signals[0]
        
        assert hasattr(signal, "gt_category")
        assert hasattr(signal, "gt_sentiment")
        assert hasattr(signal, "gt_is_misinformation")
        assert hasattr(signal, "gt_virality_potential")
    
    def test_signal_timestamp_parsed(self, data_loader):
        """Test that timestamps are parsed as datetime."""
        signals = data_loader.load_signals(limit=1)
        signal = signals[0]
        
        assert isinstance(signal.timestamp, datetime)


class TestAgentLoading:
    """Tests for agent archetype CSV loading."""
    
    @pytest.fixture
    def data_loader(self):
        from backend.data.data_loader import DataLoader
        DataLoader._instance = None
        DataLoader._initialized = False
        return DataLoader()
    
    def test_load_agents_returns_list(self, data_loader):
        """Test that agents are loaded as list."""
        agents = data_loader.load_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
    
    def test_agent_has_personality_traits(self, data_loader):
        """Test that agents have personality traits."""
        agents = data_loader.load_agents()
        agent = agents[0]
        
        assert hasattr(agent, "skepticism_score")
        assert hasattr(agent, "brand_loyalty")
        assert hasattr(agent, "financial_literacy")
        assert hasattr(agent, "network_influence")
    
    def test_agent_skepticism_in_range(self, data_loader):
        """Test that skepticism is in valid range 1-10."""
        agents = data_loader.load_agents()
        
        for agent in agents:
            assert 1 <= agent.skepticism_score <= 10


class TestKnowledgeBaseLoading:
    """Tests for knowledge base CSV loading."""
    
    @pytest.fixture
    def data_loader(self):
        from backend.data.data_loader import DataLoader
        DataLoader._instance = None
        DataLoader._initialized = False
        return DataLoader()
    
    def test_load_knowledge_base(self, data_loader):
        """Test that knowledge base loads."""
        facts = data_loader.load_knowledge_base()
        
        assert isinstance(facts, list)
        assert len(facts) > 0
    
    def test_fact_has_statement(self, data_loader):
        """Test that facts have statements."""
        facts = data_loader.load_knowledge_base()
        fact = facts[0]
        
        assert hasattr(fact, "fact_statement")
        assert len(fact.fact_statement) > 10


class TestSingletonBehavior:
    """Tests for singleton pattern."""
    
    def test_same_instance_returned(self):
        """Test that same instance is returned on multiple calls."""
        from backend.data.data_loader import DataLoader, get_data_loader
        
        # Reset singleton
        DataLoader._instance = None
        DataLoader._initialized = False
        
        loader1 = get_data_loader()
        loader2 = get_data_loader()
        
        assert loader1 is loader2
    
    def test_caches_loaded_data(self):
        """Test that loaded data is cached."""
        from backend.data.data_loader import DataLoader
        
        DataLoader._instance = None
        DataLoader._initialized = False
        loader = DataLoader()
        
        # Load twice
        signals1 = loader.load_signals(limit=10)
        loader._signals = signals1  # Simulate caching
        signals2 = loader.load_signals()  # Should use cache
        
        # Cache should be used
        assert signals1 is signals2
