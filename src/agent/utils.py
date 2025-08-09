"""Utility functions for the data enrichment agent."""

import os
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_openai import ChatOpenAI

from .configuration import Configuration


def init_model(config: Optional[RunnableConfig] = None) -> Any:
    """Initialize the language model based on configuration.

    Args:
        config: Optional configuration object containing model settings.

    Returns:
        The initialized language model.
    """
    config = ensure_config(config)
    configuration = Configuration.from_runnable_config(config)
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize OpenAI model
    model = ChatOpenAI(
        model="gpt-4o-mini",  # Using gpt-4o-mini as default
        api_key=openai_api_key,
        temperature=0.1
    )
    
    return model
