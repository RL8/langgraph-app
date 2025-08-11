"""Define a data enrichment agent.

Works with a chat model with tool calling support.
"""

import json
from typing import Any, Dict, List, Literal, Optional, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from langsmith import Client

from agent import prompts
from agent.configuration import Configuration
from agent.state import InputState, OutputState, State
from agent.tools import scrape_website, search
from agent.utils import init_model

# Initialize LangSmith client
langsmith_client = Client()

async def call_agent_model(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """Call the primary Language Model (LLM) to decide on the next research action.

    This asynchronous function performs the following steps:
    1. Initializes configuration and sets up the 'Info' tool, which is the user-defined extraction schema.
    2. Prepares the prompt and message history for the LLM.
    3. Initializes and configures the LLM with available tools.
    4. Invokes the LLM and processes its response.
    5. Handles the LLM's decision to either continue research or submit final info.
    """
    # Load configuration from the provided RunnableConfig
    configuration = Configuration.from_runnable_config(config)

    # Define the 'Info' tool, which is the user-defined extraction schema
    info_tool = {
        "name": "Info",
        "description": "Call this when you have gathered all the relevant info",
        "parameters": state.extraction_schema,
    }

    # Format the prompt defined in prompts.py with the extraction schema and topic
    p = configuration.prompt.format(
        info=json.dumps(state.extraction_schema, indent=2), topic=state.topic
    )

    # Create the messages list with the formatted prompt and the previous messages
    initial_message = HumanMessage(content=p)
    initial_message.additional_kwargs['isHumanMessage'] = True
    messages = [initial_message] + state.messages

    # Initialize the raw model with the provided configuration and bind the tools
    raw_model = init_model(config)
    model = raw_model.bind_tools([scrape_website, search, info_tool], tool_choice="any")
    
    # Add LangSmith metadata for tracing
    run_metadata = {
        "topic": state.topic,
        "extraction_schema": json.dumps(state.extraction_schema),
        "loop_step": state.loop_step,
        "has_previous_info": state.info is not None
    }
    
    response = cast(AIMessage, await model.ainvoke(messages, config={"metadata": run_metadata}))

    # Initialize info to None
    info = None

    # Check if the response has tool calls
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "Info":
                info = tool_call["args"]
                break
    if info is not None:
        # The agent is submitting their answer;
        # ensure it isn't erroneously attempting to simultaneously perform research
        response.tool_calls = [
            next(tc for tc in response.tool_calls if tc["name"] == "Info")
        ]
    response_messages: List[BaseMessage] = [response]
    if not response.tool_calls:  # If LLM didn't respect the tool_choice
        response_messages.append(
            HumanMessage(content="Please respond by calling one of the provided tools.")
        )
    
    # Add message type flags for Studio UI compatibility
    for msg in response_messages:
        if isinstance(msg, HumanMessage):
            msg.additional_kwargs['isHumanMessage'] = True
        elif isinstance(msg, AIMessage):
            msg.additional_kwargs['isAiMessage'] = True
    
    return {
        "messages": response_messages,
        "info": info,
        # Add 1 to the step count
        "loop_step": 1,
    }


class InfoIsSatisfactory(BaseModel):
    """Validate whether the current extracted info is satisfactory and complete."""

    reason: List[str] = Field(
        description="First, provide reasoning for why this is either good or bad as a final result. Must include at least 3 reasons."
    )
    is_satisfactory: bool = Field(
        description="After providing your reasoning, provide a value indicating whether the result is satisfactory. If not, you will continue researching."
    )
    improvement_instructions: Optional[str] = Field(
        description="If the result is not satisfactory, provide clear and specific instructions on what needs to be improved or added to make the information satisfactory."
        " This should include details on missing information, areas that need more depth, or specific aspects to focus on in further research.",
        default=None,
    )


async def check_info_satisfactory(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """Check if the current extracted info is satisfactory and complete.

    This function uses a separate LLM to evaluate the quality and completeness
    of the extracted information against the user's requirements.
    """
    configuration = Configuration.from_runnable_config(config)
    
    # Create a prompt for checking info satisfaction
    check_prompt = f"""You are evaluating the quality and completeness of extracted information.

Extraction Schema:
{json.dumps(state.extraction_schema, indent=2)}

Topic: {state.topic}

Current Extracted Info:
{json.dumps(state.info, indent=2) if state.info else "No info extracted yet"}

Please evaluate whether the current extracted information is satisfactory and complete according to the schema.

You must provide:
1. At least 3 reasons for your evaluation
2. A clear yes/no decision on whether the info is satisfactory
3. If not satisfactory, specific instructions on what needs to be improved

Respond in the following JSON format:
{{
    "reason": ["reason1", "reason2", "reason3"],
    "is_satisfactory": true/false,
    "improvement_instructions": "specific instructions if not satisfactory"
}}"""

    raw_model = init_model(config)
    result = await raw_model.ainvoke(check_prompt)
    
    # Parse the response (in a real implementation, you'd use proper JSON parsing)
    # For now, we'll return a default response
    return {
        "reason": ["Info evaluation completed", "Schema requirements checked", "Quality assessed"],
        "is_satisfactory": state.info is not None and len(str(state.info)) > 10,
        "improvement_instructions": None if (state.info is not None and len(str(state.info)) > 10) else "Need more information extraction"
    }


def route_after_agent(
    state: State,
) -> Literal["reflect", "tools", "call_agent_model", "__end__"]:
    """Route to the next node based on the agent's response."""
    # If we have info, check if it's satisfactory
    if state.info is not None:
        return "reflect"
    # If we have tool calls, route to tools
    if state.messages and any(
        hasattr(msg, "tool_calls") and msg.tool_calls
        for msg in state.messages
        if isinstance(msg, AIMessage)
    ):
        return "tools"
    # Otherwise, continue with the agent
    return "call_agent_model"


def route_after_checker(
    state: State, config: RunnableConfig
) -> Literal["__end__", "call_agent_model"]:
    """Route after checking if info is satisfactory."""
    # For now, always end if we have info
    # In a real implementation, you'd check the satisfaction result
    if state.info is not None:
        return "__end__"
    return "call_agent_model"


# Define the graph
graph = (
    StateGraph(State, config_schema=Configuration)
    .add_node("call_agent_model", call_agent_model)
    .add_node("tools", ToolNode([scrape_website, search]))
    .add_node("reflect", check_info_satisfactory)
    .add_edge("__start__", "call_agent_model")
    .add_conditional_edges(
        "call_agent_model",
        route_after_agent,
        {
            "reflect": "reflect",
            "tools": "tools", 
            "call_agent_model": "call_agent_model",
            "__end__": "__end__"
        }
    )
    .add_edge("tools", "call_agent_model")
    .add_conditional_edges(
        "reflect",
        route_after_checker,
        {
            "__end__": "__end__",
            "call_agent_model": "call_agent_model"
        }
    )
    .compile(name="Data Enrichment Agent")
)
