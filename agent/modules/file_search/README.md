# File Search Module

This module provides the agent with the capability to search for files on the local system.

## Functionality

The primary function of this module is to find files based on a user's query. This can involve searching by filename or, in a more advanced implementation, searching within the content of files for specific keywords or phrases.

**Current Implementation (Simulated):**
The current `main.py` simulates this functionality. It does not perform actual file system searches. Instead, it returns a predefined list of mock file paths if certain keywords (e.g., "report", "data") are present in the search query. This allows for testing the agent's tool selection and pipeline execution flow involving this module without actual file system dependencies.

## `AGENT.md`

The `AGENT.md` file for this module is crucial for the `AgentController`'s LLM to understand its purpose. It specifies:
- **Tool Name:** "File Search"
- **Description:** What the tool does (searches local files).
- **When to use:** Guidelines for the LLM on when to select this tool (e.g., when the user asks to find local files, check for documents, or search within local documents).
- **Input Parameters:**
    - `query` (string, required): Keywords or search terms.
    - `directory` (string, optional): Specific directory to search. Defaults to `./documents_test` in the simulation.
- **Output:** A list of matching file paths or a summary.

## `main.py`

The `main.py` script implements the core logic of the tool.

### `run(input_data: dict) -> dict` function:

- **Input (`input_data` dict):**
    - Expects a dictionary containing at least a `"query"` key with the search string.
    - Optionally, it can include a `"directory"` key to specify the search path.
- **Output (dict):**
    - Returns a dictionary containing:
        - `status` (string): A message indicating the outcome (e.g., "File search complete (simulated).").
        - `query_received` (string): The original query.
        - `directory_searched` (string): The directory that was targeted for the search.
        - `files_found` (list): A list of strings, where each string is a path to a (mock) found file.
        - `summary` (string): A human-readable summary of the search results.
        - `error` (string, optional): If an error occurs (e.g., no query provided).

### Standalone Execution:
Running `python agent/modules/file_search/main.py` directly will execute a small test block defined in its `if __name__ == '__main__':` section, demonstrating basic usage and output.

## Future Enhancements (for a real implementation):

- Implement actual file system traversal using `os.walk` or `glob`.
- Add content searching capabilities for various file types (e.g., .txt, .pdf, .docx) using appropriate parsing libraries.
- Implement more sophisticated keyword matching and ranking of results.
- Allow configuration of default search directories and excluded paths.
