# agent/modules/websearch/main.py
"""
Web Search Module for the Local Multimodal LLM Agent.

This module simulates the functionality of performing a web search based on a query.
It's designed to be used by the agent when information is likely to be found on
the public internet, especially for current events or topics not covered by
local files or specialized knowledge bases.

Currently, this is a placeholder implementation and does not make actual external
HTTP requests. It returns mock search results for specific queries.
"""

from typing import Dict, Any, List

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates performing a web search based on a query string.

    This function is the entry point for the web search module. It expects an
    `input_data` dictionary containing a 'query' key with the search string.

    The current simulation returns predefined mock search results (including title,
    link, and snippet) if specific keywords like "ollama python agent" or "weather"
    are found in the query. It does not interact with any real search engines.

    Args:
        input_data (Dict[str, Any]): A dictionary containing the input for the tool.
            Expected keys:
            - "query" (str): The search term or question to search on the web.

    Returns:
        Dict[str, Any]: A dictionary containing the results of the simulated search.
            Includes:
            - "status" (str): A message indicating the outcome of the operation.
            - "query_received" (str): The original query string received.
            - "search_results" (List[Dict[str, str]]): A list of dictionaries, where each
              dictionary represents a mock search result with "title", "link", and
              "snippet" keys.
            - "summary" (str): A human-readable summary of the search operation.
            - "error" (str, optional): An error message if the query is missing.
    """
    query = input_data.get('query')
    # print(f"[Web Search Tool] Received query: '{query}'") # Verbose

    if not query:
        return {"error": "No query provided for web search.", "search_results": [], "status": "Error - No query"}

    # Simulate finding some web results
    # In a real implementation, this would involve using a search engine API or web scraping libraries.
    mock_search_results: List[Dict[str, str]] = []
    query_lower = query.lower()

    if "ollama python agent" in query_lower:
        mock_search_results.extend([
            {
                "title": "Building a Local LLM Agent with Ollama and Python - Example Guide",
                "link": "https://example.com/ollama-python-agent-guide",
                "snippet": "Step-by-step guide to create a local agent using Ollama models in Python..."
            },
            {
                "title": "GitHub - ollama-python-toolkit",
                "link": "https://github.com/example/ollama-python-toolkit",
                "snippet": "A Python toolkit for interacting with Ollama models, including examples for agents..."
            }
        ])
    elif "weather" in query_lower:
        location_parts = query_lower.split("in ", 1) # Split only on the first "in "
        location = location_parts[1].strip() if len(location_parts) > 1 else "your current area"
        mock_search_results.append({
            "title": f"Weather forecast for {location.capitalize()}",
            "link": f"https://example.com/weather/{location.replace(' ', '_')}",
            "snippet": f"The weather in {location.capitalize()} is expected to be sunny with a high of 25°C. (Simulated)"
        })
    elif "ai safety" in query_lower:
        mock_search_results.append({
            "title": "Recent Developments in AI Safety Research - Reputable Source",
            "link": "https://example.com/ai-safety-news-q3-2024",
            "snippet": "A summary of key advancements and discussions in AI safety from the last quarter... (Simulated)"
        })
    
    if not mock_search_results:
        result_message = f"No relevant web results found for '{query}' in simulated search."
    else:
        result_message = f"Simulated web search found {len(mock_search_results)} results for '{query}'."

    # print(f"[Web Search Tool] Result: {result_message}") # Verbose
    return {
        "status": "Web search complete (simulated).",
        "query_received": query, # Return original case query
        "search_results": mock_search_results,
        "summary": result_message
    }

if __name__ == '__main__':
    """
    Example usage of the run function when the script is executed directly.
    Demonstrates how the simulated web search responds to different queries.
    """
    print("--- Testing Web Search Module (Simulated) ---")
    test_inputs = [
        {"query": "ollama python agent examples"},
        {"query": "latest news on AI safety"},
        {"query": "weather in Berlin"},
        {"query": "current stock price of ExampleCorp"}, # Should find nothing
        {"query": None} # Error case
    ]

    for i, test_input in enumerate(test_inputs):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Input: {test_input}")
        actual_input_for_run = test_input if test_input.get("query") is not None else {"query": None}
        output = run(actual_input_for_run)
        print(f"Output: {output}")
```
