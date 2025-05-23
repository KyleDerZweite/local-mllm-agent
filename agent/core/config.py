# agent/core/config.py
"""
Configuration settings for the Local Multimodal LLM Agent.

This file stores constants used throughout the agent, such as Ollama model names,
API endpoints, and default directory paths. Centralizing configuration here
makes it easier to manage and update settings without modifying core logic.
"""

# === Ollama Model Names ===
# These are the default model identifiers for the Ollama service.
# Ensure these models are pulled and available in your Ollama instance (e.g., via `ollama pull <model_name>`).

DEEPSEEK_MODEL = "deepseek-coder:6.7b"  # Used for text-based reasoning, tool selection, and direct answers.
LLAVA_MODEL = "llava:7b"                 # Used for multimodal queries involving images (currently planned for full integration).

# === Default Paths ===
# Specifies the default directory name for agent modules.
# This path is typically relative to the agent's root directory (e.g., 'agent/modules').
MODULES_DIR = "modules"

# === API Endpoints ===
# Base URL for the Ollama API. The agent will append specific endpoints like '/generate' or '/chat'.
OLLAMA_API_BASE_URL = "http://localhost:11434/api"  # Standard local Ollama API endpoint.

# === Other Constants ===
# You can add other global configurations or constants here as the agent evolves.
# Example: MAX_HISTORY_ENTRIES = 50

# --- End of Configuration ---
