# Integration Tests for A2A MCP

This document explains how to run the integration tests for the OrchestratorAgent using real Azure OpenAI API calls.

## Quick Start

### Option 1: Using the automated script
```bash
bash run_integration_tests_cmd.sh
```

### Option 2: Manual setup
```bash
# Install dependencies
pip install -r requirements_tests_integration.txt

# Run tests
python -m pytest tests/test_orchestrator_agent_integration.py -v -m integration
```

## Prerequisites

### 1. Environment Variables
Create a `.env` file in the project root with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_API_VERSION=2025-01-01-preview
```

### 2. Python Requirements
- Python 3.13+ (as specified in pyproject.toml)
- pip package manager

## What the Tests Cover

The integration tests verify real API functionality across multiple agents:

### OrchestratorAgent Tests (`test_orchestrator_agent_integration.py`)
1. **`test_generate_summary_works`** - Tests that the `generate_summary()` method works with real Azure OpenAI API
2. **`test_answer_user_question_works`** - Tests that the `answer_user_question()` method works with real API  
3. **`test_agent_initialization_with_env`** - Tests that the agent initializes correctly with environment variables

### LangGraphPlannerAgent Tests (`test_langgraph_planner_integration.py`)
1. **`test_planner_agent_initialization`** - Tests LangGraph planner initialization with Azure OpenAI
2. **`test_invoke_method_works`** - Tests planning functionality via invoke method with real API
3. **`test_stream_method_works`** - Tests streaming planning responses with real API

### ADK TravelAgent Tests (`test_adk_travel_agent_integration.py`) 
1. **`test_travel_agent_initialization`** - Tests ADK travel agent initialization
2. **`test_stream_method_works`** - Tests streaming travel booking functionality (requires MCP server)
3. **`test_format_response_method`** - Tests response formatting for JSON and text
4. **`test_get_agent_response_with_json_data`** - Tests structured booking data processing
5. **`test_get_agent_response_with_input_required`** - Tests input request handling

## Test Output

Each test will print the actual API responses for verification:
- Generated summaries from travel booking data
- Q&A responses with JSON structure validation
- Agent initialization confirmation

## Troubleshooting

### Tests are skipped
- Ensure `.env` file exists with valid Azure OpenAI credentials
- Check that all required environment variables are set

### API errors
- Verify your Azure OpenAI API key is valid and has sufficient quota
- Ensure the endpoint URL is correct for your Azure resource
- Check that the API version is supported

### Import errors  
- Run `pip install -r requirements_tests_integration.txt` to install all dependencies
- Ensure you're using Python 3.13+ as required by the project

## Alternative: Using uv (if available)

If you have `uv` installed, you can also run:
```bash
bash run_integration_tests.sh
```

This uses the project's `uv` configuration and is the recommended approach for development.