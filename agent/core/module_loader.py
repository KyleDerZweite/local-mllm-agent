# agent/core/module_loader.py
"""
Dynamically loads agent modules (tools) from the filesystem.

This module defines the `ModuleLoader` class, which is responsible for scanning
a designated directory (specified in `config.py` as `MODULES_DIR`) for subdirectories,
each representing a potential module. For a subdirectory to be considered a valid module,
it must contain an `AGENT.md` file (describing the tool's capabilities) and a `main.py`
file (containing a `run` function that executes the tool's logic).

The loader parses `AGENT.md` to extract a description for the LLM and dynamically
imports the `run` function from `main.py`. Information about loaded tools is stored
and made available to other parts of the agent, like the `AgentController`.
"""

import os
import importlib.util
from typing import Dict, Any, Optional, List

try:
    from .config import MODULES_DIR
except ImportError:
    print("ModuleLoader: Could not perform relative import of config. Using default MODULES_DIR.")
    MODULES_DIR = "modules" 

class ModuleLoader:
    """
    Discovers, loads, and manages agent modules (tools).

    Scans a specified directory for modules, parses their `AGENT.md` metadata files,
    and dynamically imports their `main.py` to make their `run` functions available.
    The path to the modules directory and the name of the metadata file are configurable.
    """
    def __init__(self, base_module_path: str = MODULES_DIR, agent_md_filename: str = "AGENT.md"):
        """
        Initializes the ModuleLoader.

        Args:
            base_module_path (str): The base path to the modules directory, typically relative
                                    to the agent's root (e.g., "modules"). This is used to
                                    construct both filesystem paths and Python import paths.
                                    Defaults to `MODULES_DIR` from `config.py`.
            agent_md_filename (str): The name of the metadata file within each module's
                                     directory that describes the tool. Defaults to "AGENT.md".
        """
        self.base_module_path = base_module_path
        # Resolve the absolute path to the modules directory for filesystem operations.
        if not os.path.isabs(self.base_module_path):
            # Assumes this script (module_loader.py) is in agent/core/
            current_script_dir = os.path.dirname(os.path.abspath(__file__)) 
            agent_root_dir = os.path.dirname(current_script_dir) # Up one level to agent/
            self.modules_dir = os.path.join(agent_root_dir, self.base_module_path)
        else:
            self.modules_dir = self.base_module_path
            
        self.agent_md_filename = agent_md_filename
        self.available_tools: Dict[str, Dict[str, Any]] = {} # Stores loaded tool data
        print(f"ModuleLoader initialized. Looking for modules in: {self.modules_dir}")

    def _parse_agent_md(self, md_file_path: str) -> Optional[str]:
        """
        Parses the AGENT.md file to extract the tool's description.

        The parsing strategy is simple: it looks for a line starting with '# Tool:'
        (case-insensitive for the content after '#') and then concatenates subsequent non-empty
        lines as the description until a blank line or end-of-file.
        If this pattern isn't found, it attempts a fallback to use content after the first
        Markdown heading, or the whole file if no heading is present.

        Args:
            md_file_path (str): The absolute path to the AGENT.md file.

        Returns:
            Optional[str]: The extracted description string, or "No description found." if parsing
                           is successful but yields no lines. Returns None if the file cannot be read
                           or a critical parsing error occurs.
        """
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            description_lines: List[str] = []
            in_description_section = False
            
            for line in lines:
                stripped_line = line.strip()
                # Start capturing after a line like '# Tool: Tool Name Here'
                if stripped_line.lower().startswith("# tool:") and not description_lines:
                    in_description_section = True 
                    # We don't include the '# Tool:' line itself in the description.
                    continue 
                
                if in_description_section:
                    if not stripped_line: # Stop at the first blank line
                        break
                    description_lines.append(stripped_line)
            
            # Fallback if specific '# Tool:' section wasn't found or was empty
            if not description_lines and lines:
                if lines[0].strip().startswith("#"):
                    # If the first line is a heading, take all subsequent non-empty lines
                    description_lines = [l.strip() for l in lines[1:] if l.strip()]
                else:
                    # Otherwise, take all non-empty lines as description
                    description_lines = [l.strip() for l in lines if l.strip()]

            return " ".join(description_lines) if description_lines else "No description found."

        except FileNotFoundError:
            print(f"ModuleLoader Warning: AGENT.md file not found at {md_file_path}")
            return None
        except Exception as e:
            print(f"ModuleLoader Error: Error parsing AGENT.md file at {md_file_path}: {e}")
            return None

    def load_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        Scans the modules directory, loads valid modules, and parses their AGENT.md files.

        A module is considered valid if it's a directory containing both `main.py`
        (with a callable `run` function) and the specified `agent_md_filename`.
        Loaded tools are stored in `self.available_tools`.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary of available tools, where keys are
            module names and values are dictionaries containing the module instance,
            description, path, and name.
        """
        print(f"ModuleLoader: Starting to load modules from: {self.modules_dir}")
        if not os.path.isdir(self.modules_dir):
            print(f"ModuleLoader Error: Modules directory not found at {self.modules_dir}")
            return {}

        for module_name in os.listdir(self.modules_dir):
            module_fs_path = os.path.join(self.modules_dir, module_name) # Filesystem path to module dir
            if os.path.isdir(module_fs_path):
                main_py_path = os.path.join(module_fs_path, "main.py")
                agent_md_path = os.path.join(module_fs_path, self.agent_md_filename)

                if not os.path.isfile(main_py_path):
                    print(f"ModuleLoader Info: Skipping '{module_name}': missing main.py at {main_py_path}")
                    continue
                if not os.path.isfile(agent_md_path):
                    print(f"ModuleLoader Info: Skipping '{module_name}': missing {self.agent_md_filename} at {agent_md_path}")
                    continue

                description = self._parse_agent_md(agent_md_path)
                if description is None:
                    print(f"ModuleLoader Warning: Skipping module '{module_name}' due to missing or unparsable AGENT.md.")
                    continue
                
                # Construct the Python import name (e.g., modules.file_search.main)
                # self.base_module_path is 'modules' (or configured equivalent)
                import_name = f"{self.base_module_path}.{module_name}.main"
                
                try:
                    spec = importlib.util.spec_from_file_location(import_name, main_py_path)
                    if spec and spec.loader:
                        module_obj = importlib.util.module_from_spec(spec)
                        # Add module to sys.modules *before* exec_module to handle circular deps if any
                        # and to make it findable by other imports within the loaded module if needed.
                        sys.modules[import_name] = module_obj 
                        spec.loader.exec_module(module_obj)
                        
                        if hasattr(module_obj, 'run') and callable(module_obj.run):
                            self.available_tools[module_name] = {
                                "module_instance": module_obj,
                                "description": description,
                                "path": main_py_path, # Filesystem path to main.py
                                "name": module_name    # The directory name of the module
                            }
                            print(f"ModuleLoader: Successfully loaded module: '{module_name}'")
                        else:
                            print(f"ModuleLoader Warning: Module '{module_name}' loaded but has no callable 'run' function.")
                            del sys.modules[import_name] # Clean up if not valid
                    else:
                        print(f"ModuleLoader Warning: Could not create module spec for '{module_name}' at {main_py_path}")
                except Exception as e:
                    print(f"ModuleLoader Error: Error loading module '{module_name}' from {main_py_path}: {e}")
                    if import_name in sys.modules:
                        del sys.modules[import_name] # Clean up on error
            # else: (not a directory, so skip)
            #    print(f"ModuleLoader Info: Skipping '{module_name}' as it is not a directory.")
        
        if not self.available_tools:
            print("ModuleLoader Warning: No modules were successfully loaded.")
        else:
            print(f"ModuleLoader: Finished loading. {len(self.available_tools)} tools available: {list(self.available_tools.keys())}")
        return self.available_tools

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the dictionary of available tools that have been loaded.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary where keys are module names and
            values are dictionaries containing tool metadata (module instance, description, etc.).
        """
        return self.available_tools

if __name__ == '__main__':
    import sys # Required for sys.modules manipulation if not already imported
    print("Testing ModuleLoader standalone...")
    
    # Determine paths for testing - assumes this script is in agent/core/
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    agent_root_dir_for_test = os.path.dirname(current_script_dir) # agent/
    # Temporarily add agent_root_dir_for_test to sys.path to allow 'modules.module_name.main' imports
    if agent_root_dir_for_test not in sys.path:
        sys.path.insert(0, agent_root_dir_for_test)

    # MODULES_DIR is 'modules' by default from config or local override
    test_modules_root_name = MODULES_DIR 
    test_modules_abs_path = os.path.join(agent_root_dir_for_test, test_modules_root_name)

    print(f"Test: Target modules directory for loading: {test_modules_abs_path}")
    print(f"Test: Base module path for imports: '{test_modules_root_name}'")

    # Create dummy modules for testing
    dummy_modules_info = {
        "test_module1": {
            "AGENT.md": "# Tool: Test Tool One\nDescription for test tool one.",
            "main.py": "def run(input_data: dict) -> dict:\n    print(f'[test_module1] run called with {input_data}')\n    return {'tool': 'test_module1', 'result': 'success one', 'input_echo': input_data}"
        },
        "test_module2": {
            "AGENT.md": "# Tool: Test Tool Two\nDescription for test tool two.",
            "main.py": "def run(input_data: dict) -> dict:\n    print(f'[test_module2] run called with {input_data}')\n    return {'tool': 'test_module2', 'result': 'success two', 'input_echo': input_data}"
        },
        "invalid_module_no_run": {
            "AGENT.md": "# Tool: Invalid No Run\nThis tool is missing a run function.",
            "main.py": "# No run function here"
        },
        "invalid_module_no_agent_md": {
            # No AGENT.md here
            "main.py": "def run(input_data: dict) -> dict: return {'tool': 'no_agent_md', 'result': 'should not load'}"
        }
    }

    # Create dummy AGENT.md for invalid_module_no_agent_md so it's not skipped for that reason
    # but rather for the main.py not being found (which it will be)
    # This test is more about the structure. The module itself won't be created to test missing main.py.

    if not os.path.exists(test_modules_abs_path):
        os.makedirs(test_modules_abs_path)
        print(f"Test: Created base modules directory for testing: {test_modules_abs_path}")

    for mod_name, files in dummy_modules_info.items():
        mod_dir = os.path.join(test_modules_abs_path, mod_name)
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir)
        for file_name, content in files.items():
            with open(os.path.join(mod_dir, file_name), 'w', encoding='utf-8') as f:
                f.write(content.replace("\\n", "\n")) 
        print(f"Test: Created dummy module for testing: {mod_name}")

    # Test with a module that only has AGENT.md (main.py will be missing)
    only_md_mod_name = "only_agent_md_module"
    only_md_mod_dir = os.path.join(test_modules_abs_path, only_md_mod_name)
    if not os.path.exists(only_md_mod_dir):
        os.makedirs(only_md_mod_dir)
    with open(os.path.join(only_md_mod_dir, "AGENT.md"), 'w', encoding='utf-8') as f:
        f.write("# Tool: Only MD\nThis module only has an AGENT.md file.")
    print(f"Test: Created dummy module for testing: {only_md_mod_name}")

    # Initialize ModuleLoader using the name of the modules directory (e.g., "modules")
    # The ModuleLoader constructor will resolve this to an absolute path for os operations.
    loader = ModuleLoader(base_module_path=test_modules_root_name) 
    loaded_tools = loader.load_modules()

    print("\n--- Test: Available Tools After Loading ---")
    for tool_name, tool_info in loaded_tools.items():
        print(f"  Tool: {tool_name}")
        print(f"    Description: {tool_info['description']}")
        print(f"    Path: {tool_info['path']}")
        if hasattr(tool_info['module_instance'], 'run'):
            print(f"    Attempting to run test for '{tool_name}'...")
            test_run_input = {"query": f"test query for {tool_name}"}
            try:
                run_result = tool_info['module_instance'].run(test_run_input)
                print(f"    Result from '{tool_name}': {run_result}")
            except Exception as e_run:
                print(f"    Error running '{tool_name}': {e_run}")
        else:
            print(f"    '{tool_name}' does not have a callable 'run' function as expected by loader.")
            
    if not loaded_tools:
        print("Test Warning: No tools were loaded. Check MODULES_DIR, module structure, and sys.path for tests.")
        print(f"ModuleLoader was looking in (absolute path): {loader.modules_dir}")
        print(f"Sys.path includes: {sys.path}")

    print("\n--- Test: AGENT.md Parsing (example on test_module1) ---")
    if loaded_tools.get("test_module1"):
        md_path_test = os.path.join(test_modules_abs_path, "test_module1", "AGENT.md")
        parsed_desc = loader._parse_agent_md(md_path_test)
        print(f"Parsed description for test_module1 AGENT.md: '{parsed_desc}'")
        expected_desc = "Description for test tool one."
        assert parsed_desc == expected_desc, f"Expected '{expected_desc}', got '{parsed_desc}'"
        print("AGENT.md parsing for test_module1 seems OK.")

    print("\nModuleLoader testing complete.")
    # Consider cleanup of dummy modules if needed, e.g. using shutil.rmtree
    # For CI/repeated tests, cleanup is good practice.
    # import shutil
    # if os.path.exists(test_modules_abs_path):
    #     shutil.rmtree(test_modules_abs_path)
    #     print(f"Test: Cleaned up dummy modules directory: {test_modules_abs_path}")

    # Remove agent_root_dir_for_test from sys.path if it was added
    if agent_root_dir_for_test in sys.path and sys.path[0] == agent_root_dir_for_test:
        sys.path.pop(0)
```
