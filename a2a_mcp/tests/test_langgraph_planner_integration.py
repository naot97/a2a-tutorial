"""Simple integration tests for LangGraphPlannerAgent using real Azure OpenAI API calls."""

import os
import json
from pathlib import Path

import pytest
from dotenv import load_dotenv
import sys

# Ensure the parent directory is in the path for imports
print(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
from src.a2a_mcp.agents.langgraph_planner_agent import LangGraphPlannerAgent


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
def planner_agent(env_setup):
    """Create LangGraphPlannerAgent with real environment setup."""
    # Environment variables are already loaded by env_setup fixture
    return LangGraphPlannerAgent()


@pytest.mark.integration
def test_planner_agent_initialization(env_setup):
    """Test that LangGraphPlannerAgent initializes correctly with environment variables."""
    # Environment variables are already loaded by env_setup fixture
    agent = LangGraphPlannerAgent()

    # Verify basic initialization
    assert agent.agent_name == "PlannerAgent"
    assert agent.description == "Breakdown the user request into executable tasks"
    assert agent.content_types == ["text", "text/plain"]
    assert agent.model is not None
    assert agent.graph is not None
    print(f"Planner agent initialized successfully")


@pytest.mark.integration
def test_invoke_method_works(planner_agent):
    """Test that invoke method works with real API."""
    query = "Plan a simple trip to Paris for 3 days"
    session_id = "test_session_123"

    # Call the real API via invoke
    response = planner_agent.invoke(query, session_id)

    # Basic validation
    assert isinstance(response, dict)
    assert 'content' in response
    assert 'is_task_complete' in response
    assert 'require_user_input' in response

    print(f"Invoke response: {response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_method_works(planner_agent):
    """Test that stream method works with real API."""
    query = "Plan a weekend trip to San Francisco"
    session_id = "test_session_stream"
    task_id = "task_123"

    # Collect streaming responses
    responses = []
    async for response in planner_agent.stream(query, session_id, task_id):
        responses.append(response)
        # Limit responses to avoid long test runs
        if len(responses) >= 5:
            break

    # Basic validation
    assert len(responses) > 0

    for response in responses:
        assert isinstance(response, dict)
        assert 'content' in response
        assert 'is_task_complete' in response
        assert 'require_user_input' in response

    print(f"Stream responses count: {len(responses)}")
    print(f"First response: {responses[0] if responses else 'None'}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])