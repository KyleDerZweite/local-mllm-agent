# Tool: Web Search

This tool performs a web search using a search engine to find information online.

## When to use:

Use this tool when the user's prompt requires:
- Finding current information (e.g., news, recent events).
- Answering questions about topics not likely covered by local files or specialized knowledge bases.
- Looking up publicly available information on companies, people, or general subjects.
- When other tools (like local file search or specific knowledge bases) fail to find the answer and the information might be on the public internet.

## Input Parameters:

- `query` (string, required): The search query string (e.g., "latest AI research papers", "weather in London today").

## Output:

- A list of search results, typically including titles, URLs (links), and short snippets of text from the search results.
- Or, a summarized answer if the tool is capable of extracting and synthesizing information from the search results.
- If the search yields no relevant results, it will indicate that.
