import json
import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response
import os
import sys
import django
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daphne_brain.settings")
django.setup()
import re

from EOSS.dialogue.gpt_chat.db_client import Client
from EOSS.dialogue.gpt_chat.models import Mission, Instrument, Measurement, Agency, InstrumentType
from sqlalchemy import and_, or_, func
from EOSS.dialogue.gpt_chat.execute_funcs import (
    query_missions_by_measurement,
    query_current_missions_by_measurement,
    query_instruments_by_measurement,
    query_missions_by_technology,
    query_current_missions_by_technology,
    query_most_common_orbit_for_technology,
    query_most_common_orbit_for_measurement,
    query_mission_launch_date,
    query_missions_by_agency,
    query_mission_timeline_by_measurement,
    print_orbit,
    print_date
)

logger = logging.getLogger('EOSS.dialogue.historian_agent')

class HistorianAgent:
    """
    Agent that handles historical queries related to space missions, instruments, and technologies.
    """
    
    def __init__(self):
        """Initialize the Historian agent and database connection."""
        self.client = Client()
        self.session = self.client.get_session()
    
    def _select_functions(self, query: str, parameters: Dict) -> List[Dict]:
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
You are an agent that selects appropriate functions to answer historical questions about space missions, instruments, and technologies.

Here are the available functions you can call:
1. query_missions_by_measurement(parameters) - Get missions that can measure a specific parameter (parameters should include "measurement", and optionally "year1", "year2", "space_agency")
2. query_current_missions_by_measurement(parameters) - Get currently active missions that can measure a specific parameter (parameters should include "measurement", and optionally "space_agency")
3. query_instruments_by_measurement(parameters) - Get instruments that can measure a specific parameter (parameters should include "measurement", and optionally "year1", "year2", "space_agency")
4. query_missions_by_technology(parameters) - Get missions that have used a specific technology (parameters should include "technology", and optionally "year1", "year2", "space_agency")
5. query_current_missions_by_technology(parameters) - Get currently active missions that have used a specific technology (parameters should include "technology", and optionally "space_agency")
6. query_most_common_orbit_for_technology(parameters) - Get the most common orbit for a technology (parameters should include "technology")
7. query_most_common_orbit_for_measurement(parameters) - Get the most common orbit for measuring a specific parameter (parameters should include "measurement")
8. query_mission_launch_date(parameters) - Get the launch date of a specific mission (parameters should include "mission")
9. query_missions_by_agency(parameters) - Get missions built by a specific space agency (parameters should include "space_agency")
10. query_mission_timeline_by_measurement(parameters) - Get timeline data for missions that take a certain measurement (parameters should include "measurement", and optionally "space_agency")

Based on this user query: "{query}"

And these extracted parameters: {json.dumps(parameters, indent=2)}

Determine which functions should be called to answer the query.
If none of the available functions are suitable, respond with "custom_sql_query" as the function name.

Return a list of function calls in the following JSON format:
[
  {{
    "function": "function_name",
    "arguments": {{
      "parameters": {{
        "measurement": "value",
        "technology": "value",
        "year1": "value",
        "year2": "value",
        "space_agency": "value",
        "mission": "value"
      }}
    }}
  }}
]

Only include parameters that are relevant to the function and available in the extracted parameters.
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
                print("historian function calls: ", json_str)
                return json.loads(json_str)
            return []
        except Exception as e:
            logger.error(f"Error parsing function selection response: {e}")
            return []
    
    def _custom_sql_query(self, query: str, parameters: Dict) -> Dict:
        """
        Generate and execute a custom SQL query when standard functions don't match the query.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            
        Returns:
            Dict: Results of the custom query
        """
        prompt = f"""
You are a SQL expert who needs to create a SQLAlchemy query for a space mission database.

Database tables and their key columns:
1. Mission: id, name, launch_date, eol_date, status
2. Instrument: id, name, technology
3. Measurement: id, name
4. Agency: id, name
5. InstrumentType: id, name

Relationships:
- Missions have many Instruments (Mission.instruments)
- Instruments belong to many Missions (Instrument.missions)
- Instruments have many Measurements (Instrument.measurements)
- Missions have many Agencies (Mission.agencies)
- Instruments have many Types (Instrument.types)

Given this user query: "{query}"
And these extracted parameters: {json.dumps(parameters, indent=2)}

First, describe what data we need to retrieve to answer the query.
Then, write SQLAlchemy code that would generate the appropriate SQL query.
Use func.lower() for case-insensitive matching.
Format your response as Python code that can be executed.
Do not include imports or explanations, just the executable query code.

Example format:
Query to find missions with specific instruments
query = session.query(Mission.name).distinct()\ .join(Instrument, Mission.instruments)\ .filter(Instrument.name.like("%desired_instrument%"))\ .order_by(Mission.launch_date)

result = [row[0] for row in query.all()]

Your query:
"""
        
        response = getChatResponse(prompt)
        print("Custom SQL response:", response)
        
        try:
            # Try to execute the generated query code safely
            # Note: This is just extracting the query part, not actually executing arbitrary code
            code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', response, re.DOTALL)
            
            if code_blocks:
                query_code = code_blocks[0].strip()


                
                # Just return the query as a string - you'd need safer execution in a production environment
                return {
                    "query_type": "custom",
                    "query_code": query_code,
                    "result": "Custom query execution would go here - using the Historian's direct database access"
                }
            else:
                return {
                    "query_type": "custom",
                    "error": "No valid query code found in response"
                }
        except Exception as e:
            logger.error(f"Error with custom SQL query: {e}")
            return {
                "query_type": "custom",
                "error": f"Error processing custom query: {str(e)}"
            }
    
    def process_query(self, query: str, parameters: Dict, designs: List[Dict], context: Dict) -> str:
        """
        Process a historical query and generate a response.
        
        Args:
            query: The original user query
            parameters: Extracted parameters from the query
            designs: List of available designs (not used in historian but kept for API consistency)
            context: Context information (not used in historian but kept for API consistency)
        
        Returns:
            Response to the user's query
        """
        # Select which functions to call
        function_calls = self._select_functions(query, parameters)
        
        # Execute the selected functions
        function_results = []
        
        for func_call in function_calls:
            function_name = func_call["function"]
            arguments = func_call.get("arguments", {})
            
            try:
                # Map function names to actual functions
                if function_name == "query_missions_by_measurement":
                    result = query_missions_by_measurement(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_current_missions_by_measurement":
                    result = query_current_missions_by_measurement(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_instruments_by_measurement":
                    result = query_instruments_by_measurement(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_missions_by_technology":
                    result = query_missions_by_technology(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_current_missions_by_technology":
                    result = query_current_missions_by_technology(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_most_common_orbit_for_technology":
                    result = query_most_common_orbit_for_technology(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_most_common_orbit_for_measurement":
                    result = query_most_common_orbit_for_measurement(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_mission_launch_date":
                    result = query_mission_launch_date(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_missions_by_agency":
                    result = query_missions_by_agency(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "query_mission_timeline_by_measurement":
                    result = query_mission_timeline_by_measurement(arguments.get("parameters", {}))
                    function_results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                elif function_name == "custom_sql_query":
                    result = self._custom_sql_query(query, parameters)
                    function_results.append({
                        "function": function_name,
                        "arguments": {"query": query, "parameters": parameters},
                        "result": result
                    })
                    
                else:
                    logger.warning(f"Unknown function: {function_name}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error executing function {function_name}: {e}")
                function_results.append({
                    "function": function_name,
                    "arguments": arguments,
                    "error": str(e)
                })
        
        print("function_results: ", function_results)
        
        # If no functions were called or all failed, try a custom query
        if not function_results or all("error" in result for result in function_results):
            try:
                custom_result = self._custom_sql_query(query, parameters)
                function_results.append({
                    "function": "custom_sql_query",
                    "arguments": {"query": query, "parameters": parameters},
                    "result": custom_result
                })
            except Exception as e:
                logger.error(f"Error executing custom SQL query: {e}")
        
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
You are a historian assistant for Earth observation satellite missions. 
Answer the user's query based on the information obtained from the database queries.

User query: "{query}"

Parameters extracted from query: {json.dumps(parameters, indent=2)}

Results from function calls:
{json.dumps(function_results, indent=2, default=str)}

Based on this information, please provide a clear, concise, and informative answer to the user's query.
Focus on the historical aspects and factual information. Include dates, mission names, and other relevant details.
Use numbered lists or bullet points where appropriate.

If the results are empty or no information was found, acknowledge that and suggest how the user might refine their query.
If the results include a timeline of missions, format that information in a way that emphasizes the chronological sequence.

Based on this information, please provide a clear, concise, and informative answer to the user's query.
USE ONLY the information provided to you. DO NOT give your own explanations and any of your own full forms or opinions.
ONLY give the requested information.
DO NOT ask any additional questions to the user.
Use formatting and structure to make the response easy to read and understand wherever necessary.

Answer:
"""
        
        response = getChatResponse(prompt)
        return response
