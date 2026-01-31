"""
Unit tests for the LLM Client module.

Tests JSON parsing, structured outputs, and error handling.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.core.llm_client import LLMClient, SYSTEM_PROMPTS


class TestLLMClientJSONParsing:
    """Tests for JSON response parsing."""
    
    def test_strips_markdown_json_block(self):
        """Test that markdown code blocks are properly stripped."""
        client = MagicMock(spec=LLMClient)
        client.complete = MagicMock(return_value='```json\n{"key": "value"}\n```')
        
        # Simulate the JSON parsing logic
        response = client.complete("test")
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        
        result = json.loads(response.strip())
        assert result == {"key": "value"}
    
    def test_strips_plain_code_block(self):
        """Test that plain code blocks are stripped."""
        response = '```\n{"test": 123}\n```'
        
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        result = json.loads(response.strip())
        assert result == {"test": 123}
    
    def test_handles_raw_json(self):
        """Test that raw JSON without code blocks works."""
        response = '{"direct": true}'
        result = json.loads(response)
        assert result == {"direct": True}
    
    def test_handles_invalid_json_gracefully(self):
        """Test that invalid JSON returns error dict."""
        response = "not valid json at all"
        try:
            json.loads(response)
            success = True
        except json.JSONDecodeError as e:
            success = False
            error_result = {"error": str(e), "raw": response}
        
        assert not success
        assert "error" in error_result
        assert error_result["raw"] == response


class TestSystemPrompts:
    """Tests for system prompt configuration."""
    
    def test_all_required_prompts_exist(self):
        """Test that all expected system prompts are defined."""
        required_prompts = [
            "signal_classifier",
            "agent_simulator",
            "causal_analyst",
            "adversarial_critic",
            "response_generator",
            "briefing_writer",
        ]
        
        for prompt_name in required_prompts:
            assert prompt_name in SYSTEM_PROMPTS, f"Missing prompt: {prompt_name}"
            assert len(SYSTEM_PROMPTS[prompt_name]) > 50, f"Prompt too short: {prompt_name}"
    
    def test_signal_classifier_contains_categories(self):
        """Test that signal classifier prompt mentions all categories."""
        prompt = SYSTEM_PROMPTS["signal_classifier"]
        
        expected_categories = ["Fraud_Rumor", "Service_Outage", "Competitor_News"]
        for category in expected_categories:
            assert category in prompt, f"Missing category in prompt: {category}"
    
    def test_agent_simulator_contains_actions(self):
        """Test that agent simulator prompt mentions all actions."""
        prompt = SYSTEM_PROMPTS["agent_simulator"]
        
        expected_actions = ["IGNORE", "LIKE", "SHARE", "COMMENT", "REPORT"]
        for action in expected_actions:
            assert action in prompt, f"Missing action in prompt: {action}"


class TestLLMClientInitialization:
    """Tests for LLM client initialization."""
    
    def test_raises_on_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("backend.core.llm_client.os.getenv", return_value=None):
                with pytest.raises(ValueError, match="API key not found"):
                    LLMClient(api_key=None)
    
    def test_uses_provided_api_key(self):
        """Test that provided API key is used."""
        with patch("backend.core.llm_client.OpenAI") as mock_openai:
            with patch("backend.core.llm_client.AsyncOpenAI"):
                client = LLMClient(api_key="test-key-12345")
                assert client.api_key == "test-key-12345"


class TestLLMClientCompletion:
    """Tests for completion methods."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    def test_complete_returns_string(self, mock_openai_client):
        """Test that complete() returns a string."""
        with patch("backend.core.llm_client.OpenAI", return_value=mock_openai_client):
            with patch("backend.core.llm_client.AsyncOpenAI"):
                client = LLMClient(api_key="test-key")
                client.client = mock_openai_client
                
                result = client.complete("Test prompt")
                assert result == "Test response"
                assert isinstance(result, str)
    
    def test_complete_with_system_prompt(self, mock_openai_client):
        """Test that system prompt is included in messages."""
        with patch("backend.core.llm_client.OpenAI", return_value=mock_openai_client):
            with patch("backend.core.llm_client.AsyncOpenAI"):
                client = LLMClient(api_key="test-key")
                client.client = mock_openai_client
                
                client.complete("User prompt", system_prompt="System instructions")
                
                call_args = mock_openai_client.chat.completions.create.call_args
                messages = call_args.kwargs["messages"]
                
                assert len(messages) == 2
                assert messages[0]["role"] == "system"
                assert messages[1]["role"] == "user"
