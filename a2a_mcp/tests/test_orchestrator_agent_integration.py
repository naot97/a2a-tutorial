"""Simple integration tests for OrchestratorAgent using real Azure OpenAI API calls."""

import os
import json
from pathlib import Path

import pytest
from dotenv import load_dotenv
import sys 
# Ensure the parent directory is in the path for imports
print(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
from src.a2a_mcp.agents.orchestrator_agent import OrchestratorAgent


@pytest.fixture(scope="session")
def env_setup():
    """Setup environment variables from .env file using dotenv."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        pytest.skip(".env file not found")

    # Verify required environment variables are set
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "OPENAI_API_VERSION"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")


@pytest.fixture
def orchestrator_agent(env_setup):
    """Create OrchestratorAgent with real environment setup."""
    # Environment variables are already loaded by env_setup fixture
    return OrchestratorAgent()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_summary_works(orchestrator_agent):
    """Test that generate_summary method works with real API."""
    # Setup simple test data
    orchestrator_agent.results = [
        {"name": "test-result", "content": {"message": "Booked flight to Paris", "cost": 500}}
    ]

    # Call the real API
    summary = await orchestrator_agent.generate_summary()
    print(f"Summary: {summary}")
    # Basic validation
    assert isinstance(summary, str)
    assert len(summary) > 20  # Should generate meaningful content
    print(f"Generated summary: {summary}")


@pytest.mark.integration
def test_answer_user_question_works(orchestrator_agent):
    """Test that answer_user_question method works with real API."""
    # Setup simple context
    orchestrator_agent.travel_context = {"destination": "Paris", "budget": "$2000"}
    orchestrator_agent.query_history = ["Plan a trip"]

    question = "What is my destination?"

    # Call the real API
    response = orchestrator_agent.answer_user_question(question)

    # Basic validation
    assert isinstance(response, str)
    response_data = json.loads(response)
    assert "can_answer" in response_data
    assert "answer" in response_data
    print(f"Q&A Response: {response}")


@pytest.mark.integration
def test_agent_initialization_with_env(env_setup):
    """Test that OrchestratorAgent initializes correctly with environment variables."""
    # Environment variables are already loaded by env_setup fixture
    agent = OrchestratorAgent()

    # Verify basic initialization
    assert agent.agent_name == "Orchestrator Agent"
    assert agent.results == []
    assert agent.travel_context == {}
    assert agent.query_history == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
