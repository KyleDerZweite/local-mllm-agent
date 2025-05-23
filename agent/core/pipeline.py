# agent/core/pipeline.py
"""
Manages the execution of a sequence of tools (modules).

This module defines the `Pipeline` class, which is responsible for executing a list
of tool configurations. It handles the flow of data from one tool to the next,
manages tool-specific parameters, and implements a fallback mechanism if a primary
tool encounters an error. A detailed history of the execution, including inputs,
outputs, and status for each step (and any fallbacks attempted), is recorded.
"""

from typing import List, Dict, Any, Optional

class Pipeline:
    """
    Executes a sequence of tools, manages data flow, and handles fallbacks.

    The pipeline takes a list of tool configurations. Each tool is executed in order.
    The output of a tool can become the input for the subsequent tool. If a tool fails,
    a specified fallback tool can be attempted. The pipeline maintains a history of all
    operations.
    """
    def __init__(self):
        """
        Initializes the Pipeline.

        Attributes:
            history (List[Dict[str, Any]]): Stores a log of operations performed during
                                            the execution of a tool sequence. Cleared
                                            at the start of each `execute` call.
        """
        self.history: List[Dict[str, Any]] = [] 
        # print("Pipeline class initialized.") # Verbose: uncomment for debugging init

    def execute(self, tool_sequence: List[Dict[str, Any]], initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a given sequence of tools with an initial input.

        Args:
            tool_sequence (List[Dict[str, Any]]): A list of dictionaries, where each
                dictionary configures a tool to be run. Expected keys per tool dict:
                - "name" (str): A descriptive name for the tool step.
                - "module_instance" (Any): The actual loaded module object that has a `run` method.
                - "params" (Optional[Dict[str, Any]]): Tool-specific parameters that will be merged
                  with or override the `current_input` before calling the tool's `run` method.
                - "fallback" (Optional[Dict[str, Any]]): Another tool configuration dictionary
                  (same structure as a primary tool) to be executed if the primary tool fails.
                  The fallback tool will receive the same `tool_specific_input` as the primary tool
                  unless its own `params` override parts of it.

            initial_input (Dict[str, Any]): The initial data dictionary to pass to the first tool
                                          in the sequence (or as the base for its `params`).

        Returns:
            Dict[str, Any]: A dictionary containing the final result of the pipeline execution:
                - "final_output" (Dict[str, Any]): The output from the last successfully executed
                  tool (or fallback), or the output from the last successful tool before a failure
                  if the pipeline stops prematurely.
                - "status" (str): A message indicating the overall status of the pipeline execution
                  (e.g., success, specific error, fallback success).
                - "history" (List[Dict[str, Any]]): A detailed log of each step's execution,
                  including inputs, outputs, errors, and fallback attempts.
        """
        current_input = initial_input
        self.history = [] 
        final_status = "Pipeline execution started."
        # final_output defaults to initial_input, updated upon each successful tool execution.
        # This ensures that if a tool fails, final_output holds the result of the *previous* successful step.
        final_output = current_input.copy() 

        # print(f"Pipeline: Starting execution with initial input: {current_input}") # Verbose

        for i, tool_info in enumerate(tool_sequence):
            step_num = i + 1
            tool_name = tool_info.get("name", f"UnnamedTool_{step_num}")
            module_instance = tool_info.get("module_instance")
            
            # Prepare the actual input for the tool, merging current_input with tool-specific params.
            # Params from tool_info take precedence.
            tool_specific_input = current_input.copy()
            if "params" in tool_info and isinstance(tool_info["params"], dict):
                tool_specific_input.update(tool_info["params"])

            # Check if the module instance is valid and has a callable 'run' method.
            if not module_instance or not hasattr(module_instance, 'run') or not callable(module_instance.run):
                error_msg = f"Tool '{tool_name}' (Step {step_num}) is invalid or has no callable 'run' function. Skipping."
                # print(f"Pipeline Error: {error_msg}") # Verbose
                self.history.append({
                    "step": step_num, "tool_name": tool_name,
                    "input_provided": tool_specific_input, # Log what would have been passed
                    "output": {"error": error_msg, "type": "InvalidToolConfiguration"},
                    "status": "Skipped - Invalid Tool"
                })
                final_status = f"Error: {error_msg}"
                return {"final_output": final_output, "status": final_status, "history": self.history}
            
            # print(f"Pipeline: Executing tool '{tool_name}' (Step {step_num}) with input: {tool_specific_input}") # Verbose
            
            primary_tool_failed = False
            # primary_error_details = None # Not strictly needed here as it's set in except block

            try:
                # Execute the primary tool's run method
                step_output = module_instance.run(tool_specific_input)
                # print(f"Pipeline: Tool '{tool_name}' (Step {step_num}) executed successfully. Output: {step_output}") # Verbose
                current_input = step_output 
                final_output = current_input # Update final_output with the latest successful result
                self.history.append({
                    "step": step_num, "tool_name": tool_name,
                    "input_provided": tool_specific_input, "output": step_output,
                    "status": "Success"
                })
                final_status = f"Tool '{tool_name}' (Step {step_num}) completed successfully."
            except Exception as e:
                primary_tool_failed = True
                primary_error_details = {"error": str(e), "type": type(e).__name__}
                error_msg = f"Error executing tool '{tool_name}' (Step {step_num}): {type(e).__name__} - {e}"
                # print(f"Pipeline Error: {error_msg}") # Verbose
                self.history.append({
                    "step": step_num, "tool_name": tool_name,
                    "input_provided": tool_specific_input, "output": primary_error_details,
                    "status": "Failed - Primary"
                })
                final_status = f"Error: {error_msg}" # This might be updated by fallback logic

            if primary_tool_failed:
                fallback_tool_info = tool_info.get("fallback")
                history_entry_for_primary = self.history[-1] # Get the 'Failed - Primary' entry
                history_entry_for_primary["fallback_attempted"] = False # Initialize

                if fallback_tool_info:
                    history_entry_for_primary["fallback_attempted"] = True
                    fallback_name = fallback_tool_info.get("name", f"FallbackFor_{tool_name}")
                    fallback_module = fallback_tool_info.get("module_instance")
                    history_entry_for_primary["fallback_tool_name"] = fallback_name

                    if fallback_module and hasattr(fallback_module, 'run') and callable(fallback_module.run):
                        # print(f"Pipeline: Attempting fallback tool '{fallback_name}' for '{tool_name}' (Step {step_num}).") # Verbose
                        # Fallback uses the same input as primary, unless its own params override.
                        fallback_specific_input = tool_specific_input.copy()
                        if "params" in fallback_tool_info and isinstance(fallback_tool_info["params"], dict):
                             fallback_specific_input.update(fallback_tool_info["params"])
                        history_entry_for_primary["fallback_input_provided"] = fallback_specific_input

                        try:
                            step_output = fallback_module.run(fallback_specific_input)
                            # print(f"Pipeline: Fallback tool '{fallback_name}' (Step {step_num}) executed successfully. Output: {step_output}") # Verbose
                            current_input = step_output
                            final_output = current_input # Update final_output with fallback's success
                            history_entry_for_primary["fallback_output"] = step_output
                            history_entry_for_primary["fallback_status"] = "Success"
                            final_status = f"Fallback tool '{fallback_name}' (Step {step_num}) for '{tool_name}' completed successfully."
                        except Exception as fe:
                            # print(f"Pipeline Error: Error executing fallback tool '{fallback_name}' (Step {step_num}): {type(fe).__name__} - {fe}") # Verbose
                            history_entry_for_primary["fallback_output"] = {"error": str(fe), "type": type(fe).__name__}
                            history_entry_for_primary["fallback_status"] = "Failed"
                            final_status = f"Error: Both primary tool '{tool_name}' and its fallback '{fallback_name}' (Step {step_num}) failed."
                            # If fallback fails, pipeline stops, final_output is from before primary failed.
                            return {"final_output": final_output, "status": final_status, "history": self.history}
                    else:
                        # print(f"Pipeline Warning: Fallback tool '{fallback_name}' for '{tool_name}' (Step {step_num}) is invalid or missing 'run' function.") # Verbose
                        history_entry_for_primary["fallback_status"] = "Skipped - Invalid Fallback Tool"
                        # Primary failed, fallback invalid. Pipeline stops. final_status is already primary's error.
                        return {"final_output": final_output, "status": final_status, "history": self.history}
                else: # Primary tool failed, and no fallback was specified.
                    # print(f"Pipeline Info: Tool '{tool_name}' (Step {step_num}) failed, no fallback specified. Stopping pipeline.") # Verbose
                    # final_status is already primary's error.
                    return {"final_output": final_output, "status": final_status, "history": self.history}
        
        # print(f"Pipeline: Execution finished. Final output: {final_output}") # Verbose
        return {"final_output": final_output, "status": final_status, "history": self.history}

# The __main__ block from Step 5d (Comprehensive Tests) is retained below.
# It is assumed to be correct and complete as per the previous step.
if __name__ == '__main__':
    print('Testing Pipeline (Iterative Step 5d: Comprehensive Tests)...')

    class SuccessTool:
        def __init__(self, name='SuccessTool'):
            self.name = name
        def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            # print(f'  [{self.name}] Received: {input_data}') # Test verbose
            val = input_data.get('value', 0)
            output = {'message': f'{self.name} processed', 'data': val + 1, 'source': self.name}
            # print(f'  [{self.name}] Returning: {output}') # Test verbose
            return output

    class FailTool:
        def __init__(self, name='FailTool', error_type=ValueError, error_message='intentionally failed'):
            self.name = name
            self.error_type = error_type
            self.error_message = error_message
        def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            # print(f'  [{self.name}] Received: {input_data}, will raise {self.error_type.__name__}.') # Test verbose
            raise self.error_type(f'{self.name} {self.error_message}')

    class AnotherSuccessTool:
        def __init__(self, name='AnotherSuccessTool'):
            self.name = name
        def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            # print(f'  [{self.name}] Received: {input_data}') # Test verbose
            val = input_data.get('data', 0)
            output = {'message': f'{self.name} processed', 'final_data': val * 2, 'source': self.name}
            # print(f'  [{self.name}] Returning: {output}') # Test verbose
            return output

    s_tool1 = SuccessTool('S_Tool1')
    s_tool2 = SuccessTool('S_Tool2')
    a_tool = AnotherSuccessTool('A_Tool')
    f_tool_val_err = FailTool('F_Tool_ValueError')
    f_tool_type_err = FailTool('F_Tool_TypeError', TypeError, 'type error')

    pipeline = Pipeline()
    
    # Test Case 1: Simple success sequence
    print(f"\n{'='*20} Test Case 1: Simple success sequence {'='*20}")
    sequence1 = [
        {'name': 'Step1', 'module_instance': s_tool1, 'params': {'value': 10}},
        {'name': 'Step2', 'module_instance': a_tool}
    ]
    result1 = pipeline.execute(sequence1, {'initial_value': 0})
    print(f'Pipeline Result 1 (Output): {result1.get("final_output")}')
    print(f'Pipeline Result 1 (Status): {result1.get("status")}')
    assert result1['final_output']['final_data'] == (10 + 1) * 2
    assert 'completed successfully' in result1['status']

    # Test Case 2: Tool failure with successful fallback
    print(f'\n{'='*20} Test Case 2: Tool failure with successful fallback {'='*20}')
    sequence2 = [
        {'name': 'Step1', 'module_instance': s_tool1, 'params': {'value': 5}},
        {
            'name': 'Step2_PrimaryFail', 'module_instance': f_tool_val_err, 'params': {'value': -1},
            'fallback': {'name': 'Step2_FallbackOK', 'module_instance': s_tool2, 'params': {'value': 100}}
        },
        {'name': 'Step3_AfterFallback', 'module_instance': a_tool}
    ]
    result2 = pipeline.execute(sequence2, {'initial_value': 0})
    print(f'Pipeline Result 2 (Output): {result2.get("final_output")}')
    print(f'Pipeline Result 2 (Status): {result2.get("status")}')
    assert result2['final_output']['final_data'] == (100 + 1) * 2
    assert 'Fallback tool \'Step2_FallbackOK\'' in result2['status'] and 'completed successfully' in result2['status']

    # Test Case 3: Tool failure with no fallback
    print(f'\n{'='*20} Test Case 3: Tool failure with no fallback {'='*20}')
    sequence3 = [
        {'name': 'Step1', 'module_instance': s_tool1, 'params': {'value': 1}},
        {'name': 'Step2_FailNoFallback', 'module_instance': f_tool_type_err, 'params': {'value': -1}},
        {'name': 'Step3_ShouldNotRun', 'module_instance': a_tool}
    ]
    result3 = pipeline.execute(sequence3, {'initial_value': 0})
    print(f'Pipeline Result 3 (Output): {result3.get("final_output")}')
    print(f'Pipeline Result 3 (Status): {result3.get("status")}')
    assert result3['final_output']['data'] == 1 + 1 
    assert 'Error executing tool \'Step2_FailNoFallback\'' in result3['status']
    assert len(result3['history']) == 2 and result3['history'][1]['status'] == 'Failed - Primary'
    assert result3['history'][1].get('fallback_attempted') == False

    # Test Case 4: Tool failure with failing fallback
    print(f'\n{'='*20} Test Case 4: Tool failure with failing fallback {'='*20}')
    sequence4 = [
        {'name': 'Step1', 'module_instance': s_tool1, 'params': {'value': 7}},
        {
            'name': 'Step2_PrimaryFail', 'module_instance': f_tool_val_err, 'params': {'value': -1},
            'fallback': {'name': 'Step2_FallbackFail', 'module_instance': f_tool_type_err, 'params': {'value': -2}}
        },
        {'name': 'Step3_ShouldNotRun', 'module_instance': a_tool}
    ]
    result4 = pipeline.execute(sequence4, {'initial_value': 0})
    print(f'Pipeline Result 4 (Output): {result4.get("final_output")}')
    print(f'Pipeline Result 4 (Status): {result4.get("status")}')
    assert result4['final_output']['data'] == 7 + 1 
    assert 'Both primary tool \'Step2_PrimaryFail\' and its fallback \'Step2_FallbackFail\'' in result4['status']
    assert len(result4['history']) == 2 and result4['history'][1]['fallback_status'] == 'Failed'

    # Test Case 5: Invalid tool in sequence
    print(f'\n{'='*20} Test Case 5: Invalid tool in sequence {'='*20}')
    sequence5 = [
        {'name': 'Step1', 'module_instance': s_tool1, 'params': {'value': 3}},
        {'name': 'Step2_Invalid', 'module_instance': None},
        {'name': 'Step3_ShouldNotRun', 'module_instance': a_tool}
    ]
    result5 = pipeline.execute(sequence5, {'initial_value': 0})
    print(f'Pipeline Result 5 (Output): {result5.get("final_output")}')
    print(f'Pipeline Result 5 (Status): {result5.get("status")}')
    assert result5['final_output']['data'] == 3 + 1 
    assert 'Tool \'Step2_Invalid\' (Step 2) is invalid' in result5['status']
    assert len(result5['history']) == 2 and result5['history'][1]['status'] == 'Skipped - Invalid Tool'

    # Test Case 6: Empty tool sequence
    print(f'\n{'='*20} Test Case 6: Empty tool sequence {'='*20}')
    sequence6 = []
    initial_data6 = {'message': 'empty sequence test'}
    result6 = pipeline.execute(sequence6, initial_data6)
    print(f'Pipeline Result 6 (Output): {result6.get("final_output")}')
    print(f'Pipeline Result 6 (Status): {result6.get("status")}')
    assert result6['final_output'] == initial_data6
    assert result6['status'] == 'Pipeline execution started.'
    assert len(result6['history']) == 0

    # Test Case 7: Fallback uses primary tool's input if no params
    print(f'\n{'='*20} Test Case 7: Fallback uses primary tool\'s input if no params {'='*20}')
    sequence7 = [
        {
            'name': 'Step1_PrimaryFail',
            'module_instance': f_tool_val_err, 
            'params': {'value': -1, 'original_info': 'from_initial'}, 
            'fallback': {'name': 'Step1_FallbackOK', 'module_instance': s_tool2} 
        },
        {'name': 'Step2_AfterFallback', 'module_instance': a_tool} 
    ]
    result7 = pipeline.execute(sequence7, {'initial_value': 0}) 
    print(f'Pipeline Result 7 (Output): {result7.get("final_output")}')
    print(f'Pipeline Result 7 (Status): {result7.get("status")}')
    assert result7['final_output']['final_data'] == 0 
    assert 'Fallback tool \'Step1_FallbackOK\'' in result7['status']
    history_step1 = result7['history'][0]
    assert history_step1['fallback_input_provided']['value'] == -1
    assert history_step1['fallback_output']['data'] == 0

    print('\nAll comprehensive tests completed.')
```
