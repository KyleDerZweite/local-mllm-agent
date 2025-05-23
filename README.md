# Local Multimodal LLM Agent

Local Multimodal LLM Agent in Python – orchestriert verschiedene Ollama‑Modelle (z.B. LLava‑7b für Bilder, deepseek‑7b für Text) in einem modularen Pipeline‑Framework.

## Overview

This project implements a terminal-based local agent in Python that dynamically selects and orchestrates tools/modules to answer multimodal user queries. It is designed to work offline with local LLMs via Ollama.

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
├── agent.py # CLI Entry point 
├── core/ 
│ ├── controller.py # AgentController: Main orchestration logic 
│ ├── model_adapters.py # Adapters for Ollama models (DeepSeek, LLaVA) 
│ ├── module_loader.py # Discovers and loads tools from /modules 
│ ├── pipeline.py # Executes tool sequences with fallbacks 
│ └── config.py # Configuration (model names, paths) 
├── modules/ 
│ ├── file_search/ # Example: Local file search tool 
│ │ ├── main.py 
│ │ └── AGENT.md 
│ ├── websearch/ # Example: Web search tool 
│ │ ├── main.py 
│ │ └── AGENT.md 
│ └── netz_bw_energy/ # Example: Simulated knowledge base tool 
│ ├── main.py 
│ └── AGENT.md 
└── README.md # Detailed documentation
```

## Code

For more detailed information on setup, usage, and the internal workings of the agent, please refer to the [agent/README.md](agent/README.md).

## Setup

1. **Prerequisites:**
   * Python 3.8+ recommended.
   * Ollama server installed and running. Verify by opening `http://localhost:11434` in your browser or using `ollama list`.
   * Required Ollama models pulled:
     ```bash
     ollama pull deepseek-coder:6.7b
     ollama pull llava:7b
     ```
   * Python dependencies:
     ```bash
     pip install requests
     ```

2. **Project Structure:**
   Clone or download the project and ensure the directory structure is maintained as outlined above. The agent's internal imports and module loading rely on this structure.

## Running the Agent

```bash
python agent/agent.py --prompt "Your query here" [--image "path/to/image.png"] [--verbose]
```

## Future Plans & Vision
This project aims to evolve beyond its current CLI implementation to provide more comprehensive local LLM capabilities:

## Short-Term Plans
- Full RAG Implementation: Replace the simulated knowledge base with a real vector database implementation (using FAISS, Chroma, or similar).
- Complete Multimodal Support: Improve image processing capabilities with the LLaVA model.
- Advanced Tool Chaining: Enhance the tool selection logic to support more complex workflows and conditional execution.
## Mid-Term Vision
- Flow-Based Web Interface: Develop a web-based UI that allows users to:
  - Visually design and edit agent tool pipelines
  - Monitor execution flow in real-time
  - Save and share custom pipelines
  - Drag-and-drop modules into workflows
- Dashboard & Analytics: Create a visual dashboard showing:
  - Usage statistics and performance metrics
  - Model comparison tools
  - Execution timelines
- Extended Module Library: Build a broader collection of specialized tools for various domains.

## Long-Term Aspirations
- Collaborative Multi-Agent Systems: Enable multiple specialized agents to work together on complex tasks.
- Fine-Tuning Interface: Provide tools for users to easily fine-tune local models for specific domains.
- Cross-Platform Support: Extend beyond CLI to native desktop and mobile applications.
- IoT & Home Automation Integration: Connect with smart home devices and systems.

## Contributing
Contributions to any aspect of the project are welcome! Whether you want to improve the core agent functionality, develop new modules, or work on the planned web interface, please feel free to submit issues and pull requests.

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details.
