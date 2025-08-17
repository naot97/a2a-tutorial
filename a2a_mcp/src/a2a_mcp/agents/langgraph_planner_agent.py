# type: ignore

import logging
import os

from collections.abc import AsyncIterable
from typing import Any, Literal
from dotenv import load_dotenv

from a2a_mcp.common import prompts
from a2a_mcp.common.base_agent import BaseAgent
from a2a_mcp.common.types import TaskList
from langchain_core.messages import AIMessage
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Load environment variables
load_dotenv('/home/toannguyen19/my_workspace/a2a-samples/my-a2a-tutorial/.env')


memory = MemorySaver()
logger = logging.getLogger(__name__)


# class ResponseFormat(BaseModel):
#     """Respond to the user in this format."""

#     status: Literal['input_required', 'completed', 'error'] = 'input_required'
#     question: str = Field(
#         description='Input needed from the user to generate the plan'
#     )
#     content: TaskList = Field(
#         description='List of tasks when the plan is generated'
#     )

# 1) Replace Literal with an Enum
class Status(str, Enum):
    input_required = "input_required"
    completed = "completed"
    error = "error"

# 2) Define your content model(s)
class Task(BaseModel):
    title: str
    done: bool = False

# If you had a TaskList alias, you can just use List[Task]
class ResponseFormat(BaseModel):
    # optional: forbid extras for stricter parsing
    model_config = ConfigDict(extra="forbid")

    status: Status = Field(
        default=Status.input_required,
        description="Planner state."
    )
    question: Optional[str] = Field(
        default=None,
        description="Input needed from the user to generate the plan."
    )
    content: Optional[List[Task]] = Field(
        default=None,
        description="List of tasks when the plan is generated."
    )


class LangGraphPlannerAgent(BaseAgent):
    """Planner Agent backed by LangGraph."""

    def __init__(self):
        logger.info('Initializing LanggraphPlannerAgent')

        super().__init__(
            agent_name='PlannerAgent',
            description='Breakdown the user request into executable tasks',
            content_types=['text', 'text/plain'],
        )

        self.model = AzureChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0,
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )

        self.graph = create_react_agent(
            self.model,
            checkpointer=memory,
            prompt=prompts.PLANNER_COT_INSTRUCTIONS,
            response_format=ResponseFormat,
            tools=[],
        )

    def invoke(self, query, session_id) -> str:
        """
        Invoke the LangGraph planner agent with a user query and session ID.

        Args:
            query (str): The user query to process.
            session_id (str): The session identifier.

        Returns:
            str: The agent's response.
        """
        config = {'configurable': {'thread_id': session_id}}
        self.graph.invoke({'messages': [('user', query)]}, config)
        return self.get_agent_response(config)

    async def stream(
        self, query, sessionId, task_id
    ) -> AsyncIterable[dict[str, Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': sessionId}}

        logger.info(
            f'Running LanggraphPlannerAgent stream for session {sessionId} {task_id} with input {query}'
        )

        for item in self.graph.stream(inputs, config, stream_mode='values'):
            message = item['messages'][-1]
            if isinstance(message, AIMessage):
                yield {
                    'response_type': 'text',
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': message.content,
                }
        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if (
                structured_response.status == 'input_required'
                # and structured_response.content.tasks
            ):
                return {
                    'response_type': 'text',
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.question,
                }
            if structured_response.status == 'error':
                return {
                    'response_type': 'text',
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.question,
                }
            if structured_response.status == 'completed':
                return {
                    'response_type': 'data',
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.content.model_dump(),
                }
        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.',
        }
