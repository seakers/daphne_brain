import json
import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response
import os
import sys
import django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daphne_brain.settings")
django.setup()
from EOSS.engineer.dialogue_functions import (
    get_architecture_scores,
    get_satisfying_data_products,
    get_unsatisfied_justifications,
    get_panel_scores,
    get_objective_scores,
    get_instruments_for_objective,
    get_instruments_for_stakeholder,
    get_instrument_parameter,
    get_instrument_parameter_followup,
    get_measurement_requirement,
    get_measurement_requirement_followup,
    get_cost_explanation
)



logger = logging.getLogger('EOSS.dialogue.engineer_agent')

class EngineerAgent:
    """
    Agent that handles engineering queries related to space mission designs.
    """
    
    def __init__(self):
        """
        Initialize the Engineer agent with an LLM model.
        
        Args:
            model: LLM model for generating responses
        """    
        pass

    def _select_functions(self, query: str, parameters: Dict, context) -> List[Dict]:
        """
        Select which functions to call based on the query and extracted parameters.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
        
        Returns:
            List of function descriptions with their arguments
        """
        # Create a prompt for the LLM to select the appropriate functions
        prompt = f"""
You are an agent that selects appropriate functions to answer engineering questions about space mission designs.

Here are the available functions you can call:
1. get_architecture_scores(design_id, designs, context) - Get architecture scores for a specific design to know about the science benefit
2. get_satisfying_data_products(design_id, designs, subobjective, context) - Get data products that satisfy a subobjective for a design
3. get_unsatisfied_justifications(design_id, designs, subobjective, context) - Get explanations for why a subobjective is not satisfied
4. get_panel_scores(design_id, designs, panel, context) - Get panel scores for a specific design and panel
5. get_objective_scores(design_id, designs, objective, context) - Get objective scores for a specific design and objective
6. get_instruments_for_objective(objective, context) - Get instruments that contribute to an objective
7. get_instruments_for_stakeholder(stakeholder, context) - Get instruments related to a stakeholder
8. get_instrument_parameter(vassar_instrument, instrument_parameter, context, new_dialogue_contexts) - Get parameter value for an instrument
9. get_instrument_parameter_followup(vassar_instrument, instrument_parameter, instrument_measurement, context) - Get parameter value for an instrument and measurement
10. get_measurement_requirement(vassar_measurement, measurement_parameter, context, new_dialogue_contexts) - Get requirements for a measurement parameter
11. get_measurement_requirement_followup(vassar_measurement, instrument_parameter, subobjective, context) - Get requirements for a measurement parameter and subobjective
12. get_cost_explanation(design_id, designs, context) - Get cost explanation for a specific design

Based on this user query: "{query}"

And these extracted parameters: {json.dumps(parameters, indent=2)}

Determine which functions should be called to answer the query. 
NOTE: If the function requires a design_id, and the design_id in parameters is None or null, use the selected_arch_id from the context which is {context["screen"]["selected_arch_id"]}.
Return a list of function calls in the following JSON format:
[
  {{
    "function": "function_name",
    "arguments": {{
      "arg1": "value1",
      "arg2": "value2"
    }}
  }}
]

Only include functions that are necessary to answer the query, and only include parameters that are needed for those functions.
"""
        
        # response = self.model.invoke(prompt)
        response = getChatResponse(prompt)
        response = clean_chat_response(response)
        print("select_functions response: ", response)
        
        try:
            # Extract JSON from response
            response_text = response
            # Find JSON brackets
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            return []
        except Exception as e:
            logger.error(f"Error parsing function selection response: {e}")
            return []
    
    def process_query(self, query: str, problem, parameters: Dict, designs: List[Dict], context: Dict) -> str:
        """
        Process an engineering query and generate a response.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            designs: List of available designs
            context: Context information including screen ID
        
        Returns:
            Response to the user's query
        """
        print("designs", designs, designs[0])
        # Select which functions to call
        function_calls = self._select_functions(query, parameters, context)
        
        # Execute the selected functions
        function_results = []
        new_dialogue_contexts = {"engineer_context": type('obj', (object,), {})}
        
        for func_call in function_calls:
            function_name = func_call["function"]
            arguments = func_call["arguments"]
            
            try:
                # Map function names to actual functions
                if function_name == "get_architecture_scores":
                    design_id = None
                    print("arguments design id", arguments.get("design_id"))
                    if str(arguments["design_id"]) is None or str(arguments["design_id"]) == "None" or str(arguments["design_id"]) == "" or str(arguments["design_id"]) == "null" or str(arguments["design_id"]) == "undefined" or str(arguments["design_id"]) == "-1":
                        print("design_id is None so getting")
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                        
                    print("running get_architecture_scores", design_id, designs, context)    

                    result = get_architecture_scores(
                        design_id, 
                        designs, 
                        context
                    )
                elif function_name == "get_satisfying_data_products":
                    design_id = None
                    print("arguments design id", arguments.get("design_id"))
                    if str(arguments["design_id"]) is None or str(arguments["design_id"]) == "None" or str(arguments["design_id"]) == "" or str(arguments["design_id"]) == "null" or str(arguments["design_id"]) == "undefined" or str(arguments["design_id"]) == "-1":
                        print("design_id is None so getting")
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    result = get_satisfying_data_products(
                        design_id, 
                        designs, 
                        arguments.get("subobjective"), 
                        context
                    )
                elif function_name == "get_unsatisfied_justifications":
                    design_id = None
                    print("arguments design id", arguments.get("design_id"))
                    if str(arguments["design_id"]) is None or str(arguments["design_id"]) == "None" or str(arguments["design_id"]) == "" or str(arguments["design_id"]) == "null" or str(arguments["design_id"]) == "undefined" or str(arguments["design_id"]) == "-1":
                        print("design_id is None so getting")
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    result = get_unsatisfied_justifications(
                        design_id, 
                        designs, 
                        arguments.get("subobjective"), 
                        context
                    )
                elif function_name == "get_panel_scores":
                    design_id = None
                    print("arguments design id", arguments.get("design_id"))
                    if str(arguments["design_id"]) is None or str(arguments["design_id"]) == "None" or str(arguments["design_id"]) == "" or str(arguments["design_id"]) == "null" or str(arguments["design_id"]) == "undefined" or str(arguments["design_id"]) == "-1":
                        print("design_id is None so getting")
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    result = get_panel_scores(
                        design_id, 
                        designs, 
                        arguments.get("panel"), 
                        context
                    )
                elif function_name == "get_objective_scores":
                    design_id = None
                    print("arguments design id", arguments.get("design_id"))
                    if str(arguments["design_id"]) is None or str(arguments["design_id"]) == "None" or str(arguments["design_id"]) == "" or str(arguments["design_id"]) == "null" or str(arguments["design_id"]) == "undefined" or str(arguments["design_id"]) == "-1":
                        print("design_id is None so getting")
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    result = get_objective_scores(
                        design_id, 
                        designs, 
                        arguments.get("objective"), 
                        context
                    )
                elif function_name == "get_instruments_for_objective":
                    result = get_instruments_for_objective(
                        arguments.get("objective"), 
                        context
                    )
                elif function_name == "get_instruments_for_stakeholder":
                    result = get_instruments_for_stakeholder(
                        arguments.get("stakeholder"), 
                        context
                    )
                elif function_name == "get_instrument_parameter":
                    result = get_instrument_parameter(
                        arguments.get("vassar_instrument"), 
                        arguments.get("instrument_parameter"), 
                        context, 
                        new_dialogue_contexts
                    )
                elif function_name == "get_instrument_parameter_followup":
                    result = get_instrument_parameter_followup(
                        arguments.get("vassar_instrument"), 
                        arguments.get("instrument_parameter"), 
                        arguments.get("instrument_measurement"), 
                        context
                    )
                elif function_name == "get_measurement_requirement":
                    result = get_measurement_requirement(
                        arguments.get("vassar_measurement"), 
                        arguments.get("measurement_parameter"), 
                        context, 
                        new_dialogue_contexts
                    )
                elif function_name == "get_measurement_requirement_followup":
                    result = get_measurement_requirement_followup(
                        arguments.get("vassar_measurement"), 
                        arguments.get("instrument_parameter"), 
                        arguments.get("subobjective"), 
                        context
                    )
                elif function_name == "get_cost_explanation":
                    design_id = None
                    print("arguments design id", arguments.get("design_id"))
                    if str(arguments["design_id"]) is None or str(arguments["design_id"]) == "None" or str(arguments["design_id"]) == "" or str(arguments["design_id"]) == "null" or str(arguments["design_id"]) == "undefined" or str(arguments["design_id"]) == "-1":
                        print("design_id is None so getting")
                        design_id = context["screen"]["selected_arch_id"]
                        print("design_id newwww", design_id)
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    result = get_cost_explanation(
                        design_id, 
                        designs, 
                        context
                    )
                else:
                    logger.warning(f"Unknown function: {function_name}")
                    continue
                
                function_results.append({
                    "function": function_name,
                    "arguments": arguments,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Error executing function {function_name}: {e}")
                function_results.append({
                    "function": function_name,
                    "arguments": arguments,
                    "error": str(e)
                })

        print("function_results: ", function_results)
        
        # Generate a response using the results
        return self._generate_response(query, parameters, function_results)
    
    def _generate_response(self, query: str, parameters: Dict, function_results: List[Dict]) -> str:
        """
        Generate a response based on the function results.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            function_results: Results from the executed functions
        
        Returns:
            Formatted response to the user's query
        """
        prompt = f"""
You are an engineering assistant for Earth observation satellite mission design. 
Answer the user's query based on the information obtained from the relevant function calls.

User query: "{query}"

Parameters extracted from query: {json.dumps(parameters, indent=2)}

Results from function calls:
{json.dumps(function_results, indent=2, default=str)}

Based on this information, please provide a clear, concise, and informative answer to the user's query. Use the whole information.
Focus on the engineering aspects and technical details. Provide numerical details where available. 
Please be on point and donot provide additional information that is not relevant to the user query.
Answer:
"""
        
        response = getChatResponse(prompt)
        return response