# Local Multimodal LLM Agent

This project implements a terminal-based local agent in Python that dynamically selects and orchestrates tools/modules to answer multimodal user queries. It is designed to work offline with local LLMs accessed via an Ollama server.

## Core Features

- **Local LLM Integration:** Utilizes Ollama to run language models (text and multimodal) locally.
- **Modular Tool System:** Extensible with tools (modules) that provide specific functionalities.
- **Dynamic Tool Selection:** Uses an LLM to analyze user queries and select the appropriate tool(s).
- **Pipeline Execution:** Manages sequences of tools, including data flow and fallback mechanisms.
- **CLI Interface:** Allows interaction with the agent via the command line.
- **Offline Capability:** Designed to operate without internet access by default (unless a specific tool requires it).

## Architecture

The agent follows a modular architecture centered around a `core` engine and pluggable `modules`.

```
agent/
├── agent.py                  # CLI Entry point
├── core/
│   ├── controller.py         # AgentController: Main orchestration logic
│   ├── model_adapters.py     # Adapters for Ollama models (DeepSeek, LLaVA)
│   ├── module_loader.py      # Discovers and loads tools from /modules
│   ├── pipeline.py           # Executes tool sequences with fallbacks
│   └── config.py             # Configuration (model names, paths)
├── modules/
│   ├── file_search/          # Example: Local file search tool
│   │   ├── main.py
│   │   └── AGENT.md
│   ├── websearch/            # Example: Web search tool
│   │   ├── main.py
│   │   └── AGENT.md
│   └── netz_bw_energy/       # Example: Simulated knowledge base tool
│       ├── main.py
│       └── AGENT.md
└── README.md                 # This file
```

### Key Components:

- **`agent.py`**: The main Command Line Interface (CLI) entry point. It parses arguments and invokes the `AgentController`.
- **`core/`**:
    - **`config.py`**: Stores static configuration like Ollama model names (e.g., `DEEPSEEK_MODEL`, `LLAVA_MODEL`), API URLs, and default directory names (e.g., `MODULES_DIR`).
    - **`model_adapters.py`**: Defines classes like `DeepSeekAdapter` and `LLaVAAdapter` that abstract the communication with specific Ollama models. They handle formatting requests and parsing responses from the Ollama API (typically `http://localhost:11434/api`).
    - **`module_loader.py` (`ModuleLoader`)**: Scans the `modules/` directory upon initialization. For each subdirectory representing a module, it looks for an `AGENT.md` file and a `main.py`. It parses `AGENT.md` to get a natural language description of the tool's capabilities, inputs, and outputs. It dynamically imports the `run` function from `main.py`.
    - **`pipeline.py` (`Pipeline`)**: Responsible for executing a sequence of tools as determined by the `AgentController`. It manages passing the output of one tool as input to the next. It also incorporates robust error handling, including the execution of predefined fallback tools if a primary tool in the sequence fails. The development of this component was done iteratively to ensure stability and features like detailed history logging.
    - **`controller.py` (`AgentController`)**: This is the brain of the agent. 
        1. It initializes all core components, including loading tools via `ModuleLoader`.
        2. When a user query is received, it prepares a prompt for a reasoning LLM (e.g., DeepSeek). This prompt includes the user's query and the descriptions of all available tools.
        3. It interprets the LLM's response to select an appropriate sequence of tools (and potentially parameters, though this is simplified in the current version).
        4. It instructs the `Pipeline` to execute this sequence.
        5. It formats the final result from the pipeline for presentation to the user. If no tools are selected, it may use the LLM to provide a direct answer.
- **`modules/`**: Each subdirectory is a self-contained tool.
    - **`main.py`**: Must expose a `run(input_data: dict) -> dict` function. This function contains the tool's operational logic and is what the `Pipeline` executes.
    - **`AGENT.md`**: Crucial for tool discovery and selection. It tells the `AgentController`'s LLM what the tool does, when to use it, what inputs it expects, and what outputs it produces. This allows the LLM to make informed decisions about tool usage.

### Example Modules Provided:

- **`file_search`**: (Simulated) A tool designed to search local files for keywords. Its `AGENT.md` would guide the LLM to use it for queries about local documents.
- **`websearch`**: (Simulated) A tool for performing web searches. Its `AGENT.md` suggests its use for current information or topics not covered by other tools.
- **`netz_bw_energy`**: (Simulated) Queries a specialized knowledge base for information about Netze BW energy topics. This acts as a placeholder for a more complex RAG (Retrieval Augmented Generation) system. The `AGENT.md` directs the LLM to try this tool first for relevant queries.

## Setup

1.  **Prerequisites:**
    *   Python 3.8+ recommended.
    *   Ollama server installed and running. Verify by opening `http://localhost:11434` in your browser or using `ollama list`.
    *   Required Ollama models pulled. The defaults in `config.py` are `deepseek-coder:6.7b` (for text reasoning) and `llava:7b` (for multimodal tasks, though image handling is not fully implemented in the controller yet). Adjust `config.py` if you use different models.
        ```bash
        ollama pull deepseek-coder:6.7b
        ollama pull llava:7b
        ```
    *   Python dependencies: The primary external dependency is `requests` for Ollama API calls. Other standard libraries like `os`, `sys`, `argparse`, `json`, `base64`, `importlib` are used.
        ```bash
        pip install requests
        # Pillow is used by model_adapters.py for creating dummy images during its __main__ test block.
        # It's not strictly required for the agent's main operation if not running that specific test.
        # pip install Pillow 
        ```

2.  **Project Structure:**
    Clone or download the project and ensure the directory structure is maintained as outlined above. The agent's internal imports and module loading rely on this structure.

## Running the Agent

The agent is run from the command line using `agent.py` located in the root `agent/` directory.

**Syntax:**
```bash
python agent.py --prompt "Your query here" [--image "path/to/image.png"] [--verbose]
```

**Command-line arguments:**

- `--prompt "TEXT"` (required): The text prompt for the agent.
- `--image "PATH"` (optional): Path to an image file. (Note: Image data processing is a planned enhancement in the controller).
- `--verbose` (optional): Enables detailed output, including the step-by-step execution history from the pipeline, showing inputs, outputs, and statuses for each tool, including fallbacks.

**Example Usage:**

1.  **Querying the simulated Netze BW knowledge base:**
    ```bash
    python agent.py --prompt "What is the residential electricity price from Netze BW?"
    ```

2.  **Performing a simulated web search:**
    ```bash
    python agent.py --prompt "ollama python agent examples"
    ```

3.  **Query with verbose output to see tool execution:**
    ```bash
    python agent.py --prompt "Search for annual financial reports and summarize them" --verbose
    ```
    *(This might trigger `file_search` or `websearch` based on LLM's interpretation and available (simulated) results.)*

## How it Works (Detailed Flow)

1.  **CLI Interaction**: User executes `agent.py` with a prompt (e.g., "What are Netze BW's energy costs?") and optional arguments.
2.  **Controller Initialization**: `agent.py` instantiates `AgentController`. The controller, in its `__init__`:
    a.  Initializes `ModuleLoader`, which scans `agent/modules/`, loads all valid modules, and parses their `AGENT.md` files for descriptions.
    b.  Initializes `DeepSeekAdapter` (and other model adapters as needed).
    c.  Initializes the `Pipeline`.
    d.  Prepares a consolidated string of tool descriptions for use in LLM prompts.
3.  **Query Handling**: `AgentController.handle_query()` is called.
    a.  **Tool Selection**: The controller constructs a detailed prompt for the `DeepSeekAdapter`. This prompt includes the user's query and the formatted descriptions of all available tools. The LLM's task is to determine which tool(s) are most appropriate for the query and in what order. The controller parses the LLM's textual response (e.g., a comma-separated list of tool names) to form a `tool_sequence`.
    b.  **Fallback Configuration (Simplified)**: Basic fallback rules might be applied (e.g., if 'websearch' is selected, 'file_search' could be added as its fallback).
    c.  **Pipeline Execution**: If a valid tool sequence is identified, the controller invokes `Pipeline.execute()`, passing the sequence and an initial input dictionary (often containing the original user prompt and other relevant data).
    d.  **Tool Execution**: The `Pipeline` iterates through the `tool_sequence`:
        i.  For each tool, it calls the `run()` method of the corresponding module's `main.py`.
        ii. The output of one tool becomes the input for the next.
        iii. If a tool fails, the pipeline checks for a defined fallback. If available and valid, the fallback is executed. If the fallback also fails or is not defined/valid, the pipeline usually stops for that sequence path.
        iv. A detailed history of each step (inputs, outputs, status, fallback attempts) is recorded.
    e.  **No Tools Selected**: If the LLM determines no tools are suitable, the `AgentController` may use the `DeepSeekAdapter` to generate a direct response to the user's query.
4.  **Response Generation**: The `AgentController` receives the result from the `Pipeline` (or the direct LLM response). This result includes the final output data, an overall status, and the execution history.
5.  **Output to CLI**: `agent.py` prints the formatted response and, if `--verbose` is used, the detailed execution history.

## Future Enhancements & Considerations

- **Real RAG Implementation:** Transition the `netz_bw_energy` module (or a renamed `knowledge_base_retriever`) from a simulation to a full RAG system using a vector database (e.g., FAISS, ChromaDB) for semantic search and a backend database for detailed information retrieval. This was a user suggestion and is a high-impact next step.
- **Multimodal Input Processing:** Fully implement the use of image data passed via the `--image` argument. This would involve using the `LLaVAAdapter` in the `AgentController` to process the image and text prompt together, potentially to generate a richer internal prompt or to guide tool selection and execution.
- **Advanced Tool Selection & Parameterization:** Enhance the LLM prompting strategy and response parsing in `AgentController` to allow for more sophisticated tool chaining, conditional logic, and the LLM suggesting specific parameters for tools based on the query.
- **Dynamic Fallback Strategies:** Allow the LLM to suggest fallback tools or have more configurable fallback chains rather than mostly hardcoded ones.
- **Error Handling and Resilience:** Implement more granular error handling within tools and the pipeline to allow for more graceful degradation or recovery paths.
- **Configuration Management:** Introduce a more robust configuration system (e.g., using YAML or environment variables) for models, API keys (if tools use external services), and module-specific settings.
- **Security for External Tools:** If modules are extended to access external APIs or execute system commands, rigorous security reviews and sandboxing techniques will be essential.
- **State Management & Conversational Memory:** For multi-turn conversations, implement state management to retain context and memory across interactions.
- **Asynchronous Operations:** For tools that involve long-running I/O operations (like complex API calls), consider an asynchronous execution model.
