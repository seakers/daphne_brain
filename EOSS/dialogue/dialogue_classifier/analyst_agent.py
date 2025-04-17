import json
import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response
import os
import sys
import django
from EOSS.dialogue.dialogue_classifier.design_filter_classifier import analyze_design_patterns
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daphne_brain.settings")
django.setup()
from EOSS.analyst.dialogue_functions import data_mining_run

logger = logging.getLogger('EOSS.dialogue.analyst_agent')

class AnalystAgent:
    """
    Agent that handles data analysis queries related to design features and patterns.
    """
    
    def __init__(self):
        """Initialize the Analyst agent."""
        pass

    def process_query(self, query: str, parameters: Dict, designs: List[Dict], context: Dict, session_key, problem, user_selected_ids, plot_data) -> str:
        """
        Process an analyst query and generate a response.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            designs: List of available designs
            context: Context information
        
        Returns:
            Response to the user's query
        """
        print(f"Processing analyst query: {query}")
        # print(f"With parameters: {parameters}")
        
        
        # Call the data mining function
        # try:
        design_id = None
        if "design_id" not in parameters or not parameters["design_id"]:
            design_id = context["screen"]["selected_arch_id"]
        else:
            design_id = str(parameters["design_id"])
            if design_id and design_id.startswith("D"):
                design_id = design_id[1:]  # Remove the first character "D"
            else:
                design_id = design_id
        selected_designs = []
        target_designs = None
        print("user_selected_ids", user_selected_ids)
        if user_selected_ids:
            filtered_designs = [design for design in designs if design.id in user_selected_ids]
            target_designs = filtered_designs
        print("target designs", target_designs) 
        results = analyze_design_patterns(query, design_id, session_key, problem, designs, target_designs=target_designs, context=context, plot_data=plot_data)
        if "selected_designs" in results:
            selected_designs = results["selected_designs"]
        
        print(f"Data mining results: {results}")
        
        if not results:
            return "I couldn't find any significant patterns in the designs. Try selecting a different region or adjusting your query."
        
        # Generate a response using the results
        return self._generate_response(query, parameters, results), selected_designs
        
        # except Exception as e:
        #     logger.error(f"Error in data mining: {e}")
        #     return "I encountered an error while analyzing the designs. Please try again or contact support if the problem persists."
    
    def _generate_response(self, query: str, parameters: Dict, results: List[Dict]) -> str:
        """
        Generate a response based on the data mining results.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            results: Results from data mining
            behavioral: Description of behavioral group
            non_behavioral: Description of non-behavioral group
        
        Returns:
            Formatted response to the user's query
        """
        if "type" in results and results["type"] == "filtered_designs":
            return results["message"]
        prompt = f"""
You are an analyst assistant for Earth observation satellite mission design. 
Answer the user's query based on the data mining results.

User query: "{query}"

Parameters extracted from query: {json.dumps(parameters, indent=2)}

Data mining results:
{json.dumps(results, indent=2, default=str)}

Based on this information, please provide a clear, concise, and informative answer to the user's query.
Include all the information from the message in resutls. Donot provide your own explanations.
Be clear and concise in your response.

Answer:
"""
        
        response = getChatResponse(prompt)
        return response