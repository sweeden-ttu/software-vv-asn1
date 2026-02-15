"""This module provides example tools for web scraping and search functionality.

It includes a DuckDuckGo search function (free alternative to Tavily)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, Optional

from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.runtime import get_runtime

from react_agent.context import Context


async def search(query: str) -> Optional[str]:
    """Search for general web results using DuckDuckGo.

    This function performs a search using the DuckDuckGo search engine, which is a
    free alternative that doesn't require an API key. It's useful for answering
    questions about current events and general web searches.
    
    Args:
        query: The search query string.
    """
    runtime = get_runtime(Context)
    max_results = runtime.context.max_search_results
    
    # DuckDuckGo search tool
    search_tool = DuckDuckGoSearchRun()
    
    # Perform the search - DuckDuckGo returns a string with results
    try:
        results = await search_tool.ainvoke(query)
        return results
    except Exception as e:
        return f"Search error: {str(e)}"


TOOLS: List[Callable[..., Any]] = [search]
