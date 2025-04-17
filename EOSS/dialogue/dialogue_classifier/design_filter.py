import json
import re
from typing import List, Dict, Any, Union, Callable, Optional
from EOSS.data.problem_specific import get_orbit_dataset, get_instrument_dataset

class DesignFilter:
    """
    A class to filter designs and identify patterns based on different criteria.
    Parallels the functionality in eoss-filter.js for analyzing satellite designs.
    """
    
    def __init__(self, problem=None):
        """
        Initialize the filter with problem definition
        """
        self.problem = problem
        # Define preset filter types
        self.preset_filters = {
            'present': self.filter_present,
            'absent': self.filter_absent,
            'inOrbit': self.filter_in_orbit,
            'notInOrbit': self.filter_not_in_orbit,
            'together': self.filter_together,
            'separate': self.filter_separate,
            'emptyOrbit': self.filter_empty_orbit,
            'numOrbits': self.filter_num_orbits,
            'numInstruments': self.filter_num_instruments,
            'subsetOfInstruments': self.filter_subset_of_instruments,
            'paretoFront': self.filter_pareto_front
        }
    
    def remove_outer_parentheses(self, expression: str) -> str:
        """Remove outer parentheses from expression if present"""
        if expression.startswith('(') and expression.endswith(')'):
            # Check if these are actually matching outer parentheses
            count = 0
            for i in range(len(expression) - 1):  # Skip the last char
                if expression[i] == '(':
                    count += 1
                elif expression[i] == ')':
                    count -= 1
                if count == 0 and i < len(expression) - 1:
                    # Found a closing parenthesis before the end, not outer parentheses
                    return expression
            return expression[1:-1]
        return expression
    
    def process_filter_expression(self, design: Dict[str, Any], expression: str, logic: str = None) -> bool:
        """
        Process a filter expression and check if a design satisfies it.
        Handles complex nested expressions with AND/OR logic.
        
        Args:
            design: The design to check
            expression: The filter expression
            logic: The logical operator (None for first filter, '&&' or '||' for subsequent)
            
        Returns:
            Boolean indicating if the design satisfies the filter
        """
        # Remove outer parentheses
        expression = self.remove_outer_parentheses(expression)
        
        # Handle simple expressions
        if '&&' not in expression and '||' not in expression:
            return self.apply_preset_filter(expression, design)
        
        # Split by operators while respecting parentheses
        parts = self._split_expression_respecting_parentheses(expression)
        
        result = None
        current_logic = None
        
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Even indices are expressions
                sub_result = self.process_filter_expression(design, part)
                
                if result is None:
                    result = sub_result
                elif current_logic == '&&':
                    result = result and sub_result
                elif current_logic == '||':
                    result = result or sub_result
            else:  # Odd indices are operators
                current_logic = part
                
        return result
    
    def _split_expression_respecting_parentheses(self, expression: str) -> List[str]:
        """Split expression by && and || while respecting parentheses"""
        result = []
        current = ""
        paren_level = 0
        
        i = 0
        while i < len(expression):
            # Check for && or ||
            if (i+1 < len(expression) and 
                (expression[i:i+2] == '&&' or expression[i:i+2] == '||') and 
                paren_level == 0):
                result.append(current)
                result.append(expression[i:i+2])
                current = ""
                i += 2
                continue
                
            # Track parentheses
            if expression[i] == '(':
                paren_level += 1
            elif expression[i] == ')':
                paren_level -= 1
                
            current += expression[i]
            i += 1
            
        if current:
            result.append(current)
            
        return result
    def apply_preset_filter(self, expression, design):
        """
        Apply a preset filter to a design
        
        Args:
            expression: Filter expression like {filterType[params]}
            design: Design to check
            
        Returns:
            True if design satisfies the filter, False otherwise
        """
        # Extract filter from curly braces
        if expression.startswith('{') and expression.endswith('}'):
            expression = expression[1:-1]
        
        # Handle negation
        flip = False
        if expression.startswith('~'):
            flip = True
            expression = expression[1:]
        
        # Parse filter type and parameters
        filter_type = expression.split('[')[0]
        params = expression.split('[')[1].rsplit(']', 1)[0]
        
        # Special handling for paretoFront filter which has a different parameter format
        if filter_type == 'paretoFront':
            # For paretoFront[4], the rank is the entire params string
            orbit = ''
            instr = ''
            numb = params  # Use the entire params as the rank number
        else:
            # Standard parameter format with semicolons
            param_parts = params.split(';')
            orbit = param_parts[0] if len(param_parts) > 0 else ''
            instr = param_parts[1] if len(param_parts) > 1 else ''
            numb = param_parts[2] if len(param_parts) > 2 else ''
        
        # Get inputs from design
        inputs = design.get('inputs', [])
        if isinstance(inputs, str):
            inputs = json.loads(inputs)
            
        # Apply the filter
        if filter_type in self.preset_filters:
            result = self.preset_filters[filter_type](inputs, orbit, instr, numb, design)
            return not result if flip else result
        else:
            # Unknown filter type
            return False
    
    def _get_num_orbits(self) -> int:
        """Get the number of orbits from problem definition"""
        return len(self._get_orbit_names())
    
    def _get_num_instruments(self) -> int:
        """Get the number of instruments from problem definition"""
        return len(self._get_instrument_names())
    
    def filter_present(self, bit_string, orbit, instr, numb, design):
        """Check if an instrument is present in any orbit"""
        if instr == '' or instr == '-1':
            return False
        
        instr = int(instr)
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        # print("bit_string", bit_string)
        # print("orbit", num_orbits)
        # print("num instruments", num_instruments)
        for i in range(num_orbits):
            if bit_string[num_instruments * i + instr]:
                return True
        return False
    
    def filter_absent(self, bit_string, orbit, instr, numb, design):
        """Check if an instrument is absent from all orbits"""
        if instr == '' or instr == '-1':
            return False
        
        instr = int(instr)
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        
        for i in range(num_orbits):
            if bit_string[num_instruments * i + instr]:
                return False
        return True
    
    def filter_in_orbit(self, bit_string, orbit, instr, numb, design):
        """Check if specified instruments are in a specific orbit"""
        if orbit == '' or instr == '':
            return False
        
        orbit = int(orbit)
        num_instruments = self._get_num_instruments()
        
        if ',' not in instr:
            # Single instrument
            instr = int(instr)
            return bit_string[orbit * num_instruments + instr]
        else:
            # Multiple instruments
            instruments = [int(i) for i in instr.split(',')]
            for instrument in instruments:
                if not bit_string[orbit * num_instruments + instrument]:
                    return False
            return True
    
    def filter_not_in_orbit(self, bit_string, orbit, instr, numb, design):
        """Check if specified instruments are not in a specific orbit"""
        if orbit == '' or instr == '':
            return False
        
        orbit = int(orbit)
        num_instruments = self._get_num_instruments()
        
        if ',' not in instr:
            # Single instrument
            instr = int(instr)
            return not bit_string[orbit * num_instruments + instr]
        else:
            # Multiple instruments
            instruments = [int(i) for i in instr.split(',')]
            for instrument in instruments:
                if bit_string[orbit * num_instruments + instrument]:
                    return False
            return True
    
    def filter_together(self, bit_string, orbit, instr, numb, design):
        """Check if specified instruments are together in any orbit"""
        if instr == '':
            return False
        
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        instruments = [int(i) for i in instr.split(',')]
        
        for o in range(num_orbits):
            all_present = True
            for instrument in instruments:
                if not bit_string[o * num_instruments + instrument]:
                    all_present = False
                    break
            if all_present:
                return True
        return False
    
    def filter_separate(self, bit_string, orbit, instr, numb, design):
        """Check if specified instruments are in separate orbits"""
        if instr == '':
            return False
        
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        instruments = [int(i) for i in instr.split(',')]
        
        for o in range(num_orbits):
            found_instruments = 0
            for instrument in instruments:
                if bit_string[o * num_instruments + instrument]:
                    found_instruments += 1
                    if found_instruments > 1:
                        return False
        return True
    
    def filter_empty_orbit(self, bit_string, orbit, instr, numb, design):
        """Check if an orbit is empty"""
        if orbit == '':
            return False
        
        orbit = int(orbit)
        num_instruments = self._get_num_instruments()
        
        for i in range(num_instruments):
            if bit_string[orbit * num_instruments + i]:
                return False
        return True
    
    def filter_num_orbits(self, bit_string, orbit, instr, numb, design):
        """Check if design uses a specific number of orbits"""
        if numb == '':
            return False
        
        target_count = int(numb)
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        # print("num_orbits", num_orbits)
        # print("num_instruments", num_instruments)
        
        orbit_count = 0
        # print("length of bit_string", len(bit_string))
        for o in range(num_orbits):
            for i in range(num_instruments):
                if bit_string[o * num_instruments + i]:
                    orbit_count += 1
                    break
        
        return orbit_count == target_count
    
    def filter_num_instruments(self, bit_string, orbit, instr, numb, design):
        """Count instruments based on parameters"""
        if numb == '':
            return False
        
        target_count = int(numb)
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        
        count = 0
        if orbit == '':
            # Count across all orbits
            if instr == '':
                # Count all instruments in all orbits
                for o in range(num_orbits):
                    for i in range(num_instruments):
                        if bit_string[o * num_instruments + i]:
                            count += 1
            else:
                # Count specific instrument across all orbits
                instr = int(instr)
                for o in range(num_orbits):
                    if bit_string[o * num_instruments + instr]:
                        count += 1
        else:
            # Count in specific orbit
            orbit = int(orbit)
            for i in range(num_instruments):
                if bit_string[orbit * num_instruments + i]:
                    count += 1
        
        return count == target_count
    
    def filter_subset_of_instruments(self, bit_string, orbit, instr, numb, design):
        """Check if a subset of instruments meets count criteria"""
        if orbit == '' or instr == '' or numb == '':
            return False
        
        orbit = int(orbit)
        num_instruments = self._get_num_instruments()
        instruments = [int(i) for i in instr.split(',')]
        
        count = sum(1 for i in instruments if bit_string[orbit * num_instruments + i])
        
        if ',' in numb:
            min_count, max_count = map(int, numb.split(','))
            return min_count <= count <= max_count
        else:
            min_count = int(numb)
            return count >= min_count
    
    def filter_pareto_front(self, bit_string, orbit, instr, numb, design):
        """Check if design is on Pareto front with rank <= specified"""
        # print("designnsssssssss", design)
        if 'paretoRanking' not in design:
            return False
        
        rank = design['paretoRanking']
        # print("number of pareto ranks", numb)
        # print("rank", rank)
        target_rank = int(numb) 
        return int(rank) <= int(target_rank)
    
    def find_shared_features(self, designs, feature_expressions=None):
        """
        Find features shared by all designs in the target region.
        Returns a list of features that are common across all designs.
        """
        if not designs:
            return []
        
        print("total shared designs", len(designs))
            
        # If no expressions provided, generate standard ones to test
        if not feature_expressions:
            feature_expressions = self._generate_feature_expressions()
            
        shared_features = []
        
        for expr in feature_expressions:
            all_satisfied = True
            for design in designs:
                if not self.process_filter_expression(design, expr):
                    all_satisfied = False
                    break
            
            if all_satisfied:
                shared_features.append({
                    'expression': expr,
                    'description': self._describe_feature(expr)
                })
        print("shaed features", shared_features)
        return shared_features
    
    def find_unique_features(self, target_designs, all_designs):
        """
        Find features unique to the target region compared to all designs.
        Returns features that appear in target designs but rarely in others.
        """
        if not target_designs:
            return []
            
        feature_expressions = self._generate_feature_expressions()
        unique_features = []
        
        for expr in feature_expressions:
            # Check if feature applies to target designs
            target_match_count = sum(1 for d in target_designs if self.process_filter_expression(d, expr))
            target_coverage = target_match_count / len(target_designs)
            
            # Only consider features with good coverage of target designs
            if target_coverage < 0.8:  # At least 80% of target designs have this feature
                continue
                
            # Check if feature is rare in all designs
            all_match_count = sum(1 for d in all_designs if self.process_filter_expression(d, expr))
            all_coverage = all_match_count / len(all_designs) if all_designs else 0
            
            # Calculate uniqueness
            uniqueness_score = target_coverage / all_coverage if all_coverage > 0 else float('inf')
            
            if uniqueness_score > 2:  # At least twice as common in target designs
                unique_features.append({
                    'expression': expr,
                    'description': self._describe_feature(expr),
                    'targetCoverage': target_coverage,
                    'overallCoverage': all_coverage,
                    'uniquenessScore': uniqueness_score
                })
        
        # Sort by uniqueness score
        unique_features.sort(key=lambda x: x['uniquenessScore'], reverse=True)
        return unique_features
    
    def find_driving_features(self, designs, performance_key='outputs'):
        """
        Find features that correlate with high performance.
        Returns features that most strongly predict good outcomes.
        """
        if not designs:
            return []
            
        feature_expressions = self._generate_feature_expressions()
        feature_scores = []
        
        # Calculate average performance across all designs
        all_performances = []
        for design in designs:
            if performance_key in design:
                if isinstance(design[performance_key], list):
                    # Assuming first value is science/performance
                    perf = design[performance_key][0]
                    all_performances.append(perf)
        
        baseline_performance = sum(all_performances) / len(all_performances) if all_performances else 0
        
        for expr in feature_expressions:
            # Find designs that match this feature
            matching_designs = [d for d in designs if self.process_filter_expression(d, expr)]
            
            # Skip if too few matches
            if len(matching_designs) < 5:
                continue
                
            # Calculate average performance for matching designs
            matching_performances = []
            for design in matching_designs:
                if performance_key in design:
                    if isinstance(design[performance_key], list):
                        # Assuming first value is science/performance
                        perf = design[performance_key][0]
                        matching_performances.append(perf)
            
            avg_performance = sum(matching_performances) / len(matching_performances) if matching_performances else 0
            
            # Calculate performance lift
            performance_lift = avg_performance / baseline_performance if baseline_performance > 0 else 0
            
            # Calculate coverage
            coverage = len(matching_designs) / len(designs)
            
            feature_scores.append({
                'expression': expr,
                'description': self._describe_feature(expr),
                'performance_lift': performance_lift,
                'coverage': coverage,
                'score': performance_lift * coverage  # Combined score
            })
        
        # Sort by combined score
        feature_scores.sort(key=lambda x: x['score'], reverse=True)
        return feature_scores
    
    def _generate_feature_expressions(self):
        """
        Generate common feature expressions to test against designs.
        """
        expressions = []
        num_orbits = self._get_num_orbits()
        num_instruments = self._get_num_instruments()
        
        # Generate presence/absence filters
        for i in range(num_instruments):
            expressions.append(f"{{present[;{i};]}}")
            expressions.append(f"{{absent[;{i};]}}")
        
        # Generate orbit assignment filters
        for o in range(num_orbits):
            for i in range(num_instruments):
                expressions.append(f"{{inOrbit[{o};{i};]}}")
                expressions.append(f"{{notInOrbit[{o};{i};]}}")
        
        # Generate empty orbit filters
        for o in range(num_orbits):
            expressions.append(f"{{emptyOrbit[{o};;]}}")
        
        # Generate instrument pairs
        for i in range(num_instruments):
            for j in range(i+1, num_instruments):
                expressions.append(f"{{together[;{i},{j};]}}")
                expressions.append(f"{{separate[;{i},{j};]}}")
        
        # Generate number of orbits filters
        for n in range(1, num_orbits + 1):
            expressions.append(f"{{numOrbits[;;{n}]}}")
        
        # Generate number of instruments filters
        for n in range(1, num_instruments + 1):
            expressions.append(f"{{numInstruments[;;{n}]}}")
            for o in range(num_orbits):
                expressions.append(f"{{numInstruments[{o};;{n}]}}")

        print("generated feature expressions", expressions)
        
        return expressions
    
    def _describe_feature(self, expression):
        """
        Convert a feature expression to a human-readable description.
        """
        # Remove curly braces
        if expression.startswith('{') and expression.endswith('}'):
            expression = expression[1:-1]
        
        # Handle negation
        negated = False
        if expression.startswith('~'):
            negated = True
            expression = expression[1:]
        
        try:
            filter_type = expression.split('[')[0]
            params = expression.split('[')[1].rsplit(']', 1)[0]
            param_parts = params.split(';')
            orbit = param_parts[0] if len(param_parts) > 0 else ''
            instr = param_parts[1] if len(param_parts) > 1 else ''
            numb = param_parts[2] if len(param_parts) > 2 else ''
            
            # Get instrument and orbit names if available
            instrument_names_dict = self._get_instrument_names()
            orbit_names_dict = self._get_orbit_names()

            instrument_names = {id: name for name, id in instrument_names_dict.items()}
            orbit_names = {id: name for name, id in orbit_names_dict.items()}

            print("instrument names", instrument_names)
            print("orbit names", orbit_names)
            
            # Format based on filter type
            if filter_type == 'present':
                instr_id = int(instr)
                instr_name = instrument_names.get(instr_id, f"Instrument {instr}")
                return f"{'Does not have' if negated else 'Has'} {instr_name}" 
                
            elif filter_type == 'absent':
                instr_id = int(instr)
                instr_name = instrument_names.get(instr_id, f"Instrument {instr}")
                return f"{'Has' if negated else 'Does not have'} {instr_name}"
                
            elif filter_type == 'inOrbit':
                orbit_id = int(orbit)
                orbit_name = orbit_names.get(orbit_id, f"Orbit {orbit}")
                
                if ',' in instr:
                    instr_ids = [int(i) for i in instr.split(',')]
                    instr_names = [instrument_names.get(i, f"Instrument {i}") for i in instr_ids]
                    instr_text = ", ".join(instr_names)
                    return f"{'Does not have' if negated else 'Has'} {instr_text} in {orbit_name}"
                else:
                    instr_id = int(instr)
                    instr_name = instrument_names.get(instr_id, f"Instrument {instr}")
                    return f"{'Does not have' if negated else 'Has'} {instr_name} in {orbit_name}"
                    
            elif filter_type == 'notInOrbit':
                orbit_id = int(orbit)
                orbit_name = orbit_names.get(orbit_id, f"Orbit {orbit}")
                
                if ',' in instr:
                    instr_ids = [int(i) for i in instr.split(',')]
                    instr_names = [instrument_names.get(i, f"Instrument {i}") for i in instr_ids]
                    instr_text = ", ".join(instr_names)
                    return f"{'Has' if negated else 'Does not have'} {instr_text} in {orbit_name}"
                else:
                    instr_id = int(instr)
                    instr_name = instrument_names.get(instr_id, f"Instrument {instr}")
                    return f"{'Has' if negated else 'Does not have'} {instr_name} in {orbit_name}"
            
            elif filter_type == 'together':
                instr_ids = [int(i) for i in instr.split(',')]
                instr_names = [instrument_names.get(i, f"Instrument {i}") for i in instr_ids]
                instr_text = " and ".join(instr_names)
                return f"{instr_text} are {'not' if negated else ''} in the same orbit"
                
            elif filter_type == 'separate':
                instr_ids = [int(i) for i in instr.split(',')]
                instr_names = [instrument_names.get(i, f"Instrument {i}") for i in instr_ids]
                instr_text = " and ".join(instr_names)
                return f"{instr_text} are {'in' if negated else 'not in'} the same orbit"
                
            elif filter_type == 'emptyOrbit':
                orbit_id = int(orbit)
                orbit_name = orbit_names.get(orbit_id, f"Orbit {orbit}")
                return f"{orbit_name} is {'not' if negated else ''} empty"
                
            elif filter_type == 'numOrbits':
                n = int(numb)
                return f"{'Does not use' if negated else 'Uses'} {n} orbit{'s' if n != 1 else ''}"
                
            elif filter_type == 'numInstruments':
                n = int(numb)
                if orbit:
                    orbit_id = int(orbit)
                    orbit_name = orbit_names.get(orbit_id, f"Orbit {orbit}")
                    return f"{'Does not have' if negated else 'Has'} {n} instrument{'s' if n != 1 else ''} in {orbit_name}"
                elif instr:
                    instr_id = int(instr)
                    instr_name = instrument_names.get(instr_id, f"Instrument {instr}")
                    return f"Uses {instr_name} {'more' if negated else 'exactly'} {n} time{'s' if n != 1 else ''}"
                else:
                    return f"{'Does not have' if negated else 'Has'} {n} instrument{'s' if n != 1 else ''} in total"
                    
            return expression  # Fall back to original expression
            
        except Exception as e:
            return expression  # Return original expression if parsing fails
    
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
    