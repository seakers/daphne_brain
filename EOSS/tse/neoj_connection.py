from neo4j import GraphDatabase
import json
import os
import logging
from dotenv import load_dotenv

class Neo4jKnowledgeGraph:
    """Helper class to extract Tool-Function-Metric relationships from Neo4j"""

    def __init__(self, uri, username, password):
        """Initialize with Neo4j connection parameters"""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Verify connection
            with self.driver.session() as session:
                result = session.run("MATCH () RETURN count(*) AS count")
                count = result.single()["count"]
                self.logger.info(f"Connected to Neo4j database. Found {count} nodes.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {str(e)}")
            return False
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")
    
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query and return the results"""
        assert self.driver is not None, "Driver not initialized. Call connect() first."
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_all_tools(self):
        """Get all Tool names from the database"""
        query = """
        MATCH (t:Tool)
        RETURN t.name as name
        """
        results = self.execute_query(query)
        # Extract just the names from the results
        return [record["name"] for record in results]

    def get_all_functions(self):
        """Get all Function names from the database"""
        query = """
        MATCH (f:Function)
        RETURN f.name as name
        """
        results = self.execute_query(query)
        # Extract just the names from the results
        return [record["name"] for record in results]

    def get_all_metrics(self):
        """Get all Metric names from the database"""
        query = """
        MATCH (m:Metric)
        RETURN m.name as name
        """
        results = self.execute_query(query)
        # Extract just the names from the results
        return [record["name"] for record in results]
    
    def get_tool_implements_function(self):
        """Get all Tool-implements->Function relationships"""
        query = """
        MATCH (t:Tool)-[r:IMPLEMENTS]->(f:Function)
        RETURN t.name as tool, f.name as function, type(r) as relationship, 
               properties(r) as rel_properties
        """
        return self.execute_query(query)
    
    def get_function_calculates_metric(self):
        """Get all Function-calculates->Metric relationships"""
        query = """
        MATCH (f:Function)-[r:CALCULATES]->(m:Metric)
        RETURN f.name as function, m.name as metric, type(r) as relationship,
               properties(r) as rel_properties
        """
        return self.execute_query(query)
    
    def get_function_to_tools_dict(self):
        """
        Get a dictionary mapping each function to the tools that implement it
        
        Returns:
            dict: Dictionary where keys are function names and values are lists of tool names
        """
        query = """
        MATCH (t:Tool)-[:IMPLEMENTS]->(f:Function)
        RETURN f.name as function, t.name as tool
        """
        
        results = self.execute_query(query)
        
        # Initialize the dictionary to store the mapping
        function_tools_dict = {}
        
        # Process query results
        for record in results:
            function_name = record.get("function")
            tool_name = record.get("tool")
            
            # Skip if either name is missing
            if not function_name or not tool_name:
                continue
                
            # Initialize the function entry if it doesn't exist
            if function_name not in function_tools_dict:
                function_tools_dict[function_name] = []
                
            # Add the tool to the function's list
            if tool_name not in function_tools_dict[function_name]:
                function_tools_dict[function_name].append(tool_name)
        
        return function_tools_dict
    
    def get_function_requires_function(self):
        """Get all Function-requires->Function relationships"""
        query = """
        MATCH (f1:Function)-[r:REQUIRES]->(f2:Function)
        RETURN f1.name as source_function, f2.name as required_function, 
               type(r) as relationship, properties(r) as rel_properties
        """
        return self.execute_query(query)
    
    def get_complete_knowledge_graph(self):
        """Get the complete knowledge graph with all relationships"""
        query = """
        MATCH (n)-[r]->(m)
        WHERE any(label IN labels(n) WHERE label IN ['Tool', 'Function', 'Metric'])
        AND any(label IN labels(m) WHERE label IN ['Tool', 'Function', 'Metric'])
        RETURN n.name as source, labels(n) as source_type, 
               m.name as target, labels(m) as target_type,
               type(r) as relationship, properties(r) as rel_properties
        """
        return self.execute_query(query)
    
    def export_knowledge_graph(self, output_path):
        """Export the complete knowledge graph to JSON"""
        data = {
            "nodes": {
                "tools": self.get_all_tools(),
                "functions": self.get_all_functions(),
                "metrics": self.get_all_metrics()
            },
            "relationships": {
                "tool_implements_function": self.get_tool_implements_function(),
                "function_calculates_metric": self.get_function_calculates_metric(),
                "function_requires_function": self.get_function_requires_function()
            },
            "complete_graph": self.get_complete_knowledge_graph()
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Knowledge graph exported to {output_path}")
        return data
    
def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI", "neo4j+ssc://3272b738.databases.neo4j.io")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "0tNj_x2cJuGZFrIljmm-rqAmiOoZ02zj5T7x_AciVwg")
    
    # Initialize connector
    kg = Neo4jKnowledgeGraph(uri, username, password)
    return kg

def get_metrics():
    kg = get_neo4j_driver()
    return kg.get_all_metrics()

def get_functions():
    kg = get_neo4j_driver()
    return kg.get_all_functions()

def get_tools():
    kg = get_neo4j_driver()
    return kg.get_all_tools()

def main():
    """Main function to extract Neo4j knowledge graph"""
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Load environment variables if available
    load_dotenv()
    
    # Neo4j connection details - get from environment or use default
    uri = os.getenv("NEO4J_URI", "neo4j+s://3272b738.databases.neo4j.io")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "0tNj_x2cJuGZFrIljmm-rqAmiOoZ02zj5T7x_AciVwg")
    
    # Initialize connector
    kg = Neo4jKnowledgeGraph(uri, username, password)
    
    # Connect to Neo4j
    if kg.connect():
        try:
            # Export the knowledge graph to JSON
            output_path = os.path.join(os.path.dirname(__file__), "knowledge_graph.json")
            data = kg.export_knowledge_graph(output_path)
            
            # Print summary statistics
            logger.info(f"Extracted {len(data['nodes']['tools'])} tools")
            logger.info(f"Extracted {len(data['nodes']['functions'])} functions")
            logger.info(f"Extracted {len(data['nodes']['metrics'])} metrics")
            logger.info(f"Extracted {len(data['relationships']['tool_implements_function'])} tool-implements-function relationships")
            logger.info(f"Extracted {len(data['relationships']['function_calculates_metric'])} function-calculates-metric relationships")
            logger.info(f"Extracted {len(data['relationships']['function_requires_function'])} function-requires-function relationships")
            
        finally:
            kg.close()
    else:
        logger.error("Failed to connect to Neo4j database")

if __name__ == "__main__":
    main()