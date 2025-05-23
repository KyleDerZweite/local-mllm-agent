# agent/core/controller.py
"""
The main orchestration component for the Local Multimodal LLM Agent.

This module defines the `AgentController` class, which acts as the central nervous system
of the agent. It is responsible for:
1. Initializing core components: `ModuleLoader` (to find tools), `ModelAdapters` (to communicate
   with LLMs), and `Pipeline` (to execute tool sequences).
2. Receiving user queries (text and optional image paths).
3. Using an LLM (e.g., DeepSeek) to understand the query and select an appropriate sequence
   of tools from the available modules.
4. Managing the execution of these tools via the `Pipeline`, including passing data and
   handling fallbacks.
5. Formatting the final result for the user.
6. If no tools are deemed necessary by the LLM, it can attempt to answer the query directly
   using the LLM.
"""

from typing import Dict, Any, List, Optional
import json # For pretty printing dicts in main test block

try:
    from .config import DEEPSEEK_MODEL, LLAVA_MODEL # LLaVA for future multimodal use
    from .module_loader import ModuleLoader
    from .model_adapters import DeepSeekAdapter, LLaVAAdapter # LLaVAAdapter imported for future use
    from .pipeline import Pipeline
except ImportError as e:
    print(f"AgentController: Error importing local modules: {e}. Ensure agent/core is in PYTHONPATH or running from agent project root.")
    raise

class AgentController:
    """
    Orchestrates the agent's operations from query intake to response generation.

    This involves loading tools, using an LLM to interpret user queries and select tools,
    executing these tools in a pipeline, and preparing the final output.
    """
    def __init__(self):
        """
        Initializes the AgentController.

        Sets up the module loader, loads available tools, initializes LLM model adapters
        (currently DeepSeek for text reasoning, LLaVA planned for multimodal), creates the
        execution pipeline, and prepares tool descriptions for use in LLM prompts.
        """
        print("AgentController: Initializing...")
        self.module_loader = ModuleLoader()
        self.available_tools = self.module_loader.load_modules()
        # print(f"AgentController: Loaded {len(self.available_tools)} tools: {list(self.available_tools.keys())}") # Verbose

        self.text_reasoning_model = DeepSeekAdapter(model_name=DEEPSEEK_MODEL)
        self.multimodal_model = LLaVAAdapter(model_name=LLAVA_MODEL) # Initialized for future use

        self.pipeline = Pipeline()
        self._prepare_tool_descriptions_for_llm()
        print("AgentController: Initialization complete.")

    def _prepare_tool_descriptions_for_llm(self) -> None:
        """
        Prepares a formatted string of all available tools and their descriptions.
        This string is used to provide context to the LLM during tool selection.
        The format is designed to be easily parsable by the LLM.
        """
        self.tool_descriptions_for_llm = "Available Tools:\n"
        if not self.available_tools:
            self.tool_descriptions_for_llm += "- No tools available.\n"
            return
        for name, info in self.available_tools.items():
            self.tool_descriptions_for_llm += f"- Tool Name: {name}\n"
            self.tool_descriptions_for_llm += f"  Description: {info.get('description', 'No description provided.')}\n"

    def _select_tools_with_llm(self, user_prompt: str, current_image_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Uses an LLM to select an appropriate sequence of tools based on the user prompt
        and optionally an image (though image processing is a TODO for this method).

        Args:
            user_prompt (str): The user's textual query.
            current_image_path (Optional[str]): Path to an image, if provided with the query.
                                               (Currently acknowledged but not used in this selection step).

        Returns:
            List[Dict[str, Any]]: A list of tool configuration dictionaries, ready for pipeline execution.
                                  Returns an empty list if no tools are selected or appropriate.
        """
        # TODO: If current_image_path, use self.multimodal_model (LLaVA) to generate image description
        #       or a combined text-image prompt to aid in tool selection.

        prompt_template = (
            f"User query: '{user_prompt}'\n"
            f"{'(Image provided: ' + current_image_path + ')' if current_image_path else ''}\n\n"
            f"{self.tool_descriptions_for_llm}\n"
            "Based on the user query and available tools, what tool(s) should be used, in what order? "
            "Respond with a comma-separated list of tool names (e.g., 'tool1, tool2'). "
            "If parameters are obvious from the query (e.g., a search term for 'websearch'), the system will try to pass them. "
            "Focus on selecting the correct sequence of tool names. Example: file_search, websearch\n"
            "If no tools seem appropriate for the query, respond with the word 'None'."
        )
        
        messages = [{"role": "user", "content": prompt_template}]
        # print(f"\nAgentController (LLM Tool Select): Sending prompt:\n{prompt_template}") # Verbose
        llm_response = self.text_reasoning_model.chat(messages)
        # print(f"AgentController (LLM Tool Select): LLM response for tool selection: '{llm_response}'") # Verbose

        selected_tool_names_str = llm_response.strip()
        if not selected_tool_names_str or selected_tool_names_str.lower() == 'none':
            # print("AgentController (LLM Tool Select): LLM indicated no tools are appropriate.") # Verbose
            return []

        selected_tool_names = [name.strip() for name in selected_tool_names_str.split(',') if name.strip()]
        
        tool_sequence: List[Dict[str, Any]] = []
        for tool_name in selected_tool_names:
            if tool_name in self.available_tools:
                tool_config = {
                    "name": tool_name,
                    "module_instance": self.available_tools[tool_name]["module_instance"]
                    # TODO: Allow LLM to suggest parameters for tools, then parse and add them here.
                }
                tool_sequence.append(tool_config)
            else:
                print(f"AgentController Warning: LLM selected tool '{tool_name}' but it is not available/loaded. Skipping.")
        
        # Example of a simple hardcoded fallback rule
        if tool_sequence and tool_sequence[-1]['name'] == 'websearch':
            if 'file_search' in self.available_tools:
                # print("AgentController: Applying hardcoded rule - adding 'file_search' as fallback for 'websearch'.") # Verbose
                tool_sequence[-1]['fallback'] = {
                    "name": "file_search_as_fallback",
                    "module_instance": self.available_tools['file_search']['module_instance']
                }

        return tool_sequence

    def handle_query(self, user_prompt: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Handles a user query, orchestrating tool selection and pipeline execution.

        Args:
            user_prompt (str): The textual query from the user.
            image_path (Optional[str]): Path to an image file, if the query is multimodal.

        Returns:
            Dict[str, Any]: A dictionary containing the agent's response, overall status,
                            and a history of tool execution. Structure:
                            `{"response": Any, "status": str, "execution_history": List[Dict]}`
        """
        # print(f"\nAgentController: Received query: '{user_prompt}'" + (f" with image: {image_path}" if image_path else "")) # Verbose

        if image_path:
            print(f"AgentController: Image path '{image_path}' provided. (Full multimodal processing is a TODO)")

        if not self.available_tools:
            print("AgentController Error: No tools available to handle the query.")
            return {"response": "I have no tools loaded and cannot process your request.", 
                    "status": "Error - No tools loaded", "execution_history": []}

        tool_sequence_to_run = self._select_tools_with_llm(user_prompt, image_path)

        if not tool_sequence_to_run:
            # print("AgentController: No tools selected. Attempting direct LLM response.") # Verbose
            direct_llm_messages = [
                {"role": "system", "content": "You are a helpful assistant. Answer the user's query directly and concisely."},
                {"role": "user", "content": user_prompt}
            ]
            direct_response = self.text_reasoning_model.chat(direct_llm_messages)
            return {"response": direct_response, 
                    "status": "Completed - Direct LLM response (no tools used)", 
                    "execution_history": []}

        # print(f"AgentController: Tool sequence selected for execution: {[tool.get('name') for tool in tool_sequence_to_run]}") # Verbose

        pipeline_input = {"user_prompt": user_prompt, "query": user_prompt, "image_path": image_path}
        
        pipeline_result = self.pipeline.execute(tool_sequence_to_run, pipeline_input)
        
        return {
            "response": pipeline_result.get('final_output'),
            "status": pipeline_result.get('status'),
            "execution_history": pipeline_result.get('history')
        }

if __name__ == '__main__':
    print("Testing AgentController (requires Ollama server and dummy modules)...")

    controller = None # Initialize to None for error handling
    try:
        controller = AgentController()
    except Exception as e_init:
        print(f"AgentController Test Error: Failed to initialize controller: {e_init}")
        print("Ensure Ollama is running, models (e.g., DEEPSEEK_MODEL) are pulled, and paths in config.py are correct.")

    if controller:
        if not controller.available_tools:
            print("AgentController Test Warning: No tools were loaded by ModuleLoader.")
            print("Please check MODULES_DIR and ensure dummy modules exist (e.g., 'greet_tool', 'file_search', 'websearch').")
        else:
            print(f"\nAgentController Test: Tool descriptions prepared for LLM:\n{controller.tool_descriptions_for_llm}")
        
        test_prompts = [
            {"id": 1, "desc": "tool use expected (e.g., greet_tool)", "prompt": "Greet me with the name Alex."},
            {"id": 2, "desc": "direct LLM response expected", "prompt": "What is the chemical formula for water?"},
            {"id": 3, "desc": "fallback test (websearch -> file_search)", "prompt": "Search the web for 'Ollama new features' then check local files."}
        ]

        for test in test_prompts:
            print(f"\n--- AgentController Test ({test['id']}): {test['desc']} ---")
            print(f"Sending prompt: '{test['prompt']}'")

            # Skip fallback test if relevant modules aren't loaded
            if test['id'] == 3 and not ('websearch' in controller.available_tools and 'file_search' in controller.available_tools):
                print("Skipping fallback test as 'websearch' or 'file_search' module not loaded.")
                continue

            result = controller.handle_query(user_prompt=test['prompt'])
            # Use json.dumps for potentially complex/nested dicts in response
            try:
                print(f"Test ({test['id']}) Result:\n{json.dumps(result, indent=2, default=str)}")
            except TypeError:
                print(f"Test ({test['id']}) Result (raw, json dump failed):\n{result}")
    else:
        print("AgentController Test: Controller initialization failed. Cannot run further tests.")

    print("\nAgentController testing finished.")
```
