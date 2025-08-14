"""Unit tests for state management."""

import pytest
from agent.state import State, InputState, OutputState


class TestState:
    """Test State class functionality."""

    def test_state_initialization(self):
        """Test state initialization with basic parameters."""
        schema = {"artist_name": {"type": "string"}}
        state = State(topic="David Bowie", extraction_schema=schema)
        
        assert state.topic == "David Bowie"
        assert state.extraction_schema == schema
        assert state.messages == []
        assert state.loop_step == 0
        assert state.info is None

    def test_state_with_info(self):
        """Test state initialization with existing info."""
        schema = {"artist_name": {"type": "string"}}
        info = {"artist_name": "David Bowie"}
        state = State(topic="David Bowie", extraction_schema=schema, info=info)
        
        assert state.info == info

    def test_state_message_accumulation(self):
        """Test that messages are properly accumulated."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        state = State(topic="test", extraction_schema={})
        
        # Add messages
        human_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi there")
        
        state.messages = [human_msg, ai_msg]
        
        assert len(state.messages) == 2
        assert state.messages[0] == human_msg
        assert state.messages[1] == ai_msg

    def test_state_loop_step_increment(self):
        """Test loop step increment functionality."""
        state = State(topic="test", extraction_schema={})
        
        assert state.loop_step == 0
        
        # Simulate loop increment
        state.loop_step = 1
        assert state.loop_step == 1


class TestInputState:
    """Test InputState class functionality."""

    def test_input_state_creation(self):
        """Test InputState creation."""
        schema = {"test": {"type": "string"}}
        input_state = InputState(topic="test topic", extraction_schema=schema)
        
        assert input_state.topic == "test topic"
        assert input_state.extraction_schema == schema
        assert input_state.info is None

    def test_input_state_with_info(self):
        """Test InputState with existing info."""
        schema = {"test": {"type": "string"}}
        info = {"test": "value"}
        input_state = InputState(topic="test", extraction_schema=schema, info=info)
        
        assert input_state.info == info


class TestOutputState:
    """Test OutputState class functionality."""

    def test_output_state_creation(self):
        """Test OutputState creation."""
        info = {"artist_name": "David Bowie", "genres": ["rock", "pop"]}
        output_state = OutputState(info=info)
        
        assert output_state.info == info

    def test_output_state_info_structure(self):
        """Test that OutputState info is properly structured."""
        info = {
            "artist_name": "David Bowie",
            "albums": ["Space Oddity", "Ziggy Stardust"],
            "genres": ["rock", "glam rock"]
        }
        output_state = OutputState(info=info)
        
        assert "artist_name" in output_state.info
        assert "albums" in output_state.info
        assert "genres" in output_state.info
        assert len(output_state.info["albums"]) == 2
