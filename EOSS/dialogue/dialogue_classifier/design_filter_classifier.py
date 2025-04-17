import re
from django.forms.models import model_to_dict
import json
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
import sys
import os
from EOSS.data.problem_specific import get_orbit_dataset, get_instrument_dataset
from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response
from EOSS.dialogue.dialogue_classifier.design_filter import DesignFilter
from EOSS.analyst.dialogue_functions import data_mining_run

# Import LLM client - replace with your actual LLM client import
# from ...utils.llm_client import LLMClient
# For demonstration, using a placeholder

class FilterQueryType(Enum):
    SHARED_FEATURES = "shared_features"
    UNIQUE_FEATURES = "unique_features"
    RECURRING_PATTERNS = "recurring_patterns" 
    DRIVING_FEATURES = "driving_features"
    FILTER_DESIGNS = "filter_designs"
    UNKNOWN = "unknown"

class FilterParameter(Enum):
    INSTRUMENT = "instrument"
    ORBIT = "orbit"
    COUNT = "count"

class DesignFilterClassifier:
    """
    Classifies natural language queries about design patterns and features
    into structured filter operations.
    """
    
    def __init__(self, problem=None):
        """
        Initialize the classifier with an LLM client and problem definition
        """
        self.problem = problem
        
        # Load instrument and orbit names if available
        self.instrument_names = self._get_instrument_names()
        self.orbit_names = self._get_orbit_names()
        orbit_dataset = get_orbit_dataset(self.problem)
        instrument_dataset = get_instrument_dataset(self.problem)
        
        # Example questions for each query type - used for few-shot learning
        self.query_examples = {
            FilterQueryType.SHARED_FEATURES: [
                "what features are shared by the target designs?",
                "what patterns appear in all the selected designs?", 
                "what do the designs in this region have in common?",
                "what are the common characteristics of these designs?",
            ],
            FilterQueryType.RECURRING_PATTERNS: [
                "what are the recurring patterns within the low-cost region?",
                "what are the recurring patterns in the target region"
            ],
            FilterQueryType.UNIQUE_FEATURES: [
                "what features are unique to the target designs?",
                "what makes these designs different from others?",
                "what distinguishes this group of designs?",
                "what features are exclusive to designs in this region?",
            ],
            FilterQueryType.DRIVING_FEATURES: [
                "what are the driving features for good performance?",
                "which features lead to high science return?",
                "what patterns correlate with low cost?",
                "can you suggest a good feature that describes high-performing designs?",
            ],
            FilterQueryType.FILTER_DESIGNS: [
                "which designs have VIIRS in orbit LEO-600-polar-NA?",
                "show me designs that don't use BIOMASS",
                "highlight architectures with exactly 2 orbits",
                "find designs where CMIS and SMAP_RAD are in the same orbit",
            ]
        }
    
    def _get_instrument_names(self):
        """Get instrument names from problem definition"""
        instrument_dataset = get_instrument_dataset(self.problem)
        instrument_names = {}
        for i in range(len(instrument_dataset)):
            instrument_names[instrument_dataset[i]['name']] = i
        return instrument_names  # Return a dictionary instead of the dataset

    def _get_orbit_names(self):
        """Get orbit names from problem definition"""
        orbit_dataset = get_orbit_dataset(self.problem)
        orbit_names = {}
        for i in range(len(orbit_dataset)):
            orbit_names[orbit_dataset[i]['name']] = i
        return orbit_names
        
    def classify_query(self, query_text: str) -> Tuple[FilterQueryType, Dict[str, Any]]:
        """
        Classify a natural language query into a filter query type and extract parameters.
        
        Args:
            query_text: Natural language question from the user
            
        Returns:
            Tuple of (query_type, parameters)
        """
        query_text = query_text.lower().strip()
        
        # First try rule-based classification for common patterns

        # query_type, parameters = self._rule_based_classification(query_text)
        # print("query type after rule based:", query_type)
        
        # # If rule-based classification doesn't yield clear results, use LLM
        # if query_type == FilterQueryType.UNKNOWN:
        #     print("in llm based classification")
        query_type, parameters = self._llm_based_classification(query_text)
        
        return query_type, parameters
    
    def _rule_based_classification(self, query_text: str) -> Tuple[FilterQueryType, Dict[str, Any]]:
        """
        Attempt to classify the query using rule-based patterns.
        
        Args:
            query_text: Natural language question
            
        Returns:
            Tuple of (query_type, parameters)
        """
        parameters = {}
        
        # Check for shared/common feature patterns
        shared_patterns = [
            r"(?:what|which)(?:.*)(?:shared|common|all)(?:.*)(?:features|patterns|characteristics)",
            r"what do (?:.*) have in common",
        ]
        if any(re.search(pattern, query_text) for pattern in shared_patterns):
            return FilterQueryType.SHARED_FEATURES, parameters
            
        # Check for unique feature patterns
        unique_patterns = [
            r"(?:what|which)(?:.*)(?:unique|distinguish|exclusive)(?:.*)(?:features|patterns|characteristics)",
            r"what makes (?:.*) different from",
        ]
        if any(re.search(pattern, query_text) for pattern in unique_patterns):
            return FilterQueryType.UNIQUE_FEATURES, parameters
            
        # Check for driving feature patterns
        driving_patterns = [
            r"(?:what|which)(?:.*)(?:driving|good|best|important)(?:.*)(?:features|patterns|characteristics)",
            r"(?:features|patterns)(?:.*)(?:correlate|lead to|result in)(?:.*)(?:high|good|better)",
            r"suggest a (?:.*) feature",
        ]
        if any(re.search(pattern, query_text) for pattern in driving_patterns):
            return FilterQueryType.DRIVING_FEATURES, parameters
            
        # Check for specific filter patterns (more complex)
        filter_patterns = [
            r"(?:which|what|show|highlight|find)(?:.*)(?:designs|architectures)(?:.*)((?:have|contain|use|assign)(?:.*)|(?:don't|do not|doesn't|does not)(?:.*))",
        ]
        
        for pattern in filter_patterns:
            match = re.search(pattern, query_text)
            if match:
                # Extract filter parameters
                parameters = self._extract_filter_parameters(query_text)
                if parameters:
                    return FilterQueryType.FILTER_DESIGNS, parameters
        
        return FilterQueryType.UNKNOWN, {}
    
    def _extract_filter_parameters(self, query_text: str) -> Dict[str, Any]:
        """
        Extract filter parameters from query text.
        
        Args:
            query_text: Natural language question
            
        Returns:
            Dictionary of parameters
        """
        params = {}
        
        # Look for instrument names
        for name, idx in self.instrument_names.items():
            if name.lower() in query_text.lower():
                if 'instrument' not in params:
                    params['instrument'] = []
                params['instrument'].append((name, idx))
        
        # Look for orbit names or numbers
        for name, idx in self.orbit_names.items():
            if name.lower() in query_text.lower():
                if 'orbit' not in params:
                    params['orbit'] = []
                params['orbit'].append((name, idx))
                
        # Also look for orbit numbers
        orbit_number_pattern = r'orbit\s+(\d+)'
        for match in re.finditer(orbit_number_pattern, query_text):
            orbit_num = int(match.group(1))
            if orbit_num >= 0 and 'orbit' not in params:
                params['orbit'] = []
                params['orbit'].append((f"Orbit {orbit_num}", orbit_num))
                
        # Look for counts
        count_pattern = r'(\d+)\s+(?:orbit|instrument)'
        for match in re.finditer(count_pattern, query_text):
            count = int(match.group(1))
            if count > 0:
                params['count'] = count
                
        # Detect negation
        params['negated'] = any(neg in query_text for neg in ["don't", "do not", "doesn't", "does not", "not", "without"])
                
        # Detect relationship indicators
        params['together'] = any(word in query_text for word in ["together", "same orbit", "same", "co-located"])
        params['separate'] = any(word in query_text for word in ["separate", "different orbit", "apart"])
                
        return params
    
    def _llm_based_classification(self, query_text: str) -> Tuple[FilterQueryType, Dict[str, Any]]:
        """
        Use the LLM to classify the query when rule-based patterns don't match.
        
        Args:
            query_text: Natural language question
            
        Returns:
            Tuple of (query_type, parameters)
        """
        # Construct a prompt with examples for few-shot learning
        prompt = self._construct_classification_prompt(query_text)
        
        try:
            # Call LLM API
            response = getChatResponse(prompt)
            print("llm classification response:", response)
            
            # Parse the LLM response
            query_type, parameters = self._parse_llm_response(response, query_text)
            return query_type, parameters
            
        except Exception as e:
            print(f"Error in LLM classification: {str(e)}")
            return FilterQueryType.UNKNOWN, {}
    
    def _construct_classification_prompt(self, query_text: str) -> str:
        """
        Construct a prompt for the LLM to classify the query.
        
        Args:
            query_text: Natural language question
            
        Returns:
            Prompt string for the LLM
        """
        # Create a system prompt
        prompt = (
            "You are an expert in satellite design analysis. Your task is to classify the user's question "
            "into one of these categories and extract relevant parameters:\n\n"
            "1. SHARED_FEATURES - Questions about common patterns or features shared by designs\n"
            "2. UNIQUE_FEATURES - Questions about features that distinguish certain designs\n"
            "3. DRIVING_FEATURES - Questions about features that lead to good performance\n"
            "4. FILTER_DESIGNS - Questions asking to find/show specific designs\n\n"
        )
        
        # Add examples for few-shot learning
        prompt += "Here are some examples:\n\n"
        
        for query_type, examples in self.query_examples.items():
            prompt += f"Category: {query_type.value}\n"
            for ex in examples[:2]:  # Use 2 examples per category
                prompt += f"- Question: \"{ex}\"\n"
            prompt += "\n"
        
        # Add instrument and orbit information
        prompt += "Available instruments:\n"
        for name, idx in self.instrument_names.items():
            prompt += f"- {name} (id: {idx})\n"
        
        prompt += "\nAvailable orbits:\n"
        for name, idx in self.orbit_names.items():
            prompt += f"- {name} (id: {idx})\n"
        
        # Add the user's question
        prompt += f"\nNow classify this question: \"{query_text}\"\n\n"
        prompt += "Respond in JSON format with fields: category, instruments, orbits, count, negated, together, separate, pareto_rank, range_type \n"
        prompt += "ONLY return the JSON with the fields stated above. DO NOT return anything else. NO explanations or questions."
        prompt += "The range type can be exact, at_most or at_least. The pareto_rank is the rank of the pareto front. "
        prompt += "You get the pareto ranking when the user asks for a pareto designs like  Show me the Pareto front designs with ranking 5. If the user asks something like Show me the Pareto front designs with instrument BIOMASS, then give the pareto ranking as default 1 and instrument BIOMASS and so on in the JSON above."
        prompt += "When returning the intruments and orbits make sure to return in a list format with name and id - [intrument_name, instrument_id] or [orbit_name, orbit_id]. If multiple, return in a list of lists"
        
        return prompt
    
    def _parse_llm_response(self, response: str, query_text: str) -> Tuple[FilterQueryType, Dict[str, Any]]:
        """
        Parse the LLM response to extract classification and parameters.
        
        Args:
            response: LLM response
            query_text: Original query text (for fallback extraction)
            
        Returns:
            Tuple of (query_type, parameters)
        """
        try:
            # Try to find and parse JSON in the response
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                
                # Map the category string to enum
                category = result.get('category', '').strip().lower()
                query_type = FilterQueryType.UNKNOWN
                
                for qt in FilterQueryType:
                    if qt.value == category:
                        query_type = qt
                        break
                
                # Extract parameters
                parameters = {
                    'instrument': result.get('instruments', []),
                    'orbit': result.get('orbits', []),
                    'count': result.get('count'),
                    'negated': result.get('negated', False),
                    'together': result.get('together', False),
                    'separate': result.get('separate', False),
                    'pareto_rank': None,  # Initialize as None, will set properly below
                    'range_type': result.get('range_type', 'exact')
                }

                # Handle pareto_rank specially to account for different formats
                pareto_rank_raw = result.get('pareto_rank')
                if pareto_rank_raw is not None:
                    # Handle case where pareto_rank comes as a list
                    if isinstance(pareto_rank_raw, list) and len(pareto_rank_raw) > 0:
                        parameters['pareto_rank'] = pareto_rank_raw[0]  # Use first element
                    else:
                        parameters['pareto_rank'] = pareto_rank_raw  # Use as is

                print("parameters from llm response:", parameters)

                # Clean up parameters - we always want to keep pareto_rank even if 0
                parameters = {k: v for k, v in parameters.items() if k == 'pareto_rank' or (v is not None and bool(v))}
                print("cleaned parameters", parameters)
                
                return query_type, parameters
            else:
                # If no JSON found, try to extract query type from text
                for qt in FilterQueryType:
                    if qt.value.lower() in response.lower():
                        # Fall back to rule-based parameter extraction
                        params = self._extract_filter_parameters(query_text)
                        return qt, params
                
                return FilterQueryType.UNKNOWN, {}
                
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            return FilterQueryType.UNKNOWN, {}
    

    def build_filter_expression(self, query_type: FilterQueryType, 
                        parameters: Dict[str, Any]) -> Optional[str]:
        """
        Build a filter expression based on the classified query type and parameters.
        
        Args:
            query_type: The classified query type
            parameters: Extracted parameters
            
        Returns:
            Filter expression string or None if not applicable
        """
        if query_type != FilterQueryType.FILTER_DESIGNS:
            # Other query types don't need filter expressions
            return None
            
        # For FILTER_DESIGNS, we need to build a filter expression
        instruments = parameters.get('instrument', [])
        orbits = parameters.get('orbit', [])
        count = parameters.get('count')
        negated = parameters.get('negated', False)
        together = parameters.get('together', False)
        separate = parameters.get('separate', False)
        pareto_rank = parameters.get('pareto_rank')
        range_type = parameters.get('range_type', 'exact')
        
        # Initialize expressions list to build complex filters
        expressions = []
        
        # Add Pareto front ranking filter if specified
        if pareto_rank is not None:
            try:
                # Make sure pareto_rank is an integer
                pareto_rank = int(pareto_rank)
                if pareto_rank < 0:
                    pareto_rank = 0
            except (ValueError, TypeError):
                pareto_rank = 1  # Default to rank 1 if invalid
                
            if range_type == 'at_most':
                # Use the paretoFront[N] format which already implements <= logic in frontend
                pareto_expr = f"{{paretoFront[{pareto_rank}]}}"
            elif range_type == 'at_least':
                # For "at least", we need a combination of expressions
                # As seen in the frontend code, paretoFront[N] means rank <= N
                # So we need to use logic to create "rank >= N"
                max_rank = 15  # Maximum expected Pareto rank
                # Create an expression for each rank from pareto_rank to max_rank
                # and combine with OR to get rank >= pareto_rank
                rank_exprs = []
                
                for r in range(0, max_rank + 1):
                    if r >= pareto_rank:
                        # For each rank >= pareto_rank, create an expression for exactly that rank
                        if r == 0:
                            # For rank 1, it's simply paretoFront[1]
                            rank_expr = f"{{paretoFront[0]}}"
                        else:
                            # For rank > 1, it's designs in paretoFront[r] but not in paretoFront[r-1]
                            # This gives us exactly rank r
                            rank_expr = f"({{paretoFront[{r}]}})"
                        rank_exprs.append(rank_expr)
                
                # Combine all expressions with OR to get rank >= pareto_rank
                pareto_expr = "(" + "||".join(rank_exprs) + ")"
                print("pareto_expr for at_least:", pareto_expr)
            else:
                # For exact rank
                    # For rank 1, it's simply designs in paretoFront[1]
                pareto_expr = f"{{paretoFront[{pareto_rank}]}}"
        
            expressions.append(pareto_expr)
        
        # Add instrument presence filter
        if instruments and not orbits:
            for instr in instruments:
                instr_id = instr[1]
                instr_expr = f"{{present[;{instr_id};]}}"
                if negated:
                    instr_expr = f"~{instr_expr}"
                expressions.append(instr_expr)
        
        # Add instrument-in-orbit filter
        elif instruments and orbits:
            orbit_id = orbits[0][1]
            instr_ids = [str(i[1]) for i in instruments]
            if len(instr_ids) == 1:
                orbit_expr = f"{{inOrbit[{orbit_id};{instr_ids[0]};]}}"
            else:
                orbit_expr = f"{{inOrbit[{orbit_id};{','.join(instr_ids)};]}}"
            
            if negated:
                orbit_expr = f"~{orbit_expr}"
            expressions.append(orbit_expr)
        
        # Add orbital count filter
        if count is not None and not (instruments and orbits):
            if not orbits and not instruments:  # Count refers to orbits
                count_expr = f"{{numOrbits[;;{count}]}}"
                if negated:
                    count_expr = f"~{count_expr}"
                expressions.append(count_expr)
            elif orbits:  # Count refers to instruments in specific orbit
                orbit_id = orbits[0][1]
                count_expr = f"{{numInstruments[{orbit_id};;{count}]}}"
                if negated:
                    count_expr = f"~{count_expr}"
                expressions.append(count_expr)
        
        # Handle instruments together/separate case
        if together and len(instruments) >= 2:
            instr_ids = [str(i[1]) for i in instruments]
            together_expr = f"{{together[;{','.join(instr_ids)};]}}"
            if negated:
                together_expr = f"~{together_expr}"
            expressions.append(together_expr)
        
        elif separate and len(instruments) >= 2:
            instr_ids = [str(i[1]) for i in instruments]
            separate_expr = f"{{separate[;{','.join(instr_ids)};]}}"
            if negated:
                separate_expr = f"~{separate_expr}"
            expressions.append(separate_expr)
        
        # Combine expressions with AND operator
        print("expressions before combining:", expressions)
        if len(expressions) == 0:
            return None
        elif len(expressions) == 1:
            return expressions[0]
        else:
            # Combine multiple expressions with AND operator (& in this context)
            combined_expr = expressions[0]
            for expr in expressions[1:]:
                combined_expr = f"({combined_expr}&&{expr})"
            return combined_expr

    
    
    def process_query(self, query_text: str) -> Dict[str, Any]:
        """
        Process a natural language query about designs.
        
        Args:
            query_text: Natural language question
            
        Returns:
            Dictionary with classification results and filter expression
        """
        query_type, parameters = self.classify_query(query_text)
        print("Query type:", query_type)
        print("Parameters:", parameters)
        
        filter_expr = None
        if query_type == FilterQueryType.FILTER_DESIGNS:
            filter_expr = self.build_filter_expression(query_type, parameters)
        
        return {
            'query_text': query_text,
            'query_type': query_type.value,
            'parameters': parameters,
            'filter_expression': filter_expr
        }


# Integration with the main dialogue system
def process_design_filter_query(query_text, problem):
    """
    Process a natural language query about design filters.
    
    Args:
        query_text: The user's question
        problem: The problem definition
        llm_client: Optional LLM client
        
    Returns:
        Classification and filter results
    """
    classifier = DesignFilterClassifier(problem)
    print("in process design filter query")
    results = classifier.process_query(query_text)
    
    return results

def analyze_design_patterns(query, design_id, session_key, problem, designs, target_designs=None, context=None, plot_data=None):
    """
    Analyze patterns in design data to answer various questions about features and patterns.
    
    Args:
        problem: The problem definition
        designs: List of all designs
        target_designs: Subset of designs to analyze (e.g., selected region)
        query_type: Type of analysis to perform
        context: Additional context about the query
        
    Returns:
        Dictionary with analysis results
    """
    # Create filter with problem definition
    results = process_design_filter_query(query, problem)
    design_filter = DesignFilter(problem)
    query_type = results['query_type']

    print("Design filter results initial:", results)
    
    # If no target designs provided, use all designs
    
    designs_list = list(designs.values())
    
    if target_designs:
        print("First target design as dict:", target_designs[0])

    # print(f"Total designs: {len(designs_list)}")

    if designs_list:
        print("First design as dict:", designs_list[0])

    target_designs_list = []
    if target_designs:
        for i in target_designs:
            target_designs_list.append(model_to_dict(i))
    
    if not target_designs:
        target_designs = designs_list


        
    # Standardize the query type
    if not query_type:
        query_type = "shared_features"
    
    # Handle different query types
    if query_type in ["shared_features", "common_features", "recurring_patterns"]:
        shared_features = design_filter.find_shared_features(target_designs_list)
        return {
            "type": "shared_features",
            "features": shared_features[:10],  # Return top 10 shared features
            "count": len(shared_features),
            "message": f"Found {len(shared_features)} features shared by designs in the target region."
        }
        
    elif query_type in ["unique_features", "distinguishing_features"]:
        unique_features = design_filter.find_unique_features(target_designs_list, designs_list)
        return {
            "type": "unique_features",
            "features": unique_features[:10],  # Return top 10 unique features
            "count": len(unique_features),
            "message": f"Found {len(unique_features)} features unique to designs in the target region."
        }
        
    elif query_type in ["driving_features", "good_features"]:
        driving_features = results = data_mining_run(designs, design_id,  context, session_key, problem)
        return {
            "type": "driving_features",
            "features": driving_features[:10],  # Return top 10 driving features
            "count": len(driving_features),
            "message": f"Found {len(driving_features)} features that correlate with high performance."
        }
        
    elif query_type == "filter_designs":
        # Extract filter expression from context
        filter_expr = results['filter_expression']
        if not filter_expr:
            return {
                "type": "error",
                "message": "No filter expression provided."
            }
            
        # Apply filter to designs
        filtered_designs = [d for d in plot_data if design_filter.process_filter_expression(d, filter_expr)]
        
        # return {
        #     "type": "filtered_designs",
        #     "selected_designs": filter_expr,
        #     "count": len(filtered_designs),
        #     "filter": filter_expr,
        #     "filter_description": design_filter._describe_feature(filter_expr),
        #     "message": f"Found {len(filtered_designs)} designs matching the filter."
        # }
        filtered_count = len(filtered_designs)
        message = ""
        if filtered_count == 1:
            message = "I found 1 design matching your criteria. I've highlighted it on the tradespace plot for you."
        elif filtered_count <= 5:
            message = f"I found {filtered_count} designs matching your criteria. I've highlighted them on the tradespace plot so you can see them."
        else:
            message = f"I found {filtered_count} designs matching your filter. You can see them highlighted on the tradespace plot."
        return{
            "type": "filtered_designs",
            "message": message,
            "selected_designs": filter_expr,
            "filter_description": design_filter._describe_feature(filter_expr),
        }
        
    else:
        return {
            "type": "error",
            "message": f"Unknown query type: {query_type}"
        }


# Example usage
if __name__ == "__main__":
    # Sample problem definition
    sample_problem = {
        "extra": {
            "orbitNum": 3,
            "instrumentNum": 5,
            "orbits": [
                {"name": "LEO-600-polar"},
                {"name": "SSO-600-AM"},
                {"name": "SSO-800-DD"}
            ],
            "instruments": [
                {"name": "VIIRS"},
                {"name": "CMIS"},
                {"name": "SMAP"},
                {"name": "BIOMASS"},
                {"name": "ICESAT"}
            ]
        }
    }
    
    # Test queries
    test_queries = [
        "What features are shared by all designs in the target region?",
        "What distinguishes the designs in the high-performance region?",
        "Which patterns lead to good science return?",
        "Show me designs that have VIIRS in orbit 1",
        "Which architectures use exactly 2 orbits?",
        "Find designs where CMIS and SMAP are in the same orbit",
        "Highlight designs that don't use BIOMASS"
    ]
    
    # Process each query
    for query in test_queries:
        results = process_design_filter_query(query, sample_problem)
        print(f"\nQuery: {query}")
        print(f"Type: {results['query_type']}")
        if results['filter_expression']:
            print(f"Filter: {results['filter_expression']}")
        print(f"Parameters: {results['parameters']}")