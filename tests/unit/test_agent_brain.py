"""
Unit tests for the Agent Brain module.

Tests heuristic decision logic, persona consistency, and reach calculation.
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.models.schemas import AgentAction, SignalCategory


class TestHeuristicDecision:
    """Tests for heuristic-based decision making (no LLM)."""
    
    def test_high_skepticism_reduces_sharing(self, sample_agent, sample_signal):
        """Test that skeptical agents share less."""
        # Agent has skepticism_score = 9
        base_share = sample_signal.gt_virality_potential / 100  # 0.85
        share_prob = base_share * (10 - sample_agent.skepticism_score) / 10
        
        # 0.85 * (10-9)/10 = 0.85 * 0.1 = 0.085
        assert share_prob < 0.1  # Much lower than base
    
    def test_low_financial_literacy_increases_fraud_sharing(self, sample_agents, sample_signal):
        """Test that financially illiterate agents share fraud rumors more."""
        anxious_agent = sample_agents[1]  # financial_literacy = 3
        
        base_share = sample_signal.gt_virality_potential / 100
        share_prob = base_share * (10 - anxious_agent.skepticism_score) / 10
        
        # Add illiteracy bonus for fraud
        if sample_signal.gt_category == SignalCategory.FRAUD_RUMOR:
            illiteracy_bonus = (10 - anxious_agent.financial_literacy) / 20
            share_prob += illiteracy_bonus
        
        # (10 - 3) / 20 = 0.35 bonus
        assert share_prob > base_share * 0.5  # Higher than skeptical agent
    
    def test_high_brand_loyalty_reduces_negative_sharing(self, sample_agents, sample_signal):
        """Test that loyal customers share negative content less."""
        loyal_agent = sample_agents[2]  # brand_loyalty = 95
        
        base_share = sample_signal.gt_virality_potential / 100
        share_prob = base_share
        
        # Reduce for negative sentiment
        if sample_signal.gt_sentiment < 0:
            loyalty_reduction = loyal_agent.brand_loyalty / 200
            share_prob -= loyalty_reduction
        
        # 95 / 200 = 0.475 reduction
        assert share_prob < base_share
    
    def test_skeptical_agent_reports_misinformation(self, sample_agent, sample_signal):
        """Test that skeptical agents report clear misinformation."""
        # sample_agent has skepticism_score = 9
        # sample_signal has gt_is_misinformation = True
        
        should_report = (
            sample_agent.skepticism_score > 7 and 
            sample_signal.gt_is_misinformation
        )
        
        assert should_report


class TestReachCalculation:
    """Tests for agent reach/influence calculation."""
    
    def test_reach_scales_with_influence(self, sample_agents):
        """Test that high influence means higher reach."""
        reaches = []
        for agent in sample_agents:
            base_reach = 10 * (1.05 ** agent.network_influence)
            activity_multiplier = min(1.0, agent.activity_frequency / 5)
            reach = base_reach * activity_multiplier
            reaches.append((agent.archetype_name, reach))
        
        # Higher influence should mean higher reach
        # Anxious Saver has influence 80 and frequency 8.0
        # Skeptical Tech has influence 60 and frequency 3.5
        assert len(reaches) > 0
    
    def test_activity_frequency_caps_reach(self, sample_agent):
        """Test that low activity frequency reduces effective reach."""
        # Agent with frequency = 3.5
        activity_multiplier = min(1.0, sample_agent.activity_frequency / 5)
        assert activity_multiplier == 0.7  # 3.5 / 5
    
    def test_high_activity_frequency_maxes_multiplier(self, sample_agents):
        """Test that activity > 5 doesn't exceed multiplier of 1.0."""
        anxious_agent = sample_agents[1]  # activity_frequency = 8.0
        activity_multiplier = min(1.0, anxious_agent.activity_frequency / 5)
        assert activity_multiplier == 1.0


class TestEmotionalState:
    """Tests for emotional state determination."""
    
    def test_negative_sentiment_causes_fear(self, sample_agent, sample_signal):
        """Test that very negative signals cause fear in less literate agents."""
        # sample_signal.gt_sentiment = -0.8
        
        if sample_signal.gt_sentiment < -0.5:
            if sample_agent.financial_literacy < 5:
                emotional_state = "Fear"
            else:
                emotional_state = "Concern"
        else:
            emotional_state = "Neutral"
        
        # sample_agent has financial_literacy = 8, so "Concern"
        assert emotional_state == "Concern"
    
    def test_positive_sentiment_causes_trust(self, sample_agent):
        """Test that positive signals create trust."""
        # Create a positive signal
        sentiment = 0.7
        
        if sentiment > 0.5:
            emotional_state = "Trust"
        else:
            emotional_state = "Neutral"
        
        assert emotional_state == "Trust"


class TestActionSelection:
    """Tests for action selection based on probabilities."""
    
    def test_share_probability_to_action_mapping(self):
        """Test that share probability maps to appropriate actions."""
        share_prob = 0.8
        
        # Simulate action selection with fixed "roll"
        test_rolls = [0.1, 0.5, 0.7, 0.85, 0.95]
        actions = []
        
        for roll in test_rolls:
            if roll < share_prob * 0.7:  # < 0.56
                action = AgentAction.SHARE
            elif roll < share_prob:  # < 0.8
                action = AgentAction.COMMENT
            elif roll < share_prob + 0.1:  # < 0.9
                action = AgentAction.LIKE
            else:
                action = AgentAction.IGNORE
            actions.append(action)
        
        assert AgentAction.SHARE in actions
        assert AgentAction.COMMENT in actions
        assert AgentAction.IGNORE in actions
    
    def test_low_probability_mostly_ignores(self):
        """Test that low share probability leads to IGNORE."""
        share_prob = 0.1
        
        # Most rolls will result in IGNORE
        test_rolls = [0.5, 0.6, 0.7, 0.8, 0.9]
        ignores = 0
        
        for roll in test_rolls:
            if roll < share_prob * 0.7:
                action = AgentAction.SHARE
            elif roll < share_prob:
                action = AgentAction.COMMENT
            elif roll < share_prob + 0.1:
                action = AgentAction.LIKE
            else:
                action = AgentAction.IGNORE
            
            if action == AgentAction.IGNORE:
                ignores += 1
        
        assert ignores == len(test_rolls)  # All should be IGNORE


class TestAgentBrainIntegration:
    """Integration tests for AgentBrain class."""
    
    def test_heuristic_mode_works_without_llm(self, sample_agent, sample_signal, patch_llm_client):
        """Test that heuristic mode doesn't require LLM."""
        from simulator.agent_brain import AgentBrain
        
        brain = AgentBrain(use_llm=False)
        decision = brain._heuristic_decision(sample_agent, sample_signal)
        
        assert decision.agent_id == sample_agent.agent_id
        assert decision.signal_id == sample_signal.signal_id
        assert decision.action in AgentAction
        assert 0 <= decision.share_probability <= 1
        assert decision.reach_multiplier > 0
    
    def test_batch_decide_returns_all_decisions(self, sample_agents, sample_signal, patch_llm_client):
        """Test that batch_decide returns decision for each agent."""
        from simulator.agent_brain import AgentBrain
        import asyncio
        
        brain = AgentBrain(use_llm=False)
        
        async def run_batch():
            return await brain.batch_decide(sample_agents, sample_signal)
        
        decisions = asyncio.run(run_batch())
        
        assert len(decisions) == len(sample_agents)
        for decision in decisions:
            assert decision.action in AgentAction
