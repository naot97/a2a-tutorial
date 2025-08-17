#!/bin/bash

# Simple command line integration test runner for a2a_mcp project
# This script uses pip instead of uv for broader compatibility

set -e

echo "=== A2A MCP Integration Tests ==="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

echo "Installing integration test dependencies..."
pip install -r requirements_tests_integration.txt

echo ""
echo "Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Integration tests may be skipped."
    echo "Create a .env file with Azure OpenAI credentials to run full integration tests."
    echo ""
    echo "Required environment variables:"
    echo "  AZURE_OPENAI_API_KEY=your_api_key_here"
    echo "  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/"
    echo "  OPENAI_API_VERSION=2025-01-01-preview"
    echo ""
fi

echo "Running integration tests..."
python -m pytest tests/test_orchestrator_agent_integration.py tests/test_langgraph_planner_integration.py tests/test_adk_travel_agent_integration.py -v -m integration

echo ""
echo "Integration test run complete!"