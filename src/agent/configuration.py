"""Define the configurable parameters for the data enrichment agent."""

from __future__ import annotations

from typing import Annotated, Optional, Any, Dict

from langchain_core.runnables import RunnableConfig, ensure_config

from . import prompts


class Configuration:
    """The configuration for the data enrichment agent.
    
    This class uses a flexible approach to handle any parameters that LangGraph 0.4.8+ 
    might inject, preventing constructor errors while maintaining functionality.
    """

    def __init__(self, **kwargs):
        """Initialize configuration with flexible parameter handling.
        
        Args:
            **kwargs: Any parameters, including those injected by LangGraph
        """
        # Extract known configuration fields with defaults
        self.thread_id = kwargs.get('thread_id')
        self.host = kwargs.get('host')
        self.connection = kwargs.get('connection')  # Handle the 'connection' parameter
        
        # Model configuration
        self.model = kwargs.get('model', 'openai/gpt-4o-mini')
        
        # Prompt configuration
        self.prompt = kwargs.get('prompt', prompts.MAIN_PROMPT)
        
        # Search configuration
        self.max_search_results = kwargs.get('max_search_results', 10)
        
        # Tool configuration
        self.max_info_tool_calls = kwargs.get('max_info_tool_calls', 3)
        
        # Loop configuration
        self.max_loops = kwargs.get('max_loops', 6)
        
        # Store any unknown parameters that LangGraph might inject
        known_fields = {
            'thread_id', 'host', 'connection', 'model', 'prompt', 
            'max_search_results', 'max_info_tool_calls', 'max_loops'
        }
        self._extra_params = {k: v for k, v in kwargs.items() if k not in known_fields}

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Load configuration w/ defaults for the given invocation."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        
        # Pass all parameters directly to the flexible constructor
        # The __init__ method will handle filtering and storage
        return cls(**configurable)
