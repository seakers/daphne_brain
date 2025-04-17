import logging
from EOSS.dialogue.dialogue_classifier.engineer_intent_classifier import EngineerIntentClassifier, EngineerQueryType
from EOSS.dialogue.dialogue_classifier.engineer_agent import EngineerAgent  # For current_design_questions
from EOSS.dialogue.dialogue_classifier.engineer_agent2 import EngineerAgent2  # For spreadsheet_lookup

logger = logging.getLogger('EOSS.dialogue.engineer_router')

class EngineerRouter:
    """Routes engineering queries to the appropriate agent based on intent classification"""
    
    def __init__(self):
        self.intent_classifier = EngineerIntentClassifier()
        self.design_agent = EngineerAgent() 
        self.spreadsheet_agent = EngineerAgent2() 
    
    def process_query(self, query: str, problem: str, parameters: dict = None, designs=None, context: dict = None):
        """
        Process an engineering query by routing to the appropriate agent
        
        Args:
            query: User's question
            problem: Problem domain/identifier
            parameters: Additional parameters from the dialogue system
            designs: Available designs data
            context: Context information

        Returns:
            Response from the appropriate agent
        """
        if parameters is None:
            parameters = {}
        if context is None:
            context = {}
            
        # Extract problem context if available
        problem_context = {
            "instruments": context.get("problem_instruments", []),
            "orbits": context.get("problem_orbits", [])
        }
        
        # Classify the query
        query_type = self.intent_classifier.classify_query(query, problem_context)
        print("Query classified as:", query_type.value)
        
        # Merge extracted parameters with provided parameters
        # parameters.update(extracted_params)
        
        # Route to appropriate agent based on classification
        if query_type == EngineerQueryType.SPREADSHEET_LOOKUP:
            logger.info(f"Routing query to spreadsheet agent")
            return self.spreadsheet_agent.process_query(query, problem, parameters, designs, context)
        
        elif query_type == EngineerQueryType.PROBLEM_CONTEXT:
            logger.info(f"Processing query about problem context")
            # For problem context queries, we need to format the information from the context
            return self._format_problem_context_response(query, problem_context)
        
        else:  # CURRENT_DESIGN_QUESTIONS or UNKNOWN
            logger.info(f"Routing query to design agent")
            return self.design_agent.process_query(query, problem, parameters, designs, context)
    
    def _format_problem_context_response(self, query: str, problem_context: dict) -> str:
        """Format response for queries about the current problem formulation"""
        query_lower = query.lower()
        response = []
        
        # Handle instrument-related queries
        if "instrument" in query_lower:
            instruments = problem_context.get("instruments", [])
            if instruments:
                response.append("Available instruments in the current problem:")
                for i, instrument in enumerate(instruments):
                    name = instrument.get("name", f"Instrument {i+1}")
                    response.append(f"- {name}")
                    # Add attributes if requested
                    if any(attr in query_lower for attr in ["details", "attributes", "properties", "specs"]):
                        for key, value in instrument.items():
                            if key != "name":
                                response.append(f"  • {key}: {value}")
            else:
                response.append("No instrument information is available for the current problem.")
        
        # Handle orbit-related queries
        elif "orbit" in query_lower:
            orbits = problem_context.get("orbits", [])
            if orbits:
                response.append("Available orbits in the current problem:")
                for i, orbit in enumerate(orbits):
                    name = orbit.get("name", f"Orbit {i+1}")
                    altitude = orbit.get("altitude", "N/A")
                    response.append(f"- {name} (altitude: {altitude})")
                    # Add more details if requested
                    if any(attr in query_lower for attr in ["details", "attributes", "properties", "specs"]):
                        for key, value in orbit.items():
                            if key not in ["name", "altitude"]:
                                response.append(f"  • {key}: {value}")
            else:
                response.append("No orbit information is available for the current problem.")
        
        # Generic problem information query
        else:
            response.append("Current problem information:")
            
            instruments = problem_context.get("instruments", [])
            orbits = problem_context.get("orbits", [])
            
            response.append(f"\nAvailable instruments: {len(instruments)}")
            for i, instrument in enumerate(instruments[:5]):  # Show first 5 only
                response.append(f"- {instrument.get('name', f'Instrument {i+1}')}")
            if len(instruments) > 5:
                response.append(f"... and {len(instruments) - 5} more")
                
            response.append(f"\nAvailable orbits: {len(orbits)}")
            for i, orbit in enumerate(orbits[:5]):  # Show first 5 only
                response.append(f"- {orbit.get('name', f'Orbit {i+1}')} (altitude: {orbit.get('altitude', 'N/A')})")
            if len(orbits) > 5:
                response.append(f"... and {len(orbits) - 5} more")
        
        return "\n".join(response)