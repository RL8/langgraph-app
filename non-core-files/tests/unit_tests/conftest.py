"""Shared test fixtures for unit tests."""

import pytest
from agent.state import State


@pytest.fixture
def sample_state():
    """Provide a sample state for testing."""
    schema = {
        "artist_name": {"type": "string"},
        "genres": {"type": "array", "items": {"type": "string"}},
        "key_albums": {"type": "array", "items": {"type": "string"}}
    }
    return State(topic="David Bowie", extraction_schema=schema)


@pytest.fixture
def sample_state_with_info():
    """Provide a sample state with existing info."""
    schema = {
        "artist_name": {"type": "string"},
        "genres": {"type": "array", "items": {"type": "string"}},
        "key_albums": {"type": "array", "items": {"type": "string"}}
    }
    info = {
        "artist_name": "David Bowie",
        "genres": ["rock", "glam rock"],
        "key_albums": ["Space Oddity", "Ziggy Stardust"]
    }
    return State(topic="David Bowie", extraction_schema=schema, info=info)


@pytest.fixture
def mock_llm_response():
    """Provide a mock LLM response."""
    from langchain_core.messages import AIMessage
    return AIMessage(
        content="I'll search for information about David Bowie",
        tool_calls=[{"name": "search", "args": {"query": "David Bowie"}}]
    )


@pytest.fixture
def mock_info_response():
    """Provide a mock LLM response with Info tool call."""
    from langchain_core.messages import AIMessage
    return AIMessage(
        content="Here's the information I found",
        tool_calls=[{"name": "Info", "args": {"artist_name": "David Bowie"}}]
    )


@pytest.fixture
def sample_search_results():
    """Provide sample search results."""
    return {
        "results": [
            {
                "title": "David Bowie - Wikipedia",
                "url": "https://en.wikipedia.org/wiki/David_Bowie",
                "snippet": "David Bowie was a British musician and actor."
            },
            {
                "title": "David Bowie Albums",
                "url": "https://example.com/bowie-albums",
                "snippet": "Complete discography of David Bowie."
            }
        ]
    }


@pytest.fixture
def sample_scraped_content():
    """Provide sample scraped website content."""
    return {
        "content": """
        <html>
            <head><title>David Bowie</title></head>
            <body>
                <h1>David Bowie</h1>
                <p>David Bowie was a British musician and actor.</p>
                <ul>
                    <li>Space Oddity (1969)</li>
                    <li>Ziggy Stardust (1972)</li>
                </ul>
            </body>
        </html>
        """,
        "title": "David Bowie",
        "extracted_text": "David Bowie was a British musician and actor. Space Oddity (1969) Ziggy Stardust (1972)"
    }
