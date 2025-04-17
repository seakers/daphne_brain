import pandas as pd
import json
import os

def instruments_excel_to_json(excel_file_path, sheet_name="characteristics", output_json_path=None):
    """
    Parse an Excel file's characteristics tab with instrument data and convert to JSON format
    
    Args:
        excel_file_path (str): Path to the Excel file
        sheet_name (str): Name of the sheet containing instrument characteristics
        output_json_path (str, optional): Path to save the JSON file. If None, JSON is only returned
    
    Returns:
        dict: The data as a JSON-compatible dictionary
    """
    # Read the Excel file with the specific sheet
    print(f"Reading Excel file: {excel_file_path}, sheet: {sheet_name}")
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
    
    # Clean column names - Strip any leading/trailing whitespace
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    
    # Convert DataFrame to list of dictionaries (one dict per row)
    instruments = []
    
    for i, row in df.iterrows():
        # Skip rows without a name (likely empty or header rows)
        if pd.isna(row.get('Name')) or row.get('Name') == '':
            continue
            
        # Create a dict for this instrument
        instrument = {}
        
        # Process each column
        for col_name in df.columns:
            # Skip empty columns or columns with no name
            if pd.isna(col_name) or col_name == '':
                continue
                
            value = row[col_name]
            value = value.split()
            clean_value = value
            if len(value)  > 1:
                clean_value = value[1]

            # Handle different types of values
            if pd.isna(clean_value):
                # Convert NaN to None/null
                clean_value = None
            elif isinstance(value, str):
                # Remove quotes from string values if present
                if clean_value.startswith('"') and clean_value.endswith('"'):
                    clean_value = clean_value[1:-1]
                # Convert "nil" to None
                if value.lower() == 'nil':
                    value = None
                if isinstance(value, float):
                    # Convert float to int if it's a whole number
                    if value.is_integer():
                        clean_value = int(value)
                    else:
                        clean_value = float(value)
                    
            # Format column names consistently
            clean_col_name = col_name
            col_name = col_name.split()
            if len(col_name) > 1:
                clean_col_name = col_name[0]
            # Handle column names with '#' which are likely numbers
            if '#' in clean_col_name:
                clean_col_name = clean_col_name.replace('#', '').strip()
                # Try to convert numeric values
            
            
            # Add to instrument dictionary
            instrument[clean_col_name] = clean_value
        
        # Add type information based on data
        instrument["@type"] = "Instrument"
        
        instruments.append(instrument)
    
    # Create a JSON structure with metadata
    data = {
        "instruments": instruments,
        "metadata": {
            "source": os.path.basename(excel_file_path),
            "sheet": sheet_name,
            "count": len(instruments),
            "timestamp": pd.Timestamp.now().isoformat()
        }
    }
    
    # Save to file if path is provided
    if output_json_path:
        print(f"Saving JSON to: {output_json_path}")
        with open(output_json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data

def orbits_excel_to_json():
    """
    Extract orbit data from Excel files and create JSON files for each problem type
    """
    import os
    import pandas as pd
    import json
    
    # Define problem types
    problem_types = ["Decadal2007", "ClimateCentric", "SMAP", "SMAP_JPL1", "SMAP_JPL2"]
    
    # Define the path to the spreadsheet folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # spreadsheet_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spreadsheets")
    
    # # Check if the spreadsheet folder exists
    # if not os.path.exists(spreadsheet_folder):
    #     print(f"Error: Spreadsheet folder not found at {spreadsheet_folder}")
    #     return
        
    # Create a directory for JSON files if it doesn't exist
    json_folder = os.path.join(os.path.dirname(__file__))
    
    for problem in problem_types:
        try:
            # Construct the file path for the Excel file
            excel_file = os.path.join(current_dir, "spreadsheets", problem, "xls", "Mission Analysis Database.xls")
            
            # Check if the Excel file exists
            if not os.path.exists(excel_file):
                print(f"Warning: Excel file not found for problem type '{problem}': {excel_file}")
                continue
                
            # Read the "Power" tab from the Excel file
            df = pd.read_excel(excel_file, sheet_name="Power")
            
            # Extract the orbit data (assuming the structure is similar to your example)
            orbit_data = []
            
            for _, row in df.iterrows():
                # Skip rows without orbit data
                if pd.isna(row.get("id", None)):
                    continue
                    
                orbit = {
                    "name": str(row.get("id", "")),
                    "type": str(row.get("type", "")),
                    "altitude": float(row.get("altitude", 0)),
                    "inclination": float(row.get("inclination", 0)),
                }
                
                orbit_data.append(orbit)
            
            # Save to JSON file
            json_file = os.path.join(json_folder, f"orbit_characteristics_{problem}.json")
            with open(json_file, 'w') as f:
                json.dump(orbit_data, f, indent=4)
                
            print(f"Created orbit JSON file for '{problem}': {json_file} with {len(orbit_data)} orbits")
            
        except Exception as e:
            print(f"Error processing Excel file for problem '{problem}': {str(e)}")
    
    print("Orbit JSON file creation complete")

# def get_prbits(problem="assigning"):
#     """
#     Get orbit dataset from the appropriate JSON file based on problem type
    
#     Args:
#         problem (str): Problem type (assigning, partitioning, etc.)
    
#     Returns:
#         list: List of orbit dictionaries
#     """
#     import os
#     import json
    
#     # Get the path to the JSON file
#     json_folder = os.path.join(os.path.dirname(__file__), "spreadsheets")
#     json_file = os.path.join(json_folder, f"orbit_characteristics_{problem}.json")
    
#     # Check if the JSON file exists
#     if not os.path.exists(json_file):
#         print(f"Warning: Orbit JSON file not found: {json_file}")
#         print("Attempting to create JSON files from Excel...")
#         create_orbit_json_files()
        
#         # Check again if the file exists after creation attempt
#         if not os.path.exists(json_file):
#             print(f"Error: Could not create orbit JSON file: {json_file}")
#             return []
    
#     # Read the JSON file
#     try:
#         with open(json_file, 'r') as f:
#             orbit_data = json.load(f)
#         return orbit_data
#     except Exception as e:
#         print(f"Error reading orbit JSON file: {str(e)}")
#         return []

# def get_orbit_names(problem="assigning"):
#     """Get orbit names from problem definition"""
#     orbit_dataset = get_orbit_dataset(problem)
#     return [orbit.get("name") for orbit in orbit_dataset if orbit.get("name")]

if __name__ == "__main__":
    # Adjust these paths to match your environment
    # for problem_name in ["Decadal2007", "ClimateCentric", 
    #                      "SMAP", "SMAP_JPL1", "SMAP_JPL2"]:
    #     excel_file = "Instrument Capability Definition.xls"  # Update with your actual file name
    #     json_file = f"instrument_characteristics_{problem_name}.json"
        
    #     # Get absolute path to the Excel file
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #     excel_path = os.path.join(current_dir, "spreadsheets", problem_name, "xls", excel_file)
    #     json_path = os.path.join(current_dir, json_file)
        
    #     # Convert Excel to JSON
    #     data = instruments_excel_to_json(excel_path, sheet_name="CHARACTERISTICS", output_json_path=json_path)
    
    orbits_excel_to_json()
