# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an A2A (Agent-to-Agent) with MCP (Model Context Protocol) sample project that demonstrates how to leverage MCP as a standardized mechanism for discovering and retrieving A2A Agent Cards. The project implements a travel planning system with multiple specialized agents that communicate using the A2A protocol.

## Development Commands

This project uses `uv` for Python dependency management:

- **Install dependencies**: `uv venv && source .venv/bin/activate` (setup virtual environment)
- **Install with dev dependencies**: `uv sync --extra dev` (includes pytest and testing tools)
- **Run complete demo**: `bash run.sh` (starts all services and runs client)
- **Run unit tests**: `bash run_tests.sh` or `uv run pytest tests/test_orchestrator_agent.py -v -m "not integration"`
- **Run integration tests**: `bash run_integration_tests.sh` or `uv run pytest tests/ -v -m integration` (requires .env with AZURE_OPENAI_API_KEY)
- **Run integration tests (command line)**: `bash run_integration_tests_cmd.sh` or `pip install -r requirements_tests_integration.txt && python -m pytest tests/test_orchestrator_agent_integration.py -v -m integration`
- **Run all tests**: `uv run pytest tests/ -v`
- **Run MCP server**: `uv run --env-file .env a2a-mcp --run mcp-server --transport sse --port 10100`
- **Run individual agents**: `uv run --env-file .env src/a2a_mcp/agents/ --agent-card <agent_card_file> --port <port>`
- **Run test client**: `uv run --env-file .env src/a2a_mcp/mcp/client.py --resource "resource://agent_cards/list" --find_agent "I would like to plan a trip to France."`

### Agent Startup Commands

Each agent runs on a specific port with its corresponding agent card:
- **Orchestrator Agent (10101)**: `--agent-card agent_cards/orchestrator_agent.json`
- **Planner Agent (10102)**: `--agent-card agent_cards/planner_agent.json`
- **Air Ticketing Agent (10103)**: `--agent-card agent_cards/air_ticketing_agent.json`
- **Hotel Booking Agent (10104)**: `--agent-card agent_cards/hotel_booking_agent.json`
- **Car Rental Agent (10105)**: `--agent-card agent_cards/car_rental_agent.json`

## Architecture Overview

### Core A2A-MCP Integration Pattern

**Agent Discovery via MCP**: The system uses MCP as a centralized registry for A2A Agent Cards. Agents query the MCP server to discover other agents dynamically rather than having hardcoded connections.

**Multi-Agent Orchestration**: The architecture follows a hub-and-spoke model where the Orchestrator Agent coordinates multiple specialized Task Agents through the A2A protocol.

**Task-Based Workflow**: The system decomposes user requests into structured task plans and executes them through agent collaboration.

### Key Architectural Components

**Orchestrator Agent (`orchestrator_agent.py`)**: Central coordinator that receives user requests, uses the Planner Agent to decompose tasks, discovers appropriate Task Agents via MCP, and orchestrates execution using A2A communication.

**Planner Agent (`langgraph_planner_agent.py`)**: Built with LangGraph, responsible for analyzing user queries and generating structured task lists with required capabilities for each task.

**Task Agents (`adk_travel_agent.py`)**: Specialized agents built with Google ADK that handle specific domains (flights, hotels, car rentals). Each uses the same codebase but different agent cards for specialization.

**MCP Server (`mcp/server.py`)**: Serves agent cards as resources and provides tools for agent discovery. Uses embeddings to match user queries to appropriate agents and exposes SQLite database tools for travel data.

**Agent Cards (`agent_cards/`)**: JSON schemas that define agent capabilities, endpoints, and skills. These are served by the MCP server and used for dynamic agent discovery.

### Data Flow Architecture

1. **User Query → Orchestrator**: Initial request received
2. **Orchestrator → Planner**: Query sent for decomposition via A2A
3. **Planner → Orchestrator**: Structured task list returned
4. **Orchestrator → MCP**: Query for suitable agents per task
5. **Orchestrator → Task Agents**: Direct A2A communication for task execution
6. **Task Agents → MCP**: Access to shared tools and data
7. **Orchestrator → User**: Aggregated response

### Implementation Patterns

**Agent Executor Pattern**: All agents follow the `GenericAgentExecutor` pattern from `agent_executor.py` which handles A2A protocol communication, task state management, and event streaming.

**Base Agent Architecture**: Common functionality is abstracted in `base_agent.py` with Pydantic models for configuration and validation.

**Workflow Management**: Complex task orchestration is managed through `workflow.py` with state tracking and dependency management.

**MCP Integration**: The MCP server provides both resource discovery (agent cards) and tool access (database queries, embeddings) to enable dynamic agent collaboration.

### Security Considerations

**External Agent Data**: All data from external agents should be treated as untrusted input. Agent cards, messages, and artifacts must be validated and sanitized to prevent prompt injection attacks.

**API Key Management**: The system uses `init_api_key()` from `utils.py` to handle secure credential management for Google Generative AI and other services.

## Development Patterns

**Agent Card Structure**: Each agent must have a corresponding JSON agent card in `agent_cards/` that defines its capabilities, endpoints, and skill descriptions for MCP discovery.

**Travel Domain Model**: The system uses structured Pydantic models in `types.py` (TripInfo, TaskList, AgentResponse) to ensure consistent data exchange between agents.

**Database Integration**: Task agents access travel data through MCP tools that query the SQLite database (`travel_agency.db`) for flights, hotels, and car rentals.

**Streaming Responses**: All agents support real-time streaming via A2A event queues using `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent`.

When working with this codebase, understand that the key innovation is using MCP as a service registry for A2A agents, enabling dynamic discovery and flexible agent collaboration without hardcoded dependencies.