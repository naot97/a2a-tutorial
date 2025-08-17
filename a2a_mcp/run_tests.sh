#!/bin/bash

# Test runner script for a2a_mcp project
set -e

echo "Installing test dependencies..."
uv sync --extra dev

echo "Running unit tests..."
uv run pytest tests/test_orchestrator_agent.py -v -m "not integration"

echo ""
echo "To run integration tests (requires API keys), use:"
echo "  bash run_integration_tests.sh"
echo "  or: uv run pytest tests/ -v -m integration"

echo "Unit test run complete!"