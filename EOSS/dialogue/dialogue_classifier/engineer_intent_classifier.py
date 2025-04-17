import re
import json
from enum import Enum
from typing import Tuple, Dict, Any

from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response

class EngineerQueryType(Enum):
    CURRENT_DESIGN_QUESTIONS = "current_design_questions"  # For questions about specific designs
    SPREADSHEET_LOOKUP = "spreadsheet_lookup"             # For looking up data from spreadsheets
    PROBLEM_CONTEXT = "problem_context"                   # Questions about available instruments/orbits
    UNKNOWN = "unknown"                                   # Cannot determine the intent

class EngineerIntentClassifier:
    """Classifies engineering queries into appropriate categories to route to the right agent"""
    
    def __init__(self):
        # Examples for intent classification
        self.query_examples = {
            EngineerQueryType.CURRENT_DESIGN_QUESTIONS: [
                "Why does design X have this science benefit?",
                "Why does design X have this science score?",
                "How does design X satisfy Y?",
                "Why does design X not satisfy Y?",
                "Who satisfies X in design Y?",
                "How many objectives are fully/partially/not satisfied in design X?",
                "Which objectives are fully/partially/not satisfied in design X?",
                "Why is architecture X better than Y?",
                "What are the differences between architecture X and Y?",
                "What is the parameter of instrument X?",
                "The one for measurement X?",
                "What is the requirement for parameter X for measurement Y?",
                "The one for objective X?",
                "Why does this design have this science benefit?",
                "Why does this design have this science score?",
                "Explain the stakeholder X science score for this design?",
                "Explain the stakeholder X science benefit for this design?",
                "Explain the objective X science score for this design?",
                "Explain the objective X science benefit for this design?",
                "Which instruments improve the science score for objective X?",
                "Which instruments improve the science benefit for objective X?",
                "Which instruments improve the science score for stakeholder X?",
                "Which instruments improve the science benefit for stakeholder X?",
                "Why does this design have this cost?",
                "What requirements are not being satisfied?",
                "How can this requirement be satisfied?",
                "What does delta-v mean?", 
                "What is delta-v?",
                "What does eccentricity mean?",
                "What is eccentricity?",
                "What does inclination mean?",
                "What is inclination?",
            ],
            EngineerQueryType.SPREADSHEET_LOOKUP: [
                "What is the mass of the BIOMASS instrument?",
                "What is the aperture size of VIIRS?",
                "What are the stakeholder objectives of the water panel?",
                "What are the scores for WEA1-1?",
                "What is the data rate of the SMAP radiometer?"
            ],
            EngineerQueryType.PROBLEM_CONTEXT: [
                "What are the instruments in the current problem formulation?",
                "What are the orbits in the current problem formulation?",
                "List all available orbits in this formulation",
                "List all available instruments in this formulation",
            ]
        }
    
    def classify_query(self, query: str, problem_context: Dict = None) -> Tuple[EngineerQueryType, Dict[str, Any]]:
        """
        Classify an engineering query into appropriate category with relevant parameters.
        
        Args:
            query: The user's query string
            problem_context: Optional context about the current problem (instruments, orbits)
            
        Returns:
            Tuple of (query_type, extracted_parameters)
        """
        # Rule-based classification for common patterns
        query_lower = query.lower()
        
        # Extract parameters that might be useful
        prompt = self._build_classification_prompt(query)
        response = getChatResponse(prompt)
        cleaned_response = clean_chat_response(response)
        
        if "spreadsheet_lookup" in cleaned_response:
            return EngineerQueryType.SPREADSHEET_LOOKUP
        elif "current_design_questions" in cleaned_response:
            return EngineerQueryType.CURRENT_DESIGN_QUESTIONS
        elif "problem_context" in cleaned_response:
            return EngineerQueryType.PROBLEM_CONTEXT
        
        # Fallback to heuristics if LLM response doesn't contain the expected strings
        print(f"LLM classification unclear: '{cleaned_response}', using fallback heuristics")
        
        if any(term in query_lower for term in ["mass", "power", "data rate", "aperture", "what is", "what are"]):
            return EngineerQueryType.SPREADSHEET_LOOKUP
        elif any(term in query_lower for term in ["design", "architecture", "satisfy", "science score"]):
            return EngineerQueryType.CURRENT_DESIGN_QUESTIONS
        
        return EngineerQueryType.UNKNOWN 
    
    def _build_classification_prompt(self, query: str) -> str:
        """Build prompt for LLM to classify engineering queries"""
        prompt = "You are helping to classify engineering questions about satellite missions into different categories.\n\n"
        prompt += "Categories:\n"
        prompt += "1. current_design_questions: Questions about specific designs/architectures, science scores, requirements satisfaction, objectives and subobjectives, etc.\n"
        prompt += "2. spreadsheet_lookup: Questions asking for specific data values from reference data, typically 'what is the X of Y'.\n"
        prompt += "3. problem_context: Questions about the current problem formulation, available instruments, orbits, etc.\n\n"
        
        prompt += "Examples of each category:\n\n"
        for query_type, examples in self.query_examples.items():
            prompt += f"Category: {query_type.value}\n"
            for ex in examples:
                prompt += f"- \"{ex}\"\n"
            prompt += "\n"
        
        prompt += f"Now classify this question: \"{query}\"\n"
        prompt += "Respond only with the category name. DONOT return anything else. Just return one of current_design_questions, spreadsheet_lookup, problem_context"
        
        return prompt