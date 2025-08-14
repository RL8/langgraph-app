"""Unit tests for agent graph functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from agent.graph import call_agent_model, check_info_satisfactory, route_after_agent, route_after_checker
from agent.state import State


class TestCallAgentModel:
    """Test call_agent_model function."""

    @pytest.mark.asyncio
    async def test_call_agent_model_with_tool_calls(self):
        """Test agent model with tool calls."""
        # Mock state
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema)
        
        # Mock LLM response with tool calls
        from langchain_core.tools import ToolCall
        mock_response = AIMessage(
            content="I'll search for information",
            tool_calls=[ToolCall(id="1", name="search", args={"query": "David Bowie"})]
        )
        
        with patch('agent.graph.init_model') as mock_init_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = mock_response
            mock_init_model.return_value.bind_tools.return_value = mock_model
            
            result = await call_agent_model(state)
            
            assert "messages" in result
            assert len(result["messages"]) > 0
            assert result["messages"][0] == mock_response

    @pytest.mark.asyncio
    async def test_call_agent_model_with_info_submission(self):
        """Test agent model submitting final info."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema)
        
        # Mock LLM response with Info tool call
        from langchain_core.tools import ToolCall
        mock_response = AIMessage(
            content="Here's the information",
            tool_calls=[ToolCall(id="1", name="Info", args={"artist_name": "David Bowie"})]
        )
        
        with patch('agent.graph.init_model') as mock_init_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = mock_response
            mock_init_model.return_value.bind_tools.return_value = mock_model
            
            result = await call_agent_model(state)
            
            assert "messages" in result
            # Should filter to only Info tool call
            assert len(result["messages"][0].tool_calls) == 1
            assert result["messages"][0].tool_calls[0].name == "Info"

    @pytest.mark.asyncio
    async def test_call_agent_model_no_tool_calls(self):
        """Test agent model when no tool calls are made."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema)
        
        # Mock LLM response without tool calls
        mock_response = AIMessage(content="I need to use tools")
        
        with patch('agent.graph.init_model') as mock_init_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = mock_response
            mock_init_model.return_value.bind_tools.return_value = mock_model
            
            result = await call_agent_model(state)
            
            assert "messages" in result
            assert len(result["messages"]) == 2  # Original + reminder message


class TestCheckInfoSatisfactory:
    """Test check_info_satisfactory function."""

    @pytest.mark.asyncio
    async def test_check_info_satisfactory_with_info(self):
        """Test info satisfaction check with existing info."""
        schema = {"artist_name": {"type": "string"}}
        info = {"artist_name": "David Bowie", "genres": ["rock"]}
        state = State(topic="David Bowie", extraction_schema=schema, info=info)
        
        with patch('agent.graph.init_model') as mock_init_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = "Mock evaluation response"
            mock_init_model.return_value = mock_model
            
            result = await check_info_satisfactory(state)
            
            assert "reason" in result
            assert "is_satisfactory" in result
            assert result["is_satisfactory"] is True

    @pytest.mark.asyncio
    async def test_check_info_satisfactory_no_info(self):
        """Test info satisfaction check with no info."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema, info=None)
        
        with patch('agent.graph.init_model') as mock_init_model:
            mock_model = AsyncMock()
            mock_model.ainvoke.return_value = "Mock evaluation response"
            mock_init_model.return_value = mock_model
            
            result = await check_info_satisfactory(state)
            
            assert "reason" in result
            assert "is_satisfactory" in result
            assert result["is_satisfactory"] is False


class TestRoutingFunctions:
    """Test routing functions."""

    def test_route_after_agent_with_info(self):
        """Test routing when info is available."""
        schema = {"artist_name": {"type": "string"}}
        info = {"artist_name": "David Bowie"}
        state = State(topic="David Bowie", extraction_schema=schema, info=info)
        
        result = route_after_agent(state)
        assert result == "reflect"

    def test_route_after_agent_with_tool_calls(self):
        """Test routing when tool calls are present."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema)
        
        # Add message with tool calls
        from langchain_core.tools import ToolCall
        ai_message = AIMessage(
            content="I'll search",
            tool_calls=[ToolCall(id="1", name="search", args={"query": "test"})]
        )
        state.messages = [ai_message]
        
        result = route_after_agent(state)
        assert result == "tools"

    def test_route_after_agent_default(self):
        """Test default routing."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema)
        
        result = route_after_agent(state)
        assert result == "call_agent_model"

    def test_route_after_checker_with_info(self):
        """Test routing after checker with info."""
        schema = {"artist_name": {"type": "string"}}
        info = {"artist_name": "David Bowie"}
        state = State(topic="David Bowie", extraction_schema=schema, info=info)
        
        result = route_after_checker(state, {})
        assert result == "__end__"

    def test_route_after_checker_no_info(self):
        """Test routing after checker without info."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema, info=None)
        
        result = route_after_checker(state, {})
        assert result == "call_agent_model"
