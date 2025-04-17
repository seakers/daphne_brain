import os
import sys
import json
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from langchain_community.llms import Ollama
from langchain_community.utilities.sql_database import SQLDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DBQuery:
    """Database Query Processor for Natural Language Queries"""
    
    def __init__(self, model_name="mistral", temperature=0, debug=False):
        """Initialize the database query processor
        
        Args:
            model_name: Name of Ollama model to use (e.g., mistral, llama2, gemma)
            temperature: Temperature for LLM sampling (0-1)
            debug: Whether to print debug information
        """
        # Database connection parameters
        self.user = 'daphneeo'
        self.password = 'daphneeo'
        self.postgres_host = 'localhost'
        self.postgres_port = '5433'
        self.db_name = 'daphneeo'
        self.db_uri = f'postgresql://{self.user}:{self.password}@{self.postgres_host}:{self.postgres_port}/{self.db_name}'
        
        # Settings
        self.debug = debug
        
        # Initialize Ollama (local open source LLM)
        try:
            # Ollama needs to be running as a service: https://ollama.ai/
            self.llm = Ollama(model=model_name, temperature=temperature)
            if self.debug:
                print(f"Ollama initialized with model: {model_name}")
        except Exception as e:
            print(f"Error initializing Ollama: {str(e)}")
            print("Make sure Ollama is installed and running: https://ollama.ai/")
            self.llm = None
            
        # Connect to database
        try:
            # Create engine connection
            self.engine = create_engine(self.db_uri, echo=self.debug)
            
            # Initialize SQLDatabase for LangChain (used to get schema)
            self.db = SQLDatabase.from_uri(self.db_uri)
            
            if self.debug:
                print("Successfully connected to database")
                
            # Cache the schema for reuse
            self.schema_info = self.get_schema_info()
            
            # Load database values instead of using main.py functions
            self.db_values = self.get_database_values()
            
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            self.engine = None
            self.db = None
            self.schema_info = ""
            self.db_values = {}
    
    def get_tables(self):
        """Get list of all tables in the database"""
        if not self.engine:
            return []
            
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            print(f"Error getting tables: {str(e)}")
            return []
    
    def get_columns(self, table_name):
        """Get columns for a specific table"""
        if not self.engine:
            return []
            
        try:
            inspector = inspect(self.engine)
            return [col['name'] for col in inspector.get_columns(table_name)]
        except Exception as e:
            print(f"Error getting columns for {table_name}: {str(e)}")
            return []
    
    def get_database_values(self):
        """Get key values from database tables for use in prompts"""
        values = {}
        
        try:
            # Get measurements
            measurements_query = """
            SELECT DISTINCT name FROM ceos_measurements 
            ORDER BY name LIMIT 50
            """
            values['measurements'] = self.execute_query(measurements_query, return_column='name')
            print("measurements: ", values['measurements'])
            
            # Get agencies
            agencies_query = """
            SELECT DISTINCT name FROM ceos_agencies 
            ORDER BY name LIMIT 50
            """
            values['agencies'] = self.execute_query(agencies_query, return_column='name')
            
            # Get technologies/instrument types
            tech_query = """
            SELECT DISTINCT name FROM ceos_instrument_types
            ORDER BY name LIMIT 50
            """
            values['technologies'] = self.execute_query(tech_query, return_column='name')
            
            # Get mission names
            mission_query = """
            SELECT DISTINCT name FROM ceos_missions
            ORDER BY name LIMIT 50
            """
            values['missions'] = self.execute_query(mission_query, return_column='name')
            
            # Get instrument names
            instrument_query = """
            SELECT DISTINCT name FROM ceos_instruments
            ORDER BY name LIMIT 50
            """
            values['instruments'] = self.execute_query(instrument_query, return_column='name')
            
            return values
            
        except Exception as e:
            print(f"Error getting database values: {str(e)}")
            return {
                'measurements': ['Ocean Color', 'Precipitation', 'Soil Moisture', 'Visibility'],
                'agencies': ['NASA', 'ESA', 'JAXA', 'NOAA', 'INTA'],
                'technologies': ['Radar', 'Lidar', 'Optical', 'Radiometer', 'Spectrometer'],
                'missions': ['Terra', 'Aqua', 'Sentinel-1', 'JPSS'],
                'instruments': ['MODIS', 'ASCAT', 'AMSR', 'OLCI']
            }
    
    def execute_query(self, query, return_column=None):
        """Execute a SQL query and return results as a list"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                rows = [row for row in result]
                print("rowss ", rows)
                return [row[0] for row in rows]
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return []
    
    def get_schema_info(self):
        """Get detailed schema information for key tables"""
        if not self.engine:
            return "Database connection not available"
            
        try:
            ceos_tables = [t for t in self.get_tables() if t.startswith('ceos_')]
            
            # Get detailed information for key tables only
            # key_tables = [
            #     'ceos_missions', 'ceos_instruments', 'ceos_measurements', 
            #     'ceos_agencies', 'ceos_instruments_in_mission',
            #     'ceos_measurements_of_instrument', 'ceos_designers', 'ceos_operators'
            # ]
            
            # # Filter to only include key tables that exist
            # key_tables = [t for t in key_tables if t in ceos_tables]
            
            # Generate schema for key tables
            schema_parts = []
            inspector = inspect(self.engine)
            
            for table in ceos_tables:
                # Get columns
                columns = []
                for column in inspector.get_columns(table):
                    col_type = str(column['type'])
                    columns.append(f"  {column['name']} {col_type}")
                
                # Get foreign keys
                foreign_keys = []
                for fk in inspector.get_foreign_keys(table):
                    foreign_keys.append(f"  FOREIGN KEY ({fk['constrained_columns'][0]}) REFERENCES {fk['referred_table']}({fk['referred_columns'][0]})")
                
                schema_parts.append(f"CREATE TABLE {table} (\n" + 
                                   ",\n".join(columns) +
                                   ((",\n" + ",\n".join(foreign_keys)) if foreign_keys else "") +
                                   "\n);")
            
            # For other CEOS tables, just list them without details to keep prompt size manageable
            # other_ceos_tables = [t for t in ceos_tables if t not in key_tables]
            # if other_ceos_tables:
            #     schema_parts.append("\n-- Other CEOS tables:")
            #     for table in other_ceos_tables:
            #         cols = [c for c in self.get_columns(table)][:3]  # Just show first 3 columns
            #         schema_parts.append(f"-- {table}: Contains {', '.join(cols)}...")
                
            return "\n\n".join(schema_parts)
            
        except Exception as e:
            print(f"Error getting schema information: {str(e)}")
            return f"Error getting schema: {str(e)}"
    
    def process_query(self, query):
        """Process a natural language query and return results"""
        if not self.db or not self.llm:
            return {
                "status": "error",
                "message": "Database or LLM not initialized",
                "sql_query": None,
                "results": []
            }
        
        # Format database values for prompt
        measurements_str = ", ".join([f"'{m}'" for m in self.db_values.get('measurements', [])[:20]])
        agencies_str = ", ".join([f"'{a}'" for a in self.db_values.get('agencies', [])[:20]])
        technologies_str = ", ".join([f"'{t}'" for t in self.db_values.get('technologies', [])[:20]])
        missions_str = ", ".join([f"'{t}'" for t in self.db_values.get('missions', [])[:20]])
        instruments_str = ", ".join([f"'{t}'" for t in self.db_values.get('instruments', [])[:20]])

        print("schema info: ", self.schema_info)
        print("measurements_str: ", measurements_str)
        print("agencies_str: ", agencies_str)
        print("technologies_str: ", technologies_str)
        print("missions_str: ", missions_str)
        print("instruments_str: ", instruments_str)
        
        # Use direct SQL generation approach with schema information
        try:
            # Build a prompt with schema information and database values
            prompt = f"""Generate a SQL query to answer this question: "{query}"

DATABASE SCHEMA:
{self.schema_info}

DATABASE VALUES:
- Measurements include: {measurements_str}
- Space Agencies include: {agencies_str}
- Technologies include: {technologies_str}
- Missions include: {missions_str}
- Instruments include: {instruments_str}

IMPORTANT RELATIONSHIPS:
1. Missions have instruments: ceos_missions → ceos_instruments_in_mission → ceos_instruments
2. Instruments make measurements: ceos_instruments → ceos_measurements_of_instrument → ceos_measurements
3. Instruments are designed by agencies: ceos_instruments → ceos_designers → ceos_agencies
4. Missions are operated by agencies: ceos_missions → ceos_operators → ceos_agencies

EXAMPLE QUERIES:
Example 1: "Which missions can measure Glacier Cover?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%glacier cover%'
ORDER BY m.launch_date;

Example 2: "Which missions from NASA can measure Precipitation between 2010 and 2020?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
WHERE LOWER(me.name) LIKE '%precipitation%'
AND LOWER(a.name) LIKE '%nasa%'
AND m.launch_date < '2020-01-01'
AND m.eol_date > '2010-01-01'
ORDER BY m.launch_date;

Example 3: "Which missions do we currently use to measure Soil Moisture?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%soil moisture%'
AND m.launch_date < CURRENT_DATE
AND m.eol_date > CURRENT_DATE
ORDER BY m.launch_date;

Example 4: "Which instruments can measure Visibility?"
SELECT DISTINCT i.name 
FROM ceos_instruments i
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%visibility%'
ORDER BY i.name;

Example 5: "Which instruments from INTA can measure Visibility?"
SELECT DISTINCT i.name 
FROM ceos_instruments i
JOIN ceos_instruments_in_mission im ON i.id = im.instrument_id
JOIN ceos_missions m ON im.mission_id = m.id
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%visibility%'
AND LOWER(a.name) LIKE '%inta%'
ORDER BY i.name;

Example 6: "Which missions have flown Radar?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
LEFT JOIN ceos_type_of_instrument toi ON i.id = toi.instrument_id
LEFT JOIN ceos_instrument_types it ON toi.instrument_type_id = it.id
WHERE LOWER(i.technology) LIKE '%radar%' OR LOWER(it.name) LIKE '%radar%'
ORDER BY m.launch_date;

Example 7: "Which missions are currently flying Spectrometers?"
SELECT DISTINCT m.name 
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
LEFT JOIN ceos_type_of_instrument toi ON i.id = toi.instrument_id
LEFT JOIN ceos_instrument_types it ON toi.instrument_type_id = it.id
WHERE (LOWER(i.technology) LIKE '%spectrometer%' OR LOWER(it.name) LIKE '%spectrometer%')
AND m.launch_date < CURRENT_DATE
AND m.eol_date > CURRENT_DATE
ORDER BY m.launch_date;

Example 8: "Which orbit is the most common for Lidar?"
SELECT orbit
FROM ceos_techtype_most_common_orbits
WHERE LOWER(techtype) LIKE '%lidar%'
LIMIT 1;

Example 9: "Which orbit is the most common for Ocean Color measurements?"
SELECT orbit
FROM ceos_measurement_most_common_orbits
WHERE LOWER(measurement) LIKE '%ocean color%'
LIMIT 1;

Example 10: "When was mission Sentinel-1 launched?"
SELECT launch_date
FROM ceos_missions
WHERE LOWER(name) LIKE '%sentinel-1%'
LIMIT 1;

Example 11: "Which missions have been launched by ESA?"
SELECT DISTINCT m.name
FROM ceos_missions m
JOIN ceos_operators op ON m.id = op.mission_id
JOIN ceos_agencies a ON op.agency_id = a.id
WHERE LOWER(a.name) LIKE '%esa%'
ORDER BY m.launch_date;

Example 12: "Show me a timeline of missions which measure Aerosols"
SELECT m.name, m.status, m.launch_date, m.eol_date
FROM ceos_missions m
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%aerosols%'
ORDER BY m.launch_date;

Example 13: "What measurements can ASCAT make?"
SELECT DISTINCT me.name
FROM ceos_measurements me
JOIN ceos_measurements_of_instrument mi ON me.id = mi.measurement_id
JOIN ceos_instruments i ON mi.instrument_id = i.id
WHERE LOWER(i.name) LIKE '%ascat%'
ORDER BY me.name;

Example 14: "Show me all agencies that operate missions measuring Precipitation"
SELECT DISTINCT a.name
FROM ceos_agencies a
JOIN ceos_operators op ON a.id = op.agency_id
JOIN ceos_missions m ON op.mission_id = m.id
JOIN ceos_instruments_in_mission im ON m.id = im.mission_id
JOIN ceos_instruments i ON im.instrument_id = i.id
JOIN ceos_measurements_of_instrument mi ON i.id = mi.instrument_id
JOIN ceos_measurements me ON mi.measurement_id = me.id
WHERE LOWER(me.name) LIKE '%precipitation%'
ORDER BY a.name;

Example 15: "Which instruments are on the Terra mission?"
SELECT DISTINCT i.name
FROM ceos_instruments i
JOIN ceos_instruments_in_mission im ON i.id = im.instrument_id
JOIN ceos_missions m ON im.mission_id = m.id
WHERE LOWER(m.name) LIKE '%terra%'
ORDER BY i.name;

TASK:
For the question "{query}", generate a SQL query that correctly answers it. Please make sure to use the correct table names.
Return ONLY the SQL query with no explanations, no numbering, and no extra text.
"""

            # Generate SQL with Ollama
            sql_response = self.llm.invoke(prompt)
            
            # Clean up SQL (extract just the SQL part)
            sql_query = self._extract_sql(sql_response)
            
            if self.debug:
                print(f"Generated SQL: {sql_query}")
            
            # Execute the SQL
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text(sql_query))
                    # Convert to dataframe
                    df = pd.DataFrame(result.fetchall())
                    if not df.empty:
                        df.columns = result.keys()
                    
                    # Format results in a readable way
                    formatted_results = []
                    if not df.empty:
                        for _, row in df.iterrows():
                            formatted_results.append({col: row[col] for col in df.columns})
                    
                    return {
                        "status": "success", 
                        "sql_query": sql_query,
                        "results": formatted_results
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"SQL execution error: {str(e)}",
                    "sql_query": sql_query,
                    "results": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"SQL generation error: {str(e)}",
                "sql_query": None,
                "results": []
            }
    
    def _extract_sql(self, text):
        """Extract SQL query from LLM response"""
        # Remove markdown code blocks
        text = text.replace("```sql", "").replace("```", "")
        
        # Remove common prefixes
        for prefix in ["SQL:", "SQL Query:", "Here's the SQL query:", "Query:"]:
            if prefix in text:
                text = text.split(prefix, 1)[1]
        
        return text.strip()


# Example usage as a standalone script
if __name__ == "__main__":
    # Clear terminal screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print banner
    print("=" * 80)
    print("           Natural Language to SQL Query Processor (Ollama Edition)")
    print("=" * 80)
    
    # Available models with recommendations
    available_models = {
        "mistral": "Best overall balance for SQL (recommended)",
        "llama3": "Meta's newest model with improved reasoning (if available)",
        "mixtral": "Strongest reasoning but needs more powerful hardware",
        "codellama": "Specifically fine-tuned for code generation",
        "llama2": "Good general-purpose model",
        "gemma": "Google's lightweight model, decent for simple queries",
        "phi": "Microsoft's small model, good for basic queries"
    }
    
    # Default model recommendation
    recommended_model = "mistral"
    
    # Allow model selection
    if len(sys.argv) > 1 and sys.argv[1] in ["--model", "-m"] and len(sys.argv) > 2:
        model = sys.argv[2]
        query_args = sys.argv[3:]
        if model not in available_models:
            print(f"Warning: Unknown model '{model}', defaulting to {recommended_model}")
            model = recommended_model
    else:
        model = recommended_model  # Default model
        query_args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    print(f"Using Ollama with model: {model} - {available_models[model]}")
    print("Make sure Ollama is installed and running: https://ollama.ai/")
    print("\nAvailable models:")
    for m, desc in available_models.items():
        indicator = "→" if m == model else " "
        print(f" {indicator} {m}: {desc}")
    print("\nYou can change models with: --model [model_name]")
    
    # Create processor
    db_query = DBQuery(model_name=model, debug=True)
    
    # Check if command line query arguments were provided
    if query_args:
        # Get query from command line arguments
        query = " ".join(query_args)
        print(f"\nProcessing query: {query}")
        
        # Process query
        result = db_query.process_query(query)
        
        # Print results
        if result["status"] == "success":
            print(f"\nGenerated SQL:")
            print(result["sql_query"])
            
            print(f"\nResults ({len(result['results'])} rows):")
            if result["results"]:
                for i, row in enumerate(result["results"][:10]):  # Show first 10 results
                    print(f"\n[{i+1}] {json.dumps(row, indent=2)}")
                    
                if len(result["results"]) > 10:
                    print(f"\n... and {len(result['results']) - 10} more rows")
            else:
                print("No results found")
        else:
            print(f"\nError: {result['message']}")
            if result["sql_query"]:
                print(f"\nGenerated SQL:")
                print(result["sql_query"])
    else:
        # Interactive mode
        print("\nAvailable commands:")
        print("  models - List available models")
        print("  model [name] - Switch to a different model")
        print("  tables - List all tables in the database")
        print("  ceos_tables - List all tables starting with 'ceos_'")
        print("  columns [table_name] - List columns for a specific table")
        print("  values - Show sample values from the database")
        print("  schema - Show the database schema being used")
        print("  exit/quit - Exit the program")
        
        while True:
            query = input("\nEnter query: ")
            
            if query.lower() in ["exit", "quit", "q"]:
                break
                
            if query.lower() in ["models", "list models"]:
                print("\nAvailable models:")
                for m, desc in available_models.items():
                    indicator = "→" if m == model else " "
                    print(f" {indicator} {m}: {desc}")
                continue
                
            if query.lower().startswith("model "):
                new_model = query.lower()[6:].strip()
                if new_model in available_models:
                    model = new_model
                    print(f"Switching to model: {model}")
                    db_query = DBQuery(model_name=model, debug=True)
                else:
                    print(f"Unknown model: {new_model}")
                    print(f"Available models: {', '.join(available_models)}")
                continue
                
            if query.lower() in ["tables", "list tables"]:
                tables = db_query.get_tables()
                print("\nTables in database:")
                for table in sorted(tables):
                    print(f"- {table}")
                continue
                
            if query.lower() in ["ceos_tables", "list ceos_tables"]:
                tables = db_query.get_tables()
                print("\nCEOS tables in database:")
                for table in sorted([t for t in tables if t.startswith('ceos_')]):
                    print(f"- {table}")
                continue
                
            if query.lower() in ["schema", "show schema"]:
                print("\nDatabase Schema:")
                print(db_query.schema_info)
                continue
            
            if query.lower() in ["values", "show values"]:
                print("\nSample Database Values:")
                for category, values in db_query.db_values.items():
                    print(f"\n{category.title()} ({len(values)} items):")
                    for value in values[:10]:
                        print(f"- {value}")
                    if len(values) > 10:
                        print(f"  ... and {len(values) - 10} more")
                continue
                
            if query.lower().startswith("columns "):
                table = query.lower()[8:]
                columns = db_query.get_columns(table)
                print(f"\nColumns in {table}:")
                for column in columns:
                    print(f"- {column}")
                continue
                
            # Process query
            result = db_query.process_query(query)
            
            # Print results
            if result["status"] == "success":
                print(f"\nGenerated SQL:")
                print(result["sql_query"])
                
                print(f"\nResults ({len(result['results'])} rows):")
                if result["results"]:
                    for i, row in enumerate(result["results"][:10]):  # Show first 10 results
                        print(f"\n[{i+1}] {json.dumps(row, indent=2)}")
                        
                    if len(result["results"]) > 10:
                        print(f"\n... and {len(result['results']) - 10} more rows")
                else:
                    print("No results found")
            else:
                print(f"\nError: {result['message']}")
                if result["sql_query"]:
                    print(f"\nGenerated SQL:")
                    print(result["sql_query"])