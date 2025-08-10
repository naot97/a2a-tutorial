# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This is a Python Agent-to-Agent (A2A) protocol sample using uv for dependency management:

- **Start the agent server**: `uv run .`
- **Run test client**: `uv run test_client.py`
- **Install dependencies**: `uv sync` (uses uv.lock file)

## Container Development

- **Build container**: `podman build . -t helloworld-a2a-server`
- **Run container**: `podman run -p 9999:9999 helloworld-a2a-server`
- **Validate with CLI client**: `cd samples/python/hosts/cli && uv run . --agent http://localhost:9999`

## Architecture

This is a Hello World example demonstrating the A2A protocol architecture:

### Core Components

- **`__main__.py`**: Server entry point that configures the A2A Starlette application with public and authenticated extended agent cards
- **`agent_executor.py`**: Contains `HelloWorldAgentExecutor` implementing the `AgentExecutor` interface, wrapping a simple `HelloWorldAgent` 
- **`test_client.py`**: A2A client demonstrating both regular and streaming message sending

### A2A Protocol Structure

The agent implements a dual-card system:
- **Public Agent Card**: Basic "hello_world" skill available to all users
- **Extended Agent Card**: Additional "super_hello_world" skill for authenticated users (using bearer token)

### Key Patterns

- **Agent Cards**: Defined with skills, capabilities, and metadata using `AgentCard` and `AgentSkill` types
- **Request Handling**: Uses `DefaultRequestHandler` with `InMemoryTaskStore` for task management
- **Event Streaming**: Agent execution communicates via `EventQueue` for real-time message delivery
- **Client Resolution**: `A2ACardResolver` handles fetching public/extended cards from well-known endpoints

### Security Note

All external agent data should be treated as untrusted input. The sample includes security disclaimers about validating data from external agents to prevent prompt injection attacks.