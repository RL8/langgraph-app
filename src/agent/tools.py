"""Tools for data enrichment.

This module contains functions that are directly exposed to the LLM as tools.
These tools can be used for tasks such as web searching and scraping.
Users can edit and extend these tools as needed.
"""

import json
import os
from typing import Any, Optional, cast

import aiohttp
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

from .configuration import Configuration
from .state import State
from .utils import init_model


async def search(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Query a search engine using Tavily.

    This function queries the web to fetch comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events. Provide as much context in the query as needed to ensure high recall.
    """
    configuration = Configuration.from_runnable_config(config)
    
    # Get Tavily API key from environment
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return [{"error": "TAVILY_API_KEY environment variable is required"}]
    
    try:
        # Use Tavily API directly
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {tavily_api_key}",
                "content-type": "application/json"
            }
            
            payload = {
                "query": query,
                "max_results": configuration.max_search_results,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False
            }
            
            async with session.post(
                "https://api.tavily.com/search",
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    
                    # Format results to match expected structure
                    formatted_results = []
                    for result in results:
                        formatted_results.append({
                            "title": result.get("title", ""),
                            "link": result.get("url", ""),
                            "snippet": result.get("content", ""),
                            "source": "Tavily"
                        })
                    
                    return formatted_results
                else:
                    error_text = await response.text()
                    return [{"error": f"Tavily API error: {response.status} - {error_text}"}]
                    
    except Exception as e:
        print(f"Search error: {e}")
        return [{"error": f"Search error: {str(e)}"}]


_INFO_PROMPT = """You are doing web research on behalf of a user. You are trying to find out this information:

<info>
{info}
</info>

You just scraped the following website: {url}

Based on the website content below, jot down some notes about the website.

<Website content>
{content}
</Website content>"""


async def scrape_website(
    url: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Scrape and summarize content from a given URL.

    Returns:
        str: A summary of the scraped content, tailored to the extraction schema.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                else:
                    return f"Failed to scrape website. Status code: {response.status}"
    except Exception as e:
        return f"Error scraping website: {str(e)}"

    p = _INFO_PROMPT.format(
        info=json.dumps(state.extraction_schema, indent=2),
        url=url,
        content=content[:40_000],
    )
    raw_model = init_model(config)
    result = await raw_model.ainvoke(p)
    return str(result.content)
