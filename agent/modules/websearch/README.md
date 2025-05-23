# Web Search Module

This module enables the agent to perform web searches to find information online.

## Functionality

The core purpose of this module is to take a search query and retrieve relevant information from the internet. This is crucial for answering questions about current events, public information not available locally, or when other specialized tools (like a local knowledge base) do not have the required details.

**Current Implementation (Simulated):**
The current `main.py` simulates web search functionality. It does not make any actual HTTP requests to external search engines. Instead, it returns a predefined set of mock search results if the query contains specific keywords (e.g., "ollama python agent", "weather"). This simulation is for testing the agent's ability to select and use this tool within its workflow.

## `AGENT.md`

The `AGENT.md` file for the web search module informs the `AgentController`'s LLM about its capabilities:
- **Tool Name:** "Web Search"
- **Description:** States that the tool performs web searches using a search engine.
- **When to use:** Guides the LLM to use this tool for queries needing current information, public data, or as a fallback if local/specialized tools fail.
- **Input Parameters:**
    - `query` (string, required): The search query string (e.g., "latest AI research papers").
- **Output:** A list of search results (typically title, link, snippet) or a summarized answer.

## `main.py`

The `main.py` script contains the tool's operational logic.

### `run(input_data: dict) -> dict` function:

- **Input (`input_data` dict):**
    - Expects a dictionary with a `"query"` key containing the search string.
- **Output (dict):**
    - Returns a dictionary with:
        - `status` (string): Outcome message (e.g., "Web search complete (simulated).").
        - `query_received` (string): The original search query.
        - `search_results` (list): A list of dictionaries, where each dictionary represents a mock search result and contains `"title"`, `"link"`, and `"snippet"` keys.
        - `summary` (string): A human-readable summary of the search operation.
        - `error` (string, optional): If an error occurs (e.g., no query provided).

### Standalone Execution:
Executing `python agent/modules/websearch/main.py` directly runs a test block defined in its `if __name__ == '__main__':` section, showcasing example inputs and their simulated outputs.

## Future Enhancements (for a real implementation):

- **Search Engine API Integration:** Use official APIs from search engines (e.g., Google Custom Search JSON API, Bing Web Search API) for robust and legal searching. This would require handling API keys and request quotas.
- **Web Scraping (Limited Use):** For very specific, simple cases, direct web scraping using libraries like `requests` and `BeautifulSoup` might be considered, but it's fragile and often against website terms of service.
- **Result Summarization:** Add a layer (potentially using another LLM call) to summarize the collected search results to provide a concise answer instead of just links.
- **Content Fetching:** Allow the tool to fetch and parse the content from the result URLs (respecting `robots.txt`).
- **Source Reliability:** Consider adding mechanisms to assess the reliability of search result sources.
