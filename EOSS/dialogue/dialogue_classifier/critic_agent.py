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
from EOSS.critic.dialogue_functions import (
    general_call,
    specific_call
)

logger = logging.getLogger('EOSS.dialogue.critic_agent')

class CriticAgent:
    """
    Agent that handles critic queries related to space mission designs.
    """
    
    def __init__(self):
        """
        Initialize the Critic agent.
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
You are an agent that selects appropriate functions to answer criticism and evaluation questions about space mission designs.

Here are the available functions you can call:
1. general_call(design_id, designs, session_key, context) - Get general criticism from all critic agents for a design
2. specific_call(design_id, agent, designs, session_key, context) - Get criticism from a specific agent about a design

The agent parameter can be one of: 'expert', 'historian', 'analyst', or 'explorer'.

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
    
    def process_query(self, query: str, parameters: Dict, designs: List[Dict], context: Dict, session_key: str = None) -> str:
        """
        Process a critic query and generate a response.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            designs: List of available designs
            context: Context information including screen ID
            session_key: Session key for current user session
        
        Returns:
            Response to the user's query
        """
        # Select which functions to call
        function_calls = self._select_functions(query, parameters, context)
        
        # Execute the selected functions
        function_results = []
        
        for func_call in function_calls:
            function_name = func_call["function"]
            arguments = func_call["arguments"]
            
            try:
                # Map function names to actual functions
                if function_name == "general_call":
                    design_id = None
                    if "design_id" not in arguments or not arguments["design_id"]:
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    
                    print(f"Running general_call for design_id: {design_id}")
                    
                    result = general_call(
                        design_id,
                        designs, 
                        session_key, 
                        context
                    )
                    
                elif function_name == "specific_call":
                    design_id = None
                    if "design_id" not in arguments or not arguments["design_id"]:
                        design_id = context["screen"]["selected_arch_id"]
                    else:
                        design_id = str(arguments["design_id"])
                        if design_id and design_id.startswith("D"):
                            design_id = design_id[1:]  # Remove the first character "D"
                        else:
                            design_id = design_id
                    
                    agent = arguments.get("agent", "expert")
                    
                    print(f"Running specific_call for design_id: {design_id}, agent: {agent}")
                    
                    result = specific_call(
                        design_id,
                        agent,
                        designs,
                        session_key,
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
You are a critic assistant for Earth observation satellite mission design. 
Answer the user's query based on the information obtained from the relevant function calls.

User query: "{query}"

Parameters extracted from query: {json.dumps(parameters, indent=2)}

Results from function calls:
{json.dumps(function_results, indent=2, default=str)}

Based on this information, please provide a clear, concise, and informative answer to the user's query.
USE ONLY the information provided to you. DO NOT give your own explanations.
DO NOT ask any additional questions to the user.
Use formatting and structure to make the response easy to read and understand wherever necessary.
Answer:
"""
        
        response = getChatResponse(prompt)
        return response