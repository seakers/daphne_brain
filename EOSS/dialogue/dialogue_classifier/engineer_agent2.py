import json
import logging
import pandas as pd
import os
import glob
import re
from typing import Dict, List, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

from EOSS.dialogue.dialogue_classifier.utils import getChatResponse, clean_chat_response

logger = logging.getLogger('EOSS.dialogue.engineer_agent')

class EngineerAgent2:
    """
    Agent that handles engineering queries related to space mission designs by
    converting spreadsheets to more accessible formats for GPT.
    """
    
    def __init__(self):
        """Initialize the Engineer agent and convert spreadsheets to JSON if needed."""
        # Base directory for all spreadsheets organized by problem
        self.data_dir = os.path.join(os.path.dirname(__file__), "spreadsheets")
        # Directory for storing JSON versions of spreadsheets
        self.json_dir = os.path.join(os.path.dirname(__file__), "json_data")

        self.embeddings_dir = os.path.join(os.path.dirname(__file__), "embeddings")
        
        # Create directories if they don't exist
        for directory in [self.json_dir, self.embeddings_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Create JSON directory if it doesn't exist
       
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_embeddings = True
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.use_embeddings = False
        
        # Standard spreadsheet types we expect
        self.standard_sheet_types = [
            "Aggregation Rules",
            "AttributeSet",
            "Instrument Capability Definition",
            "Mission Analysis Database",
            "Requirement Rules", 
            "Aggregation Rules-Climate",
            "Aggregation Rules-Weather",
        ]
        
        # Maximum tokens for each data chunk to send to GPT
        self.max_chunk_size = 4000  # Approximate token count
        
        # Check for available problems and convert spreadsheets to JSON
        self._initialize_json_data()
    
    def _generate_embeddings(self, problem: str):
        """Generate embeddings for spreadsheet content."""
        if not self.use_embeddings:
            return
        
        problem_json_dir = os.path.join(self.json_dir, problem)
        problem_embedding_dir = os.path.join(self.embeddings_dir, problem)
        
        if not os.path.exists(problem_embedding_dir):
            os.makedirs(problem_embedding_dir)
            
        json_files = glob.glob(os.path.join(problem_json_dir, "*.json"))
        
        for json_path in json_files:
            basename = os.path.basename(json_path).split('.')[0]
            embedding_path = os.path.join(problem_embedding_dir, f"{basename}_embeddings.npz")
            
            # Skip if embeddings exist and are newer than JSON
            if os.path.exists(embedding_path) and os.path.getmtime(embedding_path) > os.path.getmtime(json_path):
                continue
                
            try:
                with open(json_path, 'r') as f:
                    sheet_data = json.load(f)
                
                # Store embeddings for each tab
                sheet_embeddings = {}
                
                for tab_name, tab in sheet_data.get("tabs", {}).items():
                    if "rows" not in tab or not tab["rows"]:
                        continue
                        
                    # Create content strings for each row
                    row_contents = []
                    row_indices = []
                    
                    for i, row in enumerate(tab["rows"]):
                        # Create a string representation of the row
                        row_content = " ".join([f"{k}: {v}" for k, v in row.items() if v])
                        if row_content.strip():
                            row_contents.append(row_content)
                            row_indices.append(i)
                    
                    if not row_contents:
                        continue
                        
                    # Generate embeddings for all rows at once
                    embeddings = self.embedding_model.encode(row_contents)
                    
                    # Store with their indices
                    sheet_embeddings[tab_name] = {
                        "embeddings": embeddings,
                        "row_indices": row_indices
                    }
                
                # Save embeddings
                np.savez(embedding_path, **sheet_embeddings)
                logger.info(f"Generated embeddings for {basename}")
                
            except Exception as e:
                logger.error(f"Error generating embeddings for {json_path}: {e}")

    def _find_relevant_rows(self, query: str, problem: str, n_results=50):
        """Find most relevant rows using embedding similarity."""
        if not self.use_embeddings:
            return {}
            
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        problem_embedding_dir = os.path.join(self.embeddings_dir, problem)
        if not os.path.exists(problem_embedding_dir):
            return {}
            
        relevant_rows = {}
        
        # Load each embedding file and find similar rows
        embedding_files = glob.glob(os.path.join(problem_embedding_dir, "*_embeddings.npz"))
        
        for emb_path in embedding_files:
            sheet_name = os.path.basename(emb_path).split('_embeddings.npz')[0]
            
            try:
                # Load embeddings
                embeddings_data = np.load(emb_path, allow_pickle=True)
                
                sheet_relevant = {}
                
                # Check each tab's embeddings
                for tab_name in embeddings_data.files:
                    tab_data = embeddings_data[tab_name].item()
                    tab_embeddings = tab_data["embeddings"]
                    row_indices = tab_data["row_indices"]
                    
                    # Calculate similarity scores
                    similarities = cosine_similarity([query_embedding], tab_embeddings)[0]
                    
                    # Get top matches
                    top_indices = similarities.argsort()[-20:][::-1]  # Top 20 per tab
                    
                    # Store relevant row indices with scores
                    sheet_relevant[tab_name] = [
                        (row_indices[idx], float(similarities[idx]))
                        for idx in top_indices
                        if similarities[idx] > 0.4  # Minimum relevance threshold
                    ]

                # print("herreeeee")
                
                if any(matches for matches in sheet_relevant.values()):
                    relevant_rows[sheet_name] = sheet_relevant
                # print("relevant_rowsssss", relevant_rows)
                    
            except Exception as e:
                logger.error(f"Error finding relevant rows in {emb_path}: {e}")
        
        return relevant_rows
    
    def _initialize_json_data(self):
        """
        Check all problem directories and convert spreadsheets to JSON if needed.
        Only converts if JSON doesn't exist or spreadsheet is newer than JSON.
        """
        # Get all problem directories
        problem_dirs = [d for d in os.listdir(self.data_dir) 
                      if os.path.isdir(os.path.join(self.data_dir, d))]
        
        for problem in problem_dirs:
            problem_xls_dir = os.path.join(self.data_dir, problem, "xls")
            if not os.path.exists(problem_xls_dir):
                continue
                
            # Create problem JSON directory if it doesn't exist
            problem_json_dir = os.path.join(self.json_dir, problem)
            if not os.path.exists(problem_json_dir):
                os.makedirs(problem_json_dir)
                
            # Get all Excel files
            xlsx_files = glob.glob(os.path.join(problem_xls_dir, "*.xls*"))
            xlsx_files.extend(glob.glob(os.path.join(problem_xls_dir, "*.xlsx")))
            
            for xlsx_path in xlsx_files:
                basename = os.path.splitext(os.path.basename(xlsx_path))[0]
                json_path = os.path.join(problem_json_dir, f"{basename}.json")
                
                # Check if JSON needs to be created/updated
                if not os.path.exists(json_path) or \
                   os.path.getmtime(xlsx_path) > os.path.getmtime(json_path):
                    logger.info(f"Converting {xlsx_path} to JSON")
                    self._convert_excel_to_json(xlsx_path, json_path)
    
    def _convert_excel_to_json(self, excel_path: str, json_path: str):
        """
        Convert Excel file with all its tabs to JSON format with a more intuitive structure.
        
        Args:
            excel_path: Path to the Excel file
            json_path: Path to save the JSON file
        """
        try:
            # Read all tabs in the Excel file
            excel_file = pd.ExcelFile(excel_path)
            all_tabs = excel_file.sheet_names
        
            tabs = [tab for tab in all_tabs if tab != "del"]
            print("excel_path", excel_path)
            print("tabs", tabs)

            spreadsheet_data = {"tabs": {}}
            
            spreadsheet_name = os.path.basename(excel_path).split('.')[0]
            spreadsheet_data["name"] = spreadsheet_name

            # print("spreadsheet_name", spreadsheet_name)
            
            for tab in tabs:
                try:
                    df = pd.read_excel(excel_file, sheet_name=tab)
                    
                    df = df.fillna("")
                    
                    rows = []
                    for _, row in df.iterrows():
                        row_obj = {}
                        for col in df.columns:
                            row_obj[col] = row[col]
                        rows.append(row_obj)
                    
                    spreadsheet_data["tabs"][tab] = {
                        "columns": list(df.columns),
                        "rows": rows,
                        "row_count": len(df),
                        "description": f"Tab '{tab}' from spreadsheet '{spreadsheet_name}'"
                    }
                    
                except Exception as e:
                    spreadsheet_data["tabs"][tab] = {
                        "error": f"Error loading tab: {str(e)}"
                    }
            
            # Save to JSON file
            with open(json_path, 'w') as f:
                json.dump(spreadsheet_data, f, indent=2)
                
            logger.info(f"Successfully converted {excel_path} to {json_path}")
            
        except Exception as e:
            logger.error(f"Error converting {excel_path} to JSON: {str(e)}")
    
    def _get_problem_spreadsheets(self, problem: str) -> Dict[str, str]:
        """
        Get the available spreadsheets for a specific problem.
        
        Args:
            problem: The problem identifier (folder name)
            
        Returns:
            Dictionary mapping spreadsheet names to file paths
        """
        problem_json_dir = os.path.join(self.json_dir, problem)
        
        if not os.path.exists(problem_json_dir):
            return {}
        
        spreadsheets = {}
        json_files = glob.glob(os.path.join(problem_json_dir, "*.json"))
        
        for json_path in json_files:
            basename = os.path.basename(json_path).split('.')[0]
            spreadsheets[basename] = json_path
            
        return spreadsheets
    
    def _extract_relevant_data(self, query: str, problem: str, spreadsheet_data: Dict) -> Dict:
        """
        Extract the most relevant data based on the query.
        
        Args:
            query: The user's query
            problem: The problem domain
            spreadsheet_data: All spreadsheet data
            
        Returns:
            Filtered data that's most relevant to the query
        """
        # Keywords to look for in the query
        keywords = [
            # Extract key terms from the query
            *re.findall(r'\b\w{4,}\b', query.lower()),  # Words with 4+ chars
            *self.standard_sheet_types,  # Standard sheet types
        ]
        
        relevant_data = {}
        
        # Score each spreadsheet and tab for relevance
        for sheet_name, sheet_data in spreadsheet_data.items():
            sheet_score = sum(1 for kw in keywords if kw.lower() in sheet_name.lower())
            
            if sheet_score > 0 or len(spreadsheet_data) <= 5:  # Include if relevant or if we have few sheets
                relevant_data[sheet_name] = {"tabs": {}}
                relevant_data[sheet_name]["name"] = sheet_data.get("name", sheet_name)
                
                # Score and filter tabs
                for tab_name, tab_data in sheet_data.get("tabs", {}).items():
                    tab_score = sum(1 for kw in keywords if kw.lower() in tab_name.lower())
                    
                    # Also check column names for relevance
                    col_score = 0
                    for col in tab_data.get("columns", []):
                        col_score += sum(1 for kw in keywords if kw.lower() in str(col).lower())
                    
                    # Include tab if it's relevant or the sheet is highly relevant
                    if tab_score > 0 or col_score > 0 or sheet_score > 1:
                        relevant_data[sheet_name]["tabs"][tab_name] = tab_data
        
        # If no relevant data found, include a sample of data
        print("relevant_data in keyword", len(relevant_data)) 
        if not relevant_data or all(len(sheet["tabs"]) == 0 for sheet in relevant_data.values()):
            # Take a sample of the first sheet and first tab
            if spreadsheet_data:
                first_sheet_name = next(iter(spreadsheet_data))
                first_sheet = spreadsheet_data[first_sheet_name]
                relevant_data = {
                    first_sheet_name: {
                        "name": first_sheet.get("name", first_sheet_name),
                        "tabs": {}
                    }
                }
                
                if "tabs" in first_sheet and first_sheet["tabs"]:
                    first_tab_name = next(iter(first_sheet["tabs"]))
                    first_tab = first_sheet["tabs"][first_tab_name]
                    
                    # Take a sample of the data
                    if "rows" in first_tab and first_tab["rows"]:
                        sample_rows = first_tab["rows"][:min(10, len(first_tab["rows"]))]
                        relevant_data[first_sheet_name]["tabs"][first_tab_name] = {
                            "columns": first_tab.get("columns", []),
                            "rows": sample_rows,
                            "row_count": first_tab.get("row_count", len(sample_rows)),
                            "description": f"Sample from tab '{first_tab_name}' (showing {len(sample_rows)} of {first_tab.get('row_count', len(first_tab['rows']))} rows)"
                        }
        
        return relevant_data
    
    def _load_json_data(self, problem: str) -> Dict:
        """
        Load all JSON data for a specific problem.
        
        Args:
            problem: The problem identifier
            
        Returns:
            Dictionary with all spreadsheet data
        """
        spreadsheets = self._get_problem_spreadsheets(problem)
        data = {}
        
        for sheet_name, json_path in spreadsheets.items():
            try:
                with open(json_path, 'r') as f:
                    data[sheet_name] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading {json_path}: {str(e)}")
        
        return data
        
    def process_query(self, query: str, problem: str, parameters: Dict, designs, context: Dict) -> str:
        """Process query using semantic search with embeddings."""
        logger.info(f"Processing engineering query: '{query}' for problem: '{problem}'")
        
        # Load all JSON data for this problem
        all_data = self._load_json_data(problem)
        
        if not all_data:
            # If JSON data doesn't exist, try converting again
            self._initialize_json_data()
            all_data = self._load_json_data(problem)
            
            if not all_data:
                return f"I couldn't find any data for the problem domain: {problem}."
        
        # Generate embeddings if needed
        if self.use_embeddings:
            self._generate_embeddings(problem)
            
            # Find relevant rows using embeddings
            relevant_rows = self._find_relevant_rows(query, problem)

            print("relevant rows", relevant_rows)
            
            # If we found relevant rows, extract them from the data
            if relevant_rows:
                print("in embedding based search")
                filtered_data = self._extract_rows_by_relevance(all_data, relevant_rows)
                print("filtered data in embedding", filtered_data)

                # print("filtered data", filtered_data)
                return self._generate_response(query, problem, parameters, designs, context, filtered_data)
        
        # Fall back to keyword-based search if embeddings didn't work
        relevant_data = self._extract_relevant_data(query, problem, all_data)
        # print("relevant data 2", relevant_data)
        return self._generate_response(query, problem, parameters, designs, context, relevant_data)
    

    def _extract_rows_by_relevance(self, all_data, relevant_rows):
        """Extract the most relevant rows from the data."""
        filtered_data = {}
        
        for sheet_name, sheet_relevance in relevant_rows.items():
            if sheet_name not in all_data:
                continue
                
            sheet_data = all_data[sheet_name]
            filtered_sheet = {
                "name": sheet_data.get("name", sheet_name),
                "tabs": {}
            }
            
            for tab_name, tab_matches in sheet_relevance.items():
                if not tab_matches or tab_name not in sheet_data.get("tabs", {}):
                    continue
                    
                original_tab = sheet_data["tabs"][tab_name]
                
                if "rows" not in original_tab or not original_tab["rows"]:
                    continue
                    
                # Extract relevant rows
                relevant_indices = [idx for idx, score in tab_matches]
                relevant_scores = [score for idx, score in tab_matches]
                
                filtered_rows = []
                for i, idx in enumerate(relevant_indices):
                    if idx < len(original_tab["rows"]):
                        row = original_tab["rows"][idx].copy()
                        row["_relevance_score"] = f"{relevant_scores[i]:.2f}"
                        filtered_rows.append(row)
                
                if filtered_rows:
                    filtered_sheet["tabs"][tab_name] = {
                        "columns": original_tab.get("columns", []) + ["_relevance_score"],
                        "rows": filtered_rows,
                        "row_count": len(filtered_rows),
                        "description": f"Most relevant rows from tab '{tab_name}' for your query"
                    }
            
            if filtered_sheet["tabs"]:
                filtered_data[sheet_name] = filtered_sheet
                
        return filtered_data
    
    def _filter_by_design_id(self, data: Dict, design_id: str) -> Dict:
        """
        Filter data to only include rows relevant to a specific design ID.
        
        Args:
            data: The data to filter
            design_id: The design ID to filter by
            
        Returns:
            Filtered data
        """
        filtered_data = {}
        
        for sheet_name, sheet in data.items():
            filtered_sheet = {"name": sheet.get("name", sheet_name), "tabs": {}}
            
            for tab_name, tab in sheet.get("tabs", {}).items():
                # Check if this tab has rows
                if "rows" not in tab:
                    continue
                
                # Check if any column might contain design ID
                design_id_cols = [col for col in tab.get("columns", []) 
                                 if any(id_col in str(col).lower() 
                                       for id_col in ["design", "id", "arch", "architecture"])]
                
                if design_id_cols:
                    # Filter rows that match the design ID in any of these columns
                    filtered_rows = []
                    for row in tab["rows"]:
                        for col in design_id_cols:
                            if col in row and str(row[col]) == str(design_id):
                                filtered_rows.append(row)
                                break
                    
                    if filtered_rows:
                        filtered_sheet["tabs"][tab_name] = {
                            "columns": tab.get("columns", []),
                            "rows": filtered_rows,
                            "row_count": len(filtered_rows),
                            "description": f"Filtered data for design ID {design_id} from tab '{tab_name}'"
                        }
            
            # Only include sheets that have tabs with data
            if filtered_sheet["tabs"]:
                filtered_data[sheet_name] = filtered_sheet
        
        return filtered_data
    
    def _generate_response(self, query: str, problem: str, parameters: Dict, designs, context: Dict, data: Dict) -> str:
        """
        Generate a response based on the relevant spreadsheet data.
        
        Args:
            query: The original user query
            problem: The problem domain/identifier
            parameters: Extracted parameters from the query
            designs: Available design data
            context: Context information including screen ID
            data: Relevant spreadsheet data
            
        Returns:
            Response to the user's query
        """
        # Create a summary of available data to help GPT navigate
        # data_summary = self._create_data_summary(data)
        
        # Format the data in a way that's easy for GPT to process
        formatted_data = self._format_data_for_gpt(data)
        max_tokens = 4000
        # if len(formatted_data) > max_tokens:
        #     return self._process_large_data_query(query, problem, parameters, designs, context, data)
    
        
        # Create a prompt with context, data summary, and the formatted data
        prompt = f"""
            You are an engineering assistant for Earth observation satellite mission design. 
            You are helping with the '{problem}' problem domain.

            User query: "{query}"

            Context:
            - Problem domain: {problem}
            - Parameters from query: {json.dumps(parameters, indent=2)}
            - Current context: {json.dumps(context, indent=2)}

            Detailed data:
            {formatted_data}

            Based on this information, please provide a clear, helpful answer to the user's query.
            IMPORTANT INSTRUCTIONS:
            1. Answer ONLY the specific question asked using the data provided.
            2. Provide DIRECT answers without explaining where you got the information.
            3. DO NOT include phrases like 'according to the data' or 'the spreadsheet shows'.
            4. DO NOT ask if the user needs additional information.
            5. DO NOT suggest asking more questions.
            6. If you can't answer based on the provided data, simply state 'I don't have that information.'

            Answer:
            """
        
        # Get response from GPT
        response = getChatResponse(prompt)
        return clean_chat_response(response)
    
    def _process_large_data_query(self, query: str, problem: str, parameters: Dict, designs, context: Dict, data: Dict) -> str:
        """
        Process a query when the relevant data is too large for a single prompt
        
        Args:
            query: The original user query
            problem: The problem domain/identifier
            parameters: Extracted parameters from the query
            designs: Available design data
            context: Context information
            data: Relevant spreadsheet data
            
        Returns:
            Response to the user's query
        """
        logger.info("Data too large, using multi-step approach")
        
        # Step 1: Extract key terms from the query to narrow down search
        extract_prompt = f"""
            Extract key search terms from this question. Output ONLY the 3-5 most important keywords.
            
            Question: {query}
            
            Keywords:
        """
        
        try:
            # Get search terms
            keywords_response = getChatResponse(extract_prompt)
            keywords = clean_chat_response(keywords_response).strip().split('\n')
            keywords = [k.strip() for k in keywords if k.strip()]
            logger.info(f"Extracted keywords: {keywords}")
            
            # Step 2: Filter data to only include the most relevant pieces
            filtered_data = {}
            
            for sheet_name, sheet_data in data.items():
                filtered_sheet = {"tabs": {}}
                has_matches = False
                
                for tab_name, tab_data in sheet_data.get("tabs", {}).items():
                    filtered_rows = []
                    
                    # Filter rows to only those containing keywords
                    for row in tab_data.get("rows", []):
                        row_text = " ".join(str(v) for v in row.values())
                        if any(keyword.lower() in row_text.lower() for keyword in keywords):
                            filtered_rows.append(row)
                            has_matches = True
                    
                    if filtered_rows:
                        filtered_sheet["tabs"][tab_name] = {
                            "columns": tab_data.get("columns", []),
                            "rows": filtered_rows[:5],  # Just keep the top few rows
                            "description": tab_data.get("description", "")
                        }
                
                if has_matches:
                    filtered_data[sheet_name] = filtered_sheet
            
            # Step 3: Generate response with filtered data
            formatted_filtered_data = self._format_data_for_gpt(filtered_data)
            
            final_prompt = f"""
                You are an engineering assistant for Earth observation satellite mission design.
                You are helping with the '{problem}' problem domain.

                IMPORTANT INSTRUCTIONS:
                1. Answer ONLY the specific question asked using the data provided.
                2. Provide DIRECT answers without explaining where you got the information.
                3. DO NOT include phrases like 'according to the data' or 'the spreadsheet shows'.
                4. DO NOT ask if the user needs additional information.
                5. DO NOT suggest asking more questions.
                6. If you can't answer based on the provided data, simply state 'I don't have that information.'
                
                USER QUESTION: "{query}"

                RELEVANT DATA (filtered by keywords: {', '.join(keywords)}):
                {formatted_filtered_data}

                Your answer should be concise, factual, and direct. Only include the specific information requested.
                """
            
            response = getChatResponse(final_prompt)
            clean_response = clean_chat_response(response)
        
            return clean_response
            
        except Exception as e:
            logger.error(f"Error processing large data query: {str(e)}")
            return "I'm sorry, but your question requires processing too much data. Could you make your question more specific?"
        
    def _create_data_summary(self, data: Dict) -> str:
        """
        Create a summary of the data to help GPT navigate the information.
        
        Args:
            data: The data to summarize
            
        Returns:
            A string summary of the data
        """
        if not data:
            return "No relevant data available for this query."
        
        summary = ["Available data:"]
        
        for sheet_name, sheet in data.items():
            sheet_info = f"- {sheet.get('name', sheet_name)} spreadsheet:"
            tab_info = []
            
            for tab_name, tab in sheet.get("tabs", {}).items():
                row_count = tab.get("row_count", 0)
                columns = tab.get("columns", [])
                tab_info.append(f"  * Tab '{tab_name}': {row_count} rows with columns: {', '.join(str(c) for c in columns)}")
            
            if tab_info:
                summary.append(sheet_info)
                summary.extend(tab_info)
        
        return "\n".join(summary)
    
    def _format_data_for_gpt(self, data: Dict) -> str:
        """
        Format the data in a way that's easy for GPT to process.
        
        Args:
            data: The data to format
            
        Returns:
            Formatted data as a string
        """
        if not data:
            return "No data available."
        
        formatted_data = []
        
        for sheet_name, sheet in data.items():
            sheet_header = f"SPREADSHEET: {sheet.get('name', sheet_name)}"
            formatted_data.append(sheet_header)
            formatted_data.append("=" * len(sheet_header))
            
            for tab_name, tab in sheet.get("tabs", {}).items():
                tab_header = f"TAB: {tab_name}"
                formatted_data.append("\n" + tab_header)
                formatted_data.append("-" * len(tab_header))
                
                if "rows" not in tab or not tab["rows"]:
                    formatted_data.append("No data in this tab.")
                    continue
                
                # Format rows in a table-like structure
                columns = tab.get("columns", [])
                rows = tab.get("rows", [])
                
                # Limit to prevent exceeding token limits
                row_limit = min(50, len(rows))
                if len(rows) > row_limit:
                    formatted_data.append(f"Showing {row_limit} of {len(rows)} total rows.")
                
                # Format as key-value pairs for each row
                for i, row in enumerate(rows[:row_limit]):
                    formatted_data.append(f"\nRow {i+1}:")
                    for col in columns:
                        if col in row:
                            formatted_data.append(f"  {col}: {row[col]}")
                
                if len(rows) > row_limit:
                    formatted_data.append(f"\n... (plus {len(rows) - row_limit} more rows)")
            
            formatted_data.append("\n")
        
        return "\n".join(formatted_data)
    

# def main():
#     # Example usage
#     agent = EngineerAgent()
#     query = "What are the aggregation rules for the climate mission?"
#     problem = "Climate"
#     parameters = {}
#     designs = []
#     context = {
#         "screen": {
#             "selected_arch_id": "D456"
#         }
#     }
    
#     response = agent.process_query(query, problem, parameters, designs, context)
#     print("Response:", response)

# if __name__ == "__main__":
#     main()