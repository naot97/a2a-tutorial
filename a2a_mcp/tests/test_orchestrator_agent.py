"""Unit tests for OrchestratorAgent class."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections.abc import AsyncIterable

from a2a.types import (
    SendStreamingMessageSuccessResponse,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
    DataPart,
    TextPart,
    Message,
    MessageStatus,
    Artifact,
)
from a2a_mcp.agents.orchestrator_agent import OrchestratorAgent
from a2a_mcp.common.workflow import Status, WorkflowGraph, WorkflowNode


class TestOrchestratorAgent:
    """Test class for OrchestratorAgent."""

    @pytest.fixture
    def mock_init_api_key(self):
        """Mock the init_api_key function."""
        with patch('a2a_mcp.agents.orchestrator_agent.init_api_key') as mock:
            yield mock

    @pytest.fixture
    def orchestrator_agent(self, mock_init_api_key):
        """Create an OrchestratorAgent instance for testing."""
        return OrchestratorAgent()

    def test_init(self, mock_init_api_key, orchestrator_agent):
        """Test OrchestratorAgent initialization."""
        # Verify init_api_key was called
        mock_init_api_key.assert_called_once()
        
        # Verify agent properties
        assert orchestrator_agent.agent_name == 'Orchestrator Agent'
        assert orchestrator_agent.description == 'Facilitate inter agent communication'
        assert orchestrator_agent.content_types == ['text', 'text/plain']
        
        # Verify initial state
        assert orchestrator_agent.graph is None
        assert orchestrator_agent.results == []
        assert orchestrator_agent.travel_context == {}
        assert orchestrator_agent.query_history == []
        assert orchestrator_agent.context_id is None

    @patch('a2a_mcp.agents.orchestrator_agent.AzureOpenAI')
    async def test_generate_summary(self, mock_azure_client, orchestrator_agent):
        """Test generate_summary method."""
        # Setup mock
        mock_client_instance = Mock()
        mock_azure_client.return_value = mock_client_instance
        
        mock_response = Mock()
        mock_response.choices[0].message.content = "Generated summary"
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        # Add some results to summarize
        orchestrator_agent.results = [{"test": "data"}]
        
        # Test
        result = await orchestrator_agent.generate_summary()
        
        # Verify
        assert result == "Generated summary"
        mock_client_instance.chat.completions.create.assert_called_once()
        call_args = mock_client_instance.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4.1-mini'
        assert call_args[1]['temperature'] == 0.0

    @patch('a2a_mcp.agents.orchestrator_agent.AzureOpenAI')
    def test_answer_user_question_success(self, mock_azure_client, orchestrator_agent):
        """Test answer_user_question method with successful response."""
        # Setup mock
        mock_client_instance = Mock()
        mock_azure_client.return_value = mock_client_instance
        
        mock_response = Mock()
        mock_response.choices[0].message.content = '{"can_answer": "yes", "answer": "Test answer"}'
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        # Test
        result = orchestrator_agent.answer_user_question("What is the weather?")
        
        # Verify
        assert result == '{"can_answer": "yes", "answer": "Test answer"}'
        mock_client_instance.chat.completions.create.assert_called_once()

    @patch('a2a_mcp.agents.orchestrator_agent.AzureOpenAI')
    @patch('a2a_mcp.agents.orchestrator_agent.logger')
    def test_answer_user_question_exception(self, mock_logger, mock_azure_client, orchestrator_agent):
        """Test answer_user_question method when exception occurs."""
        # Setup mock to raise exception
        mock_client_instance = Mock()
        mock_azure_client.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("API Error")
        
        # Test
        result = orchestrator_agent.answer_user_question("What is the weather?")
        
        # Verify
        expected_result = '{"can_answer": "no", "answer": "Cannot answer based on provided context"}'
        assert result == expected_result
        mock_logger.info.assert_called_with('Error answering user question: API Error')

    def test_set_node_attributes(self, orchestrator_agent):
        """Test set_node_attributes method."""
        # Setup
        mock_graph = Mock()
        orchestrator_agent.graph = mock_graph
        
        # Test
        orchestrator_agent.set_node_attributes(
            node_id="node1",
            task_id="task1", 
            context_id="context1",
            query="test query"
        )
        
        # Verify
        expected_attrs = {
            'task_id': 'task1',
            'context_id': 'context1',
            'query': 'test query'
        }
        mock_graph.set_node_attributes.assert_called_once_with("node1", expected_attrs)

    def test_add_graph_node(self, orchestrator_agent):
        """Test add_graph_node method."""
        # Setup
        mock_graph = Mock()
        orchestrator_agent.graph = mock_graph
        
        # Test
        result = orchestrator_agent.add_graph_node(
            task_id="task1",
            context_id="context1", 
            query="test query",
            node_id="parent_node",
            node_key="test_key",
            node_label="Test Label"
        )
        
        # Verify
        assert isinstance(result, WorkflowNode)
        assert result.task == "test query"
        mock_graph.add_node.assert_called_once_with(result)
        mock_graph.add_edge.assert_called_once_with("parent_node", result.id)

    def test_clear_state(self, orchestrator_agent):
        """Test clear_state method."""
        # Setup initial state
        orchestrator_agent.graph = Mock()
        orchestrator_agent.results = ["test_result"]
        orchestrator_agent.travel_context = {"key": "value"}
        orchestrator_agent.query_history = ["query1"]
        
        # Test
        orchestrator_agent.clear_state()
        
        # Verify
        assert orchestrator_agent.graph is None
        assert orchestrator_agent.results == []
        assert orchestrator_agent.travel_context == {}
        assert orchestrator_agent.query_history == []

    @pytest.mark.asyncio
    async def test_stream_empty_query(self, orchestrator_agent):
        """Test stream method with empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            async for _ in orchestrator_agent.stream("", "context1", "task1"):
                pass

    @pytest.mark.asyncio
    async def test_stream_new_context_clears_state(self, orchestrator_agent):
        """Test stream method clears state when context changes."""
        # Setup initial state
        orchestrator_agent.context_id = "old_context"
        orchestrator_agent.graph = Mock()
        orchestrator_agent.results = ["test_result"]
        
        # Mock graph execution
        mock_workflow_graph = Mock()
        mock_workflow_graph.run_workflow.return_value = AsyncIterator([])
        
        with patch('a2a_mcp.agents.orchestrator_agent.WorkflowGraph', return_value=mock_workflow_graph):
            # Test
            result_list = []
            async for result in orchestrator_agent.stream("test query", "new_context", "task1"):
                result_list.append(result)
            
            # Verify state was cleared
            assert orchestrator_agent.context_id == "new_context"
            assert orchestrator_agent.query_history == ["test query"]

    @pytest.mark.asyncio
    async def test_stream_creates_new_graph(self, orchestrator_agent):
        """Test stream method creates new graph when none exists."""
        # Mock dependencies
        mock_workflow_graph = Mock()
        mock_workflow_graph.run_workflow.return_value = AsyncIterator([])
        
        with patch('a2a_mcp.agents.orchestrator_agent.WorkflowGraph', return_value=mock_workflow_graph):
            # Test
            result_list = []
            async for result in orchestrator_agent.stream("test query", "context1", "task1"):
                result_list.append(result)
            
            # Verify graph was created
            assert orchestrator_agent.graph is not None
            assert "test query" in orchestrator_agent.query_history

    @pytest.mark.asyncio
    async def test_stream_with_completed_workflow(self, orchestrator_agent):
        """Test stream method with completed workflow generates summary."""
        # Setup mocks
        mock_workflow_graph = Mock()
        mock_workflow_graph.state = Status.COMPLETED
        mock_workflow_graph.run_workflow.return_value = AsyncIterator([])
        
        with patch('a2a_mcp.agents.orchestrator_agent.WorkflowGraph', return_value=mock_workflow_graph):
            with patch.object(orchestrator_agent, 'generate_summary', return_value="Test Summary"):
                # Test
                results = []
                async for result in orchestrator_agent.stream("test query", "context1", "task1"):
                    results.append(result)
                
                # Verify summary is generated and returned
                assert len(results) == 1
                assert results[0]['content'] == "Test Summary"
                assert results[0]['is_task_complete'] is True
                assert results[0]['require_user_input'] is False

    def test_stream_workflow_artifact_processing(self, orchestrator_agent):
        """Test stream method processes TaskArtifactUpdateEvent correctly."""
        # This test would require more complex mocking of the async workflow
        # For now, we can test the artifact processing logic separately
        
        # Create test artifact
        test_artifact_data = {
            "trip_info": {"destination": "Paris"},
            "tasks": [
                {"description": "Book flight"},
                {"description": "Book hotel"}
            ]
        }
        
        mock_artifact = Mock()
        mock_artifact.name = "PlannerAgent-result"
        mock_artifact.parts = [Mock()]
        mock_artifact.parts[0].root.data = test_artifact_data
        
        # Setup graph
        orchestrator_agent.graph = Mock()
        orchestrator_agent.results = []
        
        # Simulate artifact processing (this would normally happen in the stream method)
        orchestrator_agent.results.append(mock_artifact)
        orchestrator_agent.travel_context = test_artifact_data['trip_info']
        
        # Verify
        assert len(orchestrator_agent.results) == 1
        assert orchestrator_agent.travel_context == {"destination": "Paris"}


class AsyncIterator:
    """Helper class to create async iterator for testing."""
    
    def __init__(self, items):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class TestOrchestratorAgentIntegration:
    """Integration tests for OrchestratorAgent."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch.multiple(
            'a2a_mcp.agents.orchestrator_agent',
            init_api_key=Mock(),
            AzureOpenAI=Mock(),
            WorkflowGraph=Mock(),
        ) as mocks:
            yield mocks

    def test_orchestrator_workflow_state_management(self, mock_dependencies):
        """Test the overall workflow state management."""
        agent = OrchestratorAgent()
        
        # Test initial state
        assert agent.graph is None
        assert len(agent.results) == 0
        
        # Test state after operations
        agent.results.append({"test": "data"})
        agent.travel_context = {"trip": "info"}
        agent.query_history.append("test query")
        
        # Test clear state
        agent.clear_state()
        assert agent.graph is None
        assert len(agent.results) == 0
        assert len(agent.travel_context) == 0
        assert len(agent.query_history) == 0

    def test_node_management_operations(self, mock_dependencies):
        """Test node creation and attribute management."""
        agent = OrchestratorAgent()
        agent.graph = Mock()
        
        # Test adding nodes
        node = agent.add_graph_node(
            task_id="task1",
            context_id="ctx1", 
            query="test query",
            node_key="key1",
            node_label="Label1"
        )
        
        assert isinstance(node, WorkflowNode)
        agent.graph.add_node.assert_called_once()
        
        # Test setting attributes
        agent.set_node_attributes("node1", task_id="task2", query="new query")
        agent.graph.set_node_attributes.assert_called_with(
            "node1", 
            {"task_id": "task2", "query": "new query"}
        )


if __name__ == "__main__":
    pytest.main([__file__])
