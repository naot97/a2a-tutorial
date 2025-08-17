#!/bin/bash

# Integration test runner script for a2a_mcp project
set -e

echo "Installing test dependencies..."
uv sync --extra dev

echo "Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Some integration tests may be skipped."
    echo "Create a .env file with Azure OpenAI credentials to run full integration tests."
fi

echo "Running integration tests..."
uv run pytest tests/test_orchestrator_agent_integration.py tests/test_langgraph_planner_integration.py tests/test_adk_travel_agent_integration.py -v -m integration

echo "Integration test run complete!"