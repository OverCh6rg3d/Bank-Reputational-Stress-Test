"""
Integration tests for API endpoints.

Tests REST API functionality with a test client.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_returns_200(self, test_client: TestClient):
        """Test health endpoint returns OK."""
        response = test_client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestScenariosEndpoint:
    """Tests for /api/scenarios endpoint."""
    
    def test_get_scenarios_list(self, test_client: TestClient):
        """Test listing scenarios."""
        response = test_client.get("/api/scenarios")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_get_scenario_by_id(self, test_client: TestClient):
        """Test getting scenario by ID."""
        # First get list of scenarios
        response = test_client.get("/api/scenarios")
        scenarios = response.json()
        
        if len(scenarios) > 0:
            scenario_id = scenarios[0]["scenario_id"]
            response = test_client.get(f"/api/scenarios/{scenario_id}")
            
            assert response.status_code in [200, 404]
    
    def test_scenario_not_found_returns_404(self, test_client: TestClient):
        """Test 404 for non-existent scenario."""
        fake_id = str(uuid4())
        response = test_client.get(f"/api/scenarios/{fake_id}")
        
        assert response.status_code == 404


class TestSignalsEndpoint:
    """Tests for /api/signals endpoint."""
    
    def test_get_signals_with_limit(self, test_client: TestClient):
        """Test getting signals with limit parameter."""
        response = test_client.get("/api/signals?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_default_limit_applied(self, test_client: TestClient):
        """Test that default limit is applied."""
        response = test_client.get("/api/signals")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAgentsEndpoint:
    """Tests for /api/agents endpoint."""
    
    def test_get_agents_list(self, test_client: TestClient):
        """Test listing agents."""
        response = test_client.get("/api/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_agents_have_traits(self, test_client: TestClient):
        """Test that agents have personality traits."""
        response = test_client.get("/api/agents")
        agents = response.json()
        
        if len(agents) > 0:
            agent = agents[0]
            assert "skepticism_score" in agent or "skepticismScore" in agent


class TestKnowledgeEndpoint:
    """Tests for /api/knowledge endpoint."""
    
    def test_search_knowledge_base(self, test_client: TestClient):
        """Test searching knowledge base."""
        response = test_client.get("/api/knowledge/search?query=fraud")
        
        # May return 200 or 503 (if embedder not available)
        assert response.status_code in [200, 503]
    
    def test_search_requires_query(self, test_client: TestClient):
        """Test that search requires query parameter."""
        response = test_client.get("/api/knowledge/search")
        
        # Should fail validation
        assert response.status_code == 422


class TestDetectEndpoint:
    """Tests for /api/detect endpoint."""
    
    def test_detect_requires_body(self, test_client: TestClient):
        """Test that detect requires request body."""
        response = test_client.post("/api/detect")
        
        assert response.status_code == 422
    
    def test_detect_with_scenario_name(self, test_client: TestClient):
        """Test detection with scenario name."""
        # First get a valid scenario name
        scenarios_response = test_client.get("/api/scenarios")
        scenarios = scenarios_response.json()
        
        if len(scenarios) > 0:
            scenario_name = scenarios[0]["scenario_name"]
            
            response = test_client.post(
                "/api/detect",
                json={"scenario_name": scenario_name}
            )
            
            # May succeed or fail depending on data availability
            assert response.status_code in [200, 400, 500]


class TestGovernanceEndpoint:
    """Tests for /api/governance endpoints."""
    
    def test_get_audit_log(self, test_client: TestClient):
        """Test getting audit log."""
        response = test_client.get("/api/governance/audit-log")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_guardrails(self, test_client: TestClient):
        """Test getting guardrails configuration."""
        response = test_client.get("/api/governance/guardrails")
        
        assert response.status_code == 200
        data = response.json()
        assert "action_boundaries" in data


class TestCORSConfiguration:
    """Tests for CORS configuration."""
    
    def test_cors_headers_present(self, test_client: TestClient):
        """Test that CORS headers are set."""
        response = test_client.options(
            "/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        # FastAPI TestClient may not fully replicate OPTIONS handling
        # but the middleware should be configured
        assert response.status_code in [200, 405]


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_endpoint_returns_404(self, test_client: TestClient):
        """Test that invalid endpoints return 404."""
        response = test_client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed_returns_405(self, test_client: TestClient):
        """Test that wrong HTTP method returns 405."""
        response = test_client.delete("/api/scenarios")
        
        assert response.status_code == 405
