from enum import Enum
from typing import Annotated, Dict, List, TypedDict, Union, Tuple
from typing import Optional
from langchain_core.language_models import LLM
from langchain_ollama import ChatOllama
# from EOSS.dialogue.dialogue_classifier.substitutions import substitution_functions, load_data_sources
from EOSS.dialogue.dialogue_classifier.substitutions import substitution_functions, load_data_sources
from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response

import re

class IntentType(str, Enum):
    ANALYST = "ANALYST"
    ENGINEER = "ENGINEER"
    CRITIC = "CRITIC"
    HISTORIAN = "HISTORIAN"
    UNKNOWN = "UNKNOWN"

def classify_intent(query: str) -> IntentType:
    """
    Classify the user's query into one of the defined intent types.
    
    Args:
        query: The user's query text
        model: LLM model for classification
    
    Returns:
        IntentType: The classified intent
    """
    # Prepare a prompt for the LLM to classify the intent
    prompt = f"""
You are an intent classifier for a space mission design agent. You need to classify the following user query into one of these categories:
1. ANALYST: Queries about features, patterns, and designs in target regions
2. ENGINEER: Queries about science benefits, scores, and technical details of the designs, queries about the specific data values from the current dataset, queries about the current problem formulation.
3. CRITIC: Queries asking for opinions, comparisons, or suggestions about designs
4. HISTORIAN: Queries about historical missions, instruments, and technologies in the past

Here are examples of each type:

ANALYST examples:
- what are the features that are shared by the target designs
- what is the feature that is unique to the solutions in the target region
- what are the patterns that are found in the target designs
- what are the patterns that are found in the selected region
- what are the patterns that are found in good designs
- what are the patterns that are found in the high performance region
- what are the recurring patterns within the low-cost region
- what are the driving features
- what is the driving feature
- can you suggest a good feature that describes the target region well
- which feature can be found in the designs in the target region
- which feature covers all the solutions in the target region
- what feature covers the selected region well
- what is a good feature describing this target region
- what features describe the target region well
- what are the recurring patterns in the target region
- which of the designs have instrument X assigned to orbit Y
- highlight designs that assign instrument X in orbit Y
- show designs that assign instrument X in orbit Y
- which of the designs use instrument X
- which of the designs do not use instrument X
- highlight designs that does not use instrument X
- highlight designs that use instrument X
- which of the designs use N instruments in total
- what are the designs that use total N instruments
- what are the designs that assigns N instruments in orbit X
- which of the designs use N orbits
- highlight designs that use N orbits

ENGINEER examples:
- why does design X have this science benefit
- why does design X have this science score
- how does design X satisfy Y
- why does design X not satisfy Y
- who satisfies X in design Y
- how many objectives are fully/partially/not satisfied in design X
- which objectives are fully/partially/not satisfied in design X
- why is architecture X better than Y
- what are the differences between architecture X and Y
- what is the parameter of instrument X
- the one for measurement X
- what is the requirement for parameter X for measurement Y
- the one for objective X
- why does this design have this science benefit
- why does this design have this science score
- explain the stakeholder X science score for this design
- explain the stakeholder X science benefit for this design
- explain the objective X science score for this design
- explain the objective X science benefit for this design
- which instruments improve the science score for objective X
- which instruments improve the science benefit for objective X
- which instruments improve the science score for stakeholder X
- which instruments improve the science benefit for stakeholder X
- why does this design have this cost
- what requirements are not being satisfied
- how can this requirement be satisfied
- what does delta-v mean
- what is delta-v
- what does eccentricity mean
- what is eccentricity
- what does inclination mean
- what is inclination
- what is the mass of the BIOMASS instrument?
- what is the aperture size of VIIRS?
- what are the stakeholder objectives of the water panel?
- what are the scores for WEA1-1?
- what is the data rate of the SMAP radiometer?
- what are the instruments in the current problem formulation?
- what are the orbits in the current problem formulation?
- list all available orbits in this formulation
- list all available instruments in this formulation
- what are the instruments in the current problem formulation?
- what are the orbits in the current problem formulation?
- list all available orbits in this formulation
- list all available instruments in this formulation

CRITIC examples:
- are there any similar missions to X
- what does the agent think of design X
- does design X have any good features
- do you have any suggestion to improve design X
- what do you think of this design

HISTORIAN examples:
- which missions can measure X
- which missions can measure X between year1 and year2
- which missions from agency X can measure Y
- which missions from agency X can measure Y between year1 and year2
- which missions do we currently use to measure X
- which missions from agency X do we currently use to measure Y
- which instruments can measure X
- which instruments can measure X between year1 and year2
- which instruments from agency X can measure Y
- which instruments from agency X can measure Y between year1 and year2
- which instruments do we currently use to measure X
- which instruments from agency X do we currently use to measure Y
- which missions have flown technology X
- which missions have flown technology X between year1 and year2
- which missions from agency X have flown technology Y
- which missions from agency X have flown technology Y between year1 and year2
- which missions are currently flying technology X
- which missions from agency X are currently flying technology Y
- which orbit is the most common for technology X
- which orbit is the most typical for technology X
- what orbit do you recommend for technology X
- which orbit is the most common for measurement X
- which orbit is the most typical for measurement X
- what orbit do you recommend for measurement X
- when was mission X launched
- which missions have been launched by agency X
- which missions have been designed by agency X
- show me a timeline of missions which measure X
- show me a timeline of missions that measure X
- show me a timeline of missions from agency X which measure Y
- show me a timeline of missions from agency X that measure Y

Based on the above examples, classify the following user query:
"{query}"

Respond with EXACTLY one of these labels: ANALYST, ENGINEER, CRITIC, or HISTORIAN.
No explanation or additional text, just the label.
"""

    # Get the prediction from the model
    response = getChatResponse(prompt).upper()
    print("response", response)
    
    # Match the response to one of our defined intent types
    if IntentType.ANALYST.value in response:
        return IntentType.ANALYST
    elif IntentType.ENGINEER.value in response:
        return IntentType.ENGINEER
    elif IntentType.CRITIC.value in response:
        return IntentType.CRITIC
    elif IntentType.HISTORIAN.value in response:
        return IntentType.HISTORIAN
    else:
        return IntentType.UNKNOWN

def extract_parameters(query: str, intent_type: IntentType) -> Dict:
    # Define parameter extraction prompts based on intent type
    data_sources = load_data_sources()
    substitutions = substitution_functions()
    if intent_type == IntentType.ANALYST:
        ifeed_instruments = substitutions['instrument'](data_sources)
        
        prompt = f"""
TASK: Extract specific parameters from the critic query text below.

QUERY: "{query}"

RULES:
- For design_id: Extract as is and format if needed (add "D" prefix if just a number)
- DO NOT include parameters that aren't related to the query
- Only extract parameters that are relevant to the query content

Use these templates to identify which parameters to extract:
- what are the features that are shared by the target designs
- what is the feature that is unique to the solutions in the target region
- what are the patterns that are found in the target designs
- what are the patterns that are found in the selected region
- what are the patterns that are found in good designs
- what are the patterns that are found in the high performance region
- what are the recurring patterns within the low-cost region
- what are the driving features
- what is the driving feature
- can you suggest a good feature that describes the target region well
- which feature can be found in the designs in the target region
- which feature covers all the solutions in the target region
- what feature covers the selected region well
- what is a good feature describing this target region
- what features describe the target region well
- what are the recurring patterns in the target region
- which of the designs have instrument X assigned to orbit Y
- highlight designs that assign instrument X in orbit Y
- show designs that assign instrument X in orbit Y
- which of the designs use instrument X
- which of the designs do not use instrument X
- highlight designs that does not use instrument X
- highlight designs that use instrument X
- which of the designs use N instruments in total
- what are the designs that use total N instruments
- what are the designs that assigns N instruments in orbit X
- which of the designs use N orbits
- highlight designs that use N orbits

PARAMETERS TO EXTRACT:
1. design_id - Any architecture identifier (starts with D followed by a number or just a number)
2. orbits - Any number from 1 - 5
3. instrument - Any of these instruments: {ifeed_instruments}
2. agent - Any of these critic agents: expert, historian, analyst, explorer
3. compare_design_id - If comparing two designs, the second design ID

RESPONSE FORMAT:
Return a valid JSON object without any markdown formatting or code block syntax:
{{
  "design_id": "value or null",
  "agent": "value or null",
  "compare_design_id": "value or null"
}}

DO NOT wrap the JSON in code blocks.
DO NOT include ```json or ``` markers.
Only include parameters with actual values.
"""

    elif intent_type == IntentType.ENGINEER:
        subobjectives = substitutions['subobjective'](data_sources)
        objectives = substitutions['objective'](data_sources)
        vassar_instruments = substitutions['vassar_instrument'](data_sources)
        vassar_measurements = substitutions['vassar_measurement'](data_sources)
        vassar_stakeholders = substitutions['vassar_stakeholder'](data_sources)
        instrument_parameters = substitutions['instrument_parameter'](data_sources)
        # print("subobjectives", subobjectives)
        # print("objectives", objectives)
        # print("vassar_instruments", vassar_instruments)
        # print("vassar_measurements", vassar_measurements)
        # print("vassar_stakeholders", vassar_stakeholders)
        # print("instrument_parameters", instrument_parameters)
        # Convert lists to comma-separated strings for the prompt
        subobjectives_str = ", ".join(subobjectives)
        objectives_str = ", ".join(objectives)
        vassar_instruments_str = ", ".join(vassar_instruments)
        vassar_measurements_str = ", ".join(vassar_measurements)
        vassar_stakeholders_str = ", ".join(vassar_stakeholders)
        instrument_parameters_str = ", ".join(instrument_parameters)
        print("query", query)
        prompt = f"""
TASK: Extract specific parameters from the query text below.

QUERY: "{query}"

RULES:
- For design_id: Extract as is and format if needed (add "D" prefix if just a number)
- For parameters 2-7: Return the STANDARDIZED term from the provided lists when a match is found
- DO NOT include parameters that are synonyms or that aren't related to the query only take care of some misspellings
- Only extract parameters that are relevant to the query content

Use these templates to identify which parameters to extract:
- why does design X have this science benefit
- why does design X have this science score
- how does design X satisfy Y
- why does design X not satisfy Y
- who satisfies X in design Y
- how many objectives are fully/partially/not satisfied in design X
- which objectives are fully/partially/not satisfied in design X
- why is architecture X better than Y
- what are the differences between architecture X and Y
- what is the parameter of instrument X
- the one for measurement X
- what is the requirement for parameter X for measurement Y
- the one for objective X
- why does this design have this science benefit
- why does this design have this science score
- explain the stakeholder X science score for this design
- explain the stakeholder X science benefit for this design
- explain the objective X science score for this design
- explain the objective X science benefit for this design
- which instruments improve the science score for objective X
- which instruments improve the science benefit for objective X
- which instruments improve the science score for stakeholder X
- which instruments improve the science benefit for stakeholder X
- why does this design have this cost
- what requirements are not being satisfied
- how can this requirement be satisfied
- what does delta-v mean
- what is delta-v
- what does eccentricity mean
- what is eccentricity
- what does inclination mean
- what is inclination

PARAMETERS TO EXTRACT:
1. design_id - Any architecture identifier (starts with D followed by a number or just a number)
2. subobjective - Any of these terms: {subobjectives_str}
3. objective - Any of these terms: {objectives_str}
4. instrument_parameter - Any of these terms: {instrument_parameters_str}
5. vassar_instrument - Any of these instruments: {vassar_instruments_str}
6. vassar_measurement - Any of these measurements: {vassar_measurements_str}
7. vassar_stakeholder - Any of these stakeholders: {vassar_stakeholders_str}
8. not_partial_full - Any of these terms: not, partially, fully


RESPONSE FORMAT:
Return ONLY a valid JSON object:
{{
  "design_id": "value or null",
  "subobjective": "standardized_term or null",
  "objective": "standardized_term or null",
  "instrument_parameter": "standardized_term or null",
  "vassar_instrument": "standardized_term or null",
  "vassar_measurement": "standardized_term or null",
  "vassar_stakeholder": "standardized_term or null",
  "not_partial_full": "not/partially/fully or null"
}}
Include only parameters that are semantically present in the query.
DO NOT include any explanations or text outside the JSON object.
"""

    elif intent_type == IntentType.CRITIC:
        prompt = f"""
TASK: Extract specific parameters from the critic query text below.

QUERY: "{query}"

RULES:
- For design_id: Extract as is and format if needed (add "D" prefix if just a number)
- For agent: Return the STANDARDIZED agent type when mentioned (expert, historian, analyst, explorer)
- DO NOT include parameters that aren't related to the query
- Only extract parameters that are relevant to the query content

Use these templates to identify which parameters to extract:
- are there any similar missions to X
- what does the agent think of design X
- does design X have any good features
- do you have any suggestion to improve design X
- what do you think of this design
- how could design X be improved
- compare design X to design Y
- what are the strengths and weaknesses of design X
- what would an expert/historian/analyst/explorer say about design X

PARAMETERS TO EXTRACT:
1. design_id - Any architecture identifier (starts with D followed by a number or just a number)
2. agent - Any of these critic agents: expert, historian, analyst, explorer
3. compare_design_id - If comparing two designs, the second design ID

RESPONSE FORMAT:
Return a valid JSON object without any markdown formatting or code block syntax:
{{
  "design_id": "value or null",
  "agent": "value or null",
  "compare_design_id": "value or null"
}}

DO NOT wrap the JSON in code blocks.
DO NOT include ```json or ``` markers.
Only include parameters with actual values.
"""

    elif intent_type == IntentType.HISTORIAN:
        historian_measurement = substitutions["measurement"](data_sources)
        historian_technology = substitutions["technology"](data_sources)
        historian_space_agency = substitutions["space_agency"](data_sources)
        historian_mission = substitutions["mission"](data_sources)
        historian_measurement_str = ", ".join(historian_measurement)
        historian_technology_str = ", ".join(historian_technology)
        historian_space_agency_str = ", ".join(historian_space_agency)
        historian_mission_str = ", ".join(historian_mission)

        prompt = f"""
TASK: Extract specific parameters from the historian query text below.

QUERY: "{query}"

RULES:
- Extract ALL relevant parameters mentioned in the query
- For years, extract both individual years and year ranges
- For parameters 1,2,5,6: Return the STANDARDIZED term from the provided lists when a match is found
- DO NOT include parameters that are synonyms or that aren't related to the query only take care of some misspellings
- Also make sure to take care of any abbreviations or acronyms
- Only extract parameters that are relevant to the query content
- DO NOT include parameters that aren't explicitly mentioned

PARAMETERS TO EXTRACT:
1. measurement - Any of these terms: {historian_measurement_str}
2. technology - Any of these terms: {historian_technology_str}
3. year1 - Starting year of a time range or the specific year mentioned
4. year2 - Ending year of a time range (if a range is mentioned)
5. space_agency -  Any of these space agencies: {historian_space_agency_str}
6. mission - Any of these mission names: {historian_mission_str}
7. orbit - Any number from 1 - 5

Use these templates to identify which parameters to extract:
- which missions can measure X
- which missions can measure X between year1 and year2
- which missions from agency X can measure Y
- which missions from agency X can measure Y between year1 and year2
- which missions do we currently use to measure X
- which missions from agency X do we currently use to measure Y
- which instruments can measure X
- which instruments can measure X between year1 and year2
- which instruments from agency X can measure Y
- which instruments from agency X can measure Y between year1 and year2
- which instruments do we currently use to measure X
- which instruments from agency X do we currently use to measure Y
- which missions have flown technology X
- which missions have flown technology X between year1 and year2
- which missions from agency X have flown technology Y
- which missions from agency X have flown technology Y between year1 and year2
- which missions are currently flying technology X
- which missions from agency X are currently flying technology Y
- which orbit is the most common for technology X
- which orbit is the most typical for technology X
- what orbit do you recommend for technology X
- which orbit is the most common for measurement X
- which orbit is the most typical for measurement X
- what orbit do you recommend for measurement X
- when was mission X launched
- which missions have been launched by agency X
- which missions have been designed by agency X
- show me a timeline of missions which measure X
- show me a timeline of missions that measure X
- show me a timeline of missions from agency X which measure Y
- show me a timeline of missions from agency X that measure Y

RESPONSE FORMAT:
Return a valid JSON object without any markdown formatting or code block syntax:
{{
  "measurement": "value or null",
  "technology": "value or null",
  "year1": "value or null",
  "year2": "value or null",
  "space_agency": "value or null",
  "mission": "value or null",
  "orbit": "value or null",
  "instrument": "value or null"
}}

DO NOT wrap the JSON in code blocks.
DO NOT include ```json or ``` markers.
Only include parameters with actual values.
Include only parameters that are semantically present in the query.
DO NOT include any explanations or text outside the JSON object.
"""
    else:
        return {}

    # Get parameters from the model
    try:
        import json
        # response = model.invoke(prompt).content
        # response = clean_chat_response(response.content)
        print("hiiiiiiiiii")
        response = getChatResponse(prompt)
        print("got response")
        response = clean_chat_response(response)
        print("response", response)
        # Parse the response as JSON
        return json.loads(response)
    except Exception as e:
        print(f"Error extracting parameters: {e}")
        return {}


def classify_and_extract(query: str) -> Tuple[IntentType, Dict]:
    """
    Classify the intent and extract parameters from the query.
    
    Args:
        query: The user's query text
        model: LLM model for classification and extraction
    
    Returns:
        Tuple[IntentType, Dict]: The classified intent and extracted parameters
    """
    intent = classify_intent(query)
    parameters = extract_parameters(query, intent)
    return intent, parameters