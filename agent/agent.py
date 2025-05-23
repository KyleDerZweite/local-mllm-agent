# agent/agent.py
"""
Command-Line Interface (CLI) entry point for the Local Multimodal LLM Agent.

This script handles parsing command-line arguments, initializing the `AgentController`,
passing user queries to the controller, and displaying the agent's response and
execution history (if requested via verbose mode).

It ensures that the necessary Python paths are set up so that core components
can be imported correctly. It also includes basic error handling for controller
initialization and query processing.

Usage:
    python agent.py --prompt "Your query here" [--image "path/to/image.png"] [--verbose]
"""

import argparse
import os
import sys
import json # For pretty printing history if it's complex and verbose is on

# --- Python Path Setup ---
# Ensures that the 'core' and 'modules' directories can be found by Python's import system.
# This is done by adding the 'agent/' directory (the parent of this script) to sys.path.
try:
    current_script_path = os.path.abspath(__file__)
    agent_root_dir = os.path.dirname(current_script_path) 
    if agent_root_dir not in sys.path:
        sys.path.insert(0, agent_root_dir)
except NameError: # __file__ might not be defined in some environments (e.g. certain REPLs)
    print("Warning: Could not automatically determine agent_root_dir. Assuming '.' is in sys.path correctly.")

try:
    from core.controller import AgentController
except ImportError as e:
    print(f'CLI Error: Could not import AgentController. Original error: {e}')
    print('This usually means the script is not being run from the correct location or PYTHONPATH is not set up.')
    print(f'Current sys.path: {sys.path}')
    print('Please ensure you are running this script from the project\'s root directory (e.g., /path/to/project/agent).')
    sys.exit(1)

def main():
    """
    Main function to run the CLI agent.

    Parses command-line arguments, initializes the AgentController, passes the user's
    query (and optional image) to the controller, and then prints the structured
    response, status, and execution history (if verbose mode is enabled).
    """
    parser = argparse.ArgumentParser(
        description='Local Multimodal LLM Agent CLI.',
        formatter_class=argparse.RawTextHelpFormatter # Allows for better formatting of help text
    )
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='The text prompt for the agent to process.'
    )
    parser.add_argument(
        '--image',
        type=str,
        default=None,
        help='Optional path to an image file for multimodal queries.\n(Note: Full image processing is a TODO in the controller).' 
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output, including detailed execution history of tools.'
    )

    args = parser.parse_args()

    if args.verbose:
        print('CLI: Verbose mode enabled.')
        # Verbosity within the agent's core components is currently handled by their own print statements.
        # This flag mainly controls the display of execution_history here.

    print('CLI: Initializing AgentController...')
    try:
        controller = AgentController()
    except Exception as e:
        print(f'CLI Critical Error: Failed to initialize AgentController: {e}')
        print("Check Ollama server status, model availability (see config.py), and file paths.")
        sys.exit(1)
    
    print(f'CLI: Handling query with prompt: \'{args.prompt}\'')
    if args.image:
        if not os.path.isfile(args.image):
            print(f'CLI Error: Image file not found at specified path: {args.image}')
            sys.exit(1)
        print(f'CLI: Image path provided: {os.path.abspath(args.image)}')

    try:
        result = controller.handle_query(user_prompt=args.prompt, image_path=args.image)
    except Exception as e:
        print(f'CLI Critical Error: An unexpected error occurred during query handling: {type(e).__name__} - {e}')
        # In a production system, you might want to log the full traceback here.
        # import traceback
        # print(traceback.format_exc())
        sys.exit(1)

    # --- Displaying Agent's Response ---
    section_line = '=' * 76
    agent_response_header = '='*30 + ' AGENT RESPONSE ' + '='*30
    print(f'\n{agent_response_header}')

    response_content = result.get('response', 'No response content found.')
    if isinstance(response_content, dict):
        print('Final Output (Structured):')
        try:
            # Pretty print if it's a dict, helps with nested structures
            print(json.dumps(response_content, indent=2, default=str)) 
        except TypeError: # Fallback if dict contains non-serializable items for json.dumps
            for key, value in response_content.items():
                print(f'  {key}: {value}')
    else:
        print(f'Final Output: {response_content}')
    
    print(f'Status: {result.get('status', 'No status provided.')}')
    print(f'{section_line}\n')

    if args.verbose and result.get('execution_history'):
        print('Execution History:')
        history = result['execution_history']
        if not history:
            print('  (No tools were executed or history is empty.)')
        else:
            for i, entry in enumerate(history):
                print(f"  --- Step {entry.get('step', i+1)}: {entry.get('tool_name', 'Unknown Tool')} ---")
                print(f"    Status: {entry.get('status')}")
                
                # Safely print potentially complex input/output by converting to string and truncating
                input_provided_str = str(entry.get('input_provided', 'N/A'))
                output_str = str(entry.get('output', 'N/A'))
                print(f"    Input: {input_provided_str[:250]}{'...' if len(input_provided_str) > 250 else ''}")
                print(f"    Output: {output_str[:350]}{'...' if len(output_str) > 350 else ''}")

                if entry.get('fallback_attempted'):
                    print(f"    Fallback Tool: {entry.get('fallback_tool_name', 'N/A')} (Status: {entry.get('fallback_status', 'N/A')})")
                    if entry.get('fallback_status') != 'Skipped - Invalid Fallback Tool':
                        fallback_input_str = str(entry.get('fallback_input_provided', 'N/A'))
                        fallback_output_str = str(entry.get('fallback_output', 'N/A')) # Could be error or success data
                        print(f"      Fallback Input: {fallback_input_str[:250]}{'...' if len(fallback_input_str) > 250 else ''}")
                        print(f"      Fallback Output/Error: {fallback_output_str[:350]}{'...' if len(fallback_output_str) > 350 else ''}")
        print(f'{section_line}\n')

if __name__ == '__main__':
    main()
```
