"""
Shared pytest fixtures for the Reputational Stress-Test Simulator.

Provides mock objects and sample data for testing without LLM calls.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from backend.models.schemas import (
    AgentAction,
    AgentArchetype,
    PlatformSource,
    Scenario,
    SeverityLevel,
    SignalCategory,
    SocialSignal,
)


# =============================================================================
# Mock LLM Client
# =============================================================================

class MockLLMClient:
    """Mock LLM client that returns deterministic responses."""
    
    def __init__(self):
        self.model = "mock-model"
        self.temperature = 0.7
        self.call_count = 0
    
    def complete(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return "This is a mock LLM response."
    
    async def async_complete(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return "This is a mock async LLM response."
    
    def complete_json(self, prompt: str, **kwargs) -> dict:
        self.call_count += 1
        return {
            "summary": "Mock summary of the signals",
            "themes": ["security", "fraud", "trust"],
            "confidence": 0.85,
            "likely_cause": "Genuine Concern",
        }
    
    async def async_complete_json(self, prompt: str, **kwargs) -> dict:
        self.call_count += 1
        return {
            "action": "IGNORE",
            "reasoning": "Mock reasoning from LLM",
            "emotional_state": "Neutral",
            "share_probability": 0.3,
        }


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Provide a mock LLM client."""
    return MockLLMClient()


@pytest.fixture
def patch_llm_client(mock_llm_client: MockLLMClient):
    """Patch the global LLM client singleton."""
    with patch("backend.core.llm_client.get_llm_client", return_value=mock_llm_client):
        with patch("backend.core.llm_client._llm_client", mock_llm_client):
            yield mock_llm_client


# =============================================================================
# Mock Embedder
# =============================================================================

class MockEmbedder:
    """Mock embedder that returns zero vectors."""
    
    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        # Return 384-dim zero vectors (typical embedding size)
        return [[0.0] * 384 for _ in texts]
    
    def encode(self, texts):
        return self.embed(texts)


@pytest.fixture
def mock_embedder() -> MockEmbedder:
    """Provide a mock embedder."""
    return MockEmbedder()


@pytest.fixture
def patch_embedder(mock_embedder: MockEmbedder):
    """Patch the embedder singleton."""
    with patch("backend.core.embedder.get_embedder", return_value=mock_embedder):
        yield mock_embedder


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_signal() -> SocialSignal:
    """Create a sample social signal for testing."""
    return SocialSignal(
        signal_id=uuid4(),
        timestamp=datetime.now(),
        platform_source=PlatformSource.X_STYLE,
        author_id=uuid4(),
        content_text="OMG just heard Mashreq Bank got hacked! My account might be compromised! #MashreqHack",
        parent_id=None,
        thread_id=uuid4(),
        media_type="None",
        language="en",
        hashtags=["MashreqHack"],
        mentions=[],
        gt_category=SignalCategory.FRAUD_RUMOR,
        gt_sentiment=-0.8,
        gt_is_misinformation=True,
        gt_virality_potential=85,
    )


@pytest.fixture
def sample_signals(sample_signal: SocialSignal) -> list[SocialSignal]:
    """Create a list of sample signals for clustering tests."""
    signals = [sample_signal]
    
    # Add more signals for clustering
    for i in range(9):
        signals.append(SocialSignal(
            signal_id=uuid4(),
            timestamp=datetime.now(),
            platform_source=PlatformSource.X_STYLE,
            author_id=uuid4(),
            content_text=f"Test signal {i}: Mashreq security concern test content",
            parent_id=None,
            thread_id=uuid4(),
            media_type="None",
            language="en",
            hashtags=["Mashreq"],
            mentions=[],
            gt_category=SignalCategory.FRAUD_RUMOR if i < 5 else SignalCategory.SERVICE_OUTAGE,
            gt_sentiment=-0.5 + (i * 0.1),
            gt_is_misinformation=i < 3,
            gt_virality_potential=50 + i * 5,
        ))
    
    return signals


@pytest.fixture
def sample_agent() -> AgentArchetype:
    """Create a sample agent archetype for testing."""
    return AgentArchetype(
        agent_id=uuid4(),
        archetype_name="Skeptical Tech Professional",
        demographic_segment="Millennial",
        financial_literacy=8,
        brand_loyalty=40,
        skepticism_score=9,
        network_influence=60,
        activity_frequency=3.5,
        preferred_platform=PlatformSource.LINKEDIN_STYLE,
        core_values=["Security", "Transparency", "Innovation"],
        persona_description="A tech-savvy professional who questions everything",
        behavioral_pattern="Researches before sharing, often fact-checks claims",
    )


@pytest.fixture
def sample_agents(sample_agent: AgentArchetype) -> list[AgentArchetype]:
    """Create a list of sample agents for simulation tests."""
    agents = [sample_agent]
    
    # Add more diverse agents
    agents.append(AgentArchetype(
        agent_id=uuid4(),
        archetype_name="Anxious Saver",
        demographic_segment="GenZ",
        financial_literacy=3,
        brand_loyalty=20,
        skepticism_score=2,
        network_influence=80,
        activity_frequency=8.0,
        preferred_platform=PlatformSource.X_STYLE,
        core_values=["Safety", "Speed"],
        persona_description="Young person worried about their savings",
        behavioral_pattern="Quick to share alarming news without verification",
    ))
    
    agents.append(AgentArchetype(
        agent_id=uuid4(),
        archetype_name="Loyal Customer",
        demographic_segment="HNI",
        financial_literacy=9,
        brand_loyalty=95,
        skepticism_score=7,
        network_influence=40,
        activity_frequency=1.0,
        preferred_platform=PlatformSource.LINKEDIN_STYLE,
        core_values=["Trust", "Stability", "Reputation"],
        persona_description="Long-term bank customer with high net worth",
        behavioral_pattern="Defends the brand, reports misinformation",
    ))
    
    return agents


@pytest.fixture
def sample_scenario() -> Scenario:
    """Create a sample scenario for testing."""
    return Scenario(
        scenario_id=uuid4(),
        created_at=datetime.now(),
        scenario_name="Test Data Leak Rumor",
        description="A test scenario simulating rumors of a data breach",
        trigger_category=SignalCategory.FRAUD_RUMOR,
        target_segment="All",
        simulation_duration_hours=24,
        severity_level=SeverityLevel.HIGH,
        expected_velocity_peak=75,
        recommended_response_time_hours=4.0,
        key_narratives=["Data breach", "Customer data exposed"],
        monitoring_keywords=["hack", "breach", "data", "leak"],
        potential_impact={"reputation": "high", "regulatory": "medium"},
    )


# =============================================================================
# API Test Fixtures
# =============================================================================

@pytest.fixture
def test_client():
    """Create a test client for API testing."""
    from fastapi.testclient import TestClient
    from backend.api.main import app
    
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Create an async test client for API testing."""
    from httpx import AsyncClient, ASGITransport
    from backend.api.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
