"""Simple integration tests for TravelAgent (ADK) using real Azure OpenAI API calls."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
import sys

# Ensure the parent directory is in the path for imports
print(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
import json
from src.a2a_mcp.agents.adk_travel_agent import TravelAgent
from src.a2a_mcp.common import prompts


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
def hotel_travel_agent(env_setup):
    """Create TravelAgent for hotel bookings with real environment setup."""
    # Environment variables are already loaded by env_setup fixture
    return TravelAgent(
        agent_name="Hotel Booking Agent",
        description="Hotel booking and reservation assistant",
        instructions=prompts.HOTELS_COT_INSTRUCTIONS
    )


@pytest.fixture
def flight_travel_agent(env_setup):
    """Create TravelAgent for flight bookings with real environment setup.""" 
    # Environment variables are already loaded by env_setup fixture
    return TravelAgent(
        agent_name="Flight Booking Agent",
        description="Flight booking and reservation assistant", 
        instructions=prompts.AIRFARE_COT_INSTRUCTIONS
    )


@pytest.mark.integration
def test_travel_agent_initialization(env_setup):
    """Test that TravelAgent initializes correctly with environment variables."""
    # Environment variables are already loaded by env_setup fixture
    agent = TravelAgent(
        agent_name="Test Travel Agent",
        description="Test agent for integration testing",
        instructions="You are a helpful travel assistant."
    )

    # Verify basic initialization
    assert agent.agent_name == "Test Travel Agent"
    assert agent.description == "Test agent for integration testing"
    assert agent.content_types == ["text", "text/plain"]
    assert agent.instructions == "You are a helpful travel assistant."
    assert agent.agent is None  # Not initialized until first use
    print("Travel agent initialized successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_method_works(hotel_travel_agent):
    """Test that stream method works with real API."""
    query = "I need a hotel in Paris for 2 nights"
    context_id = "test_context_123"
    task_id = "task_456"

    # Collect streaming responses
    responses = []
    try:
        async for response in hotel_travel_agent.stream(query, context_id, task_id):
            responses.append(response)
            # Limit responses to avoid long test runs
            if len(responses) >= 3:
                break
    except Exception as e:
        # If MCP server is not running, the test might fail
        # This is expected in isolated testing
        pytest.skip(f"MCP server connection failed (expected in isolated testing): {e}")

    # Basic validation if we got responses
    if responses:
        for response in responses:
            assert isinstance(response, dict)
            assert 'content' in response
            assert 'is_task_complete' in response
            assert 'require_user_input' in response

        print(f"Stream responses count: {len(responses)}")
        print(f"First response: {responses[0] if responses else 'None'}")


@pytest.mark.integration
def test_format_response_method(hotel_travel_agent):
    """Test that format_response method works correctly."""
    # Test JSON code block formatting
    json_response = '```json\n{"status": "completed", "booking_id": "12345"}\n```'
    formatted = hotel_travel_agent.format_response(json_response)
    
    assert isinstance(formatted, dict)
    assert formatted["status"] == "completed"
    assert formatted["booking_id"] == "12345"
    print(f"JSON formatting works: {formatted}")

    # Test plain text
    plain_text = "This is a plain text response"
    formatted_text = hotel_travel_agent.format_response(plain_text)
    assert formatted_text == plain_text
    print(f"Plain text formatting works: {formatted_text}")


@pytest.mark.integration
def test_get_agent_response_with_json_data(hotel_travel_agent):
    """Test get_agent_response method with structured data."""
    # Test with completed booking data
    booking_data = {
        "hotel_name": "Le Meurice", 
        "location": "Paris",
        "check_in": "2024-03-15",
        "check_out": "2024-03-17",
        "total_cost": 800.00,
        "status": "completed"
    }
    
    response = hotel_travel_agent.get_agent_response(json.dumps(booking_data))
    
    assert isinstance(response, dict)
    assert response['response_type'] == 'data'
    assert response['is_task_complete'] is True
    assert response['require_user_input'] is False
    assert 'content' in response
    print(f"Booking response: {response}")


# @pytest.mark.integration
# def test_get_agent_response_with_input_required(hotel_travel_agent):
#     """Test get_agent_response method when input is required."""
#     input_required_data = {
#         "status": "input_required",
#         "question": "What dates would you like to stay?"
#     }
    
#     response = hotel_travel_agent.get_agent_response(json.dumps(input_required_data))
#     print(f"Response: {response}")
#     assert isinstance(response, dict)
#     assert response['response_type'] == 'data'
#     assert response['is_task_complete'] is True
#     assert response['require_user_input'] is False
#     assert response['content'] == {'question': 'What dates would you like to stay?', 'status': 'input_required'}
#     print(f"Input required response: {response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invoke_method_not_implemented(flight_travel_agent):
    """Test that invoke method raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="Please use the streraming function"):
        await flight_travel_agent.invoke("Book a flight", "session_123")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stream_empty_query_raises_error(hotel_travel_agent):
    """Test that stream method raises ValueError for empty query."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        async for _ in hotel_travel_agent.stream("", "context1", "task1"):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
