import logging
from typing import List, Dict, Any, Optional
from spreadsheet_manager import SpreadsheetManager
import os
import json
import asyncio
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
import pickle

load_dotenv()

class KnowledgeBase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KnowledgeBase, cls).__new__(cls)
        return cls._instance

    def __init__(self, uri=None, user=None, password=None, ollama_interface=None):
        if not hasattr(self, 'initialized'):
            uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = user or os.getenv("NEO4J_USER", "neo4j")
            password = password or os.getenv("NEO4J_PASSWORD", "12345678")
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.logger = logging.getLogger(__name__)
            logging.basicConfig(level=logging.INFO)
            self.initialize_database()
            self.longterm_memory = {}
            self.base_directory = "knowledge_base_data"
            if not os.path.exists(self.base_directory):
                os.makedirs(self.base_directory)
            self.memory_limit = 100  # Set a default memory limit
            self.initialized = True
            self.project_state = "idle"  # Initial project state
            self.current_project = None  # Initial current project
            self.ollama = ollama_interface  # Reference to OllamaInterface

    async def check_initial_conditions(self):
        """Check initial conditions before running the knowledge base."""
        if not os.path.exists(self.base_directory):
            self.logger.info(f"Directory '{self.base_directory}' does not exist. Creating it.")
            os.makedirs(self.base_directory)

    async def setup_new_environment(self):
        """Set up a new environment for the knowledge base."""
        await self.check_initial_conditions()
        categorized_entries = await self.list_entries()
        self.index_and_categorize_entries(categorized_entries)
        self.logger.info("New environment set up.")

    def initialize_database(self):
        """Initialize the database with necessary nodes and relationships."""
        try:
            with self.driver.session() as session:
                session.write_transaction(self._create_initial_nodes)
                session.write_transaction(self._create_longterm_memory_label)
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            self.logger.info("Attempting to create a new database.")
            self.create_database()

    def create_database(self):
        """Create a new database if it doesn't exist."""
        with self.driver.session() as session:
            session.write_transaction(self._create_initial_nodes)
        self.logger.info("New database created and initialized successfully.")

    @staticmethod
    def _create_initial_nodes(tx):
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Node) REQUIRE n.name IS UNIQUE")

    @staticmethod
    def _create_longterm_memory_label(tx):
        tx.run("CREATE (n:LongTermMemory {name: 'initial_memory', data: ''})")

    def add_nodes_batch(self, label, nodes):
        """Add multiple nodes in a batch to the graph."""
        with self.driver.session() as session:
            session.write_transaction(self._create_nodes_batch, label, nodes)

    @staticmethod
    def _create_nodes_batch(tx, label, nodes):
        query = f"UNWIND $nodes AS node MERGE (n:{label} {{name: node.name}}) SET n += node.properties"
        tx.run(query, nodes=[{"name": node["name"], "properties": node["properties"]} for node in nodes])

    def find_paths_with_constraints(self, start_node, end_node, relationship_type, max_depth=5):
        """Find paths between two nodes with constraints on relationship type and depth."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (start {name: $start_node}), (end {name: $end_node}), "
                "p = (start)-[:$relationship_type*..$max_depth]-(end) "
                "RETURN p",
                start_node=start_node, end_node=end_node, relationship_type=relationship_type, max_depth=max_depth
            )
            return [record["p"] for record in result]

    def pattern_match_query(self, pattern):
        """Execute a pattern matching query to find specific structures in the graph."""
        with self.driver.session() as session:
            result = session.run(pattern)
            return [record.data() for record in result]

    def add_relationship(self, from_node, to_node, relationship_type, properties=None):
        """Add or update a relationship with properties between nodes."""
        with self.driver.session() as session:
            session.write_transaction(self._create_relationship, from_node, to_node, relationship_type, properties)

    @staticmethod
    def _create_relationship(tx, from_node, to_node, relationship_type, properties):
        query = (
            f"MATCH (a), (b) WHERE a.name = $from_node AND b.name = $to_node "
            f"MERGE (a)-[r:{relationship_type}]->(b) "
            f"ON CREATE SET r = $properties "
            f"ON MATCH SET r += $properties"
        )
        tx.run(query, from_node=from_node, to_node=to_node, properties=properties or {})

    async def add_entry(self, entry_name, data):
        """Add an entry to the knowledge base."""
        try:
            with self.driver.session() as session:
                session.write_transaction(self._create_node, entry_name, data)
            self.logger.info(f"Entry added: {entry_name}")
        except Exception as e:
            self.logger.error(f"Error adding entry {entry_name}: {e}")

    def add_capability_relationship(self, from_capability, to_capability, relationship_type, properties=None):
        """Add a relationship between two capabilities."""
        with self.driver.session() as session:
            session.write_transaction(self._create_relationship, from_capability, to_capability, relationship_type, properties)

    async def query_insights(self, query):
        """Execute a custom query to retrieve insights from the graph database."""
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_capability_evolution(self, capability_name):
        """Retrieve the evolution of a specific capability."""
        query = (
            "MATCH (c:Capability {name: $capability_name})-[r]->(next:Capability) "
            "RETURN c.name AS current, r, next.name AS next"
        )
        return self.query_insights(query)

    async def get_longterm_memory(self) -> Dict[str, Any]:
        """Retrieve long-term memory data from the graph database."""
        self.logger.info("Retrieving long-term memory from the graph database.")
        longterm_memory = {}
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n:LongTermMemory) RETURN n.name AS name, n.data AS data")
                for record in result:
                    name = record["name"]
                    data = record["data"]
                    longterm_memory[name] = data
            self.logger.info("Successfully retrieved long-term memory.")
        except Exception as e:
            if "UnknownLabelWarning" in str(e):
                self.logger.warning("LongTermMemory label not found in the database.")
            else:
                self.logger.error(f"Error retrieving long-term memory: {str(e)}")
        return longterm_memory

    async def get_recent_experiences(self, limit=5):
        """
        Retrieve recent experiences from the knowledge base.

        Args:
            limit (int): Maximum number of experiences to retrieve.

        Returns:
            List[Dict[str, Any]]: List of recent experiences.
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Experience) RETURN e ORDER BY e.timestamp DESC LIMIT $limit",
                limit=limit
            )
            experiences = [dict(record['e']) for record in result]
        return experiences

    def add_experience(self, experience: Dict[str, Any]):
        """Add a new experience to the graph database."""
        try:
            with self.driver.session() as session:
                session.run(
                    "CREATE (e:Experience {scenario: $scenario, action: $action, outcome: $outcome, lesson_learned: $lesson_learned, timestamp: timestamp()})",
                    scenario=experience["scenario"],
                    action=experience["action"],
                    outcome=experience["outcome"],
                    lesson_learned=experience["lesson_learned"]
                )
            self.logger.info(f"Added new experience: {experience['scenario']}")
        except Exception as e:
            self.logger.error(f"Error adding new experience: {str(e)}")

    async def get_entry(self, entry_name, include_metadata=False, context=None):
        if context:
            self.logger.info(f"Retrieving entry with context: {context}")
        with self.driver.session() as session:
            result = session.read_transaction(self._find_node, entry_name)
            if result:
                data = result.get("data")
                metadata = result.get("metadata", {})
                return {"data": data, "metadata": metadata} if include_metadata else data
            else:
                return None

    @staticmethod
    def _find_node(tx, entry_name):
        query = f"MATCH (n) WHERE n.name = $entry_name RETURN n"
        result = tx.run(query, entry_name=entry_name)
        single_result = result.single()
        return single_result[0] if single_result else None

    def add_node(self, label, properties):
        """Add a node to the graph database."""
        with self.driver.session() as session:
            session.write_transaction(self._create_node, label, properties)

    @staticmethod
    def _create_node(tx, label, properties):
        sanitized_properties = {k: v for k, v in properties.items() if v is not None}
        query = f"MERGE (n:{label} {{name: $name}}) SET n += $sanitized_properties"
        tx.run(query, name=sanitized_properties.get("name"), sanitized_properties=sanitized_properties)

    async def list_entries(self):
        entries = [f.split('.')[0] for f in os.listdir(self.base_directory) if f.endswith('.json')]
        self.logger.info(f"Entries listed: {entries}")
        return entries

    async def sync_with_spreadsheet(self, spreadsheet_manager: SpreadsheetManager, sheet_name: str = "KnowledgeBase"):
        """Synchronize data between the spreadsheet and the graph database."""
        try:
            data = spreadsheet_manager.read_data("A1:Z100")
            for row in data:
                entry_name, entry_data = row[0], row[1:]
                await self.add_entry(entry_name, {"data": entry_data})

            entries = await self.list_entries()
            spreadsheet_manager.write_data((1, 1), [["Entry Name", "Data"]] + [[entry, json.dumps(self.longterm_memory.get(entry, {}))] for entry in entries], sheet_name=sheet_name)
            self.logger.info("Synchronized data between spreadsheet and graph database.")
        except Exception as e:
            self.logger.error(f"Error synchronizing data: {e}")

    def index_and_categorize_entries(self, entries):
        """Index and categorize entries for efficient retrieval."""
        categorized_entries = sorted(entries, key=lambda x: x)
        self.logger.info(f"Indexed and categorized entries: {categorized_entries}")
        return categorized_entries

    def refine_memory_entry(self, data):
        """Refine a memory entry for better relevance and actionability."""
        refined_data = {k: v for k, v in data.items() if v}
        self.logger.info(f"Refined memory entry: {refined_data}")
        return refined_data

    def prioritize_memory_entries(self):
        """Prioritize memory entries based on relevance and usage frequency."""
        prioritized_entries = sorted(self.longterm_memory.items(), key=lambda item: item[1].get('relevance', 0), reverse=True)
        self.longterm_memory = dict(prioritized_entries[:self.memory_limit])

    def save_memory_state(self, recent_experiences, file_path='nimbus_memory.pkl'):
        """Save the entire memory state to a file."""
        state = {
            'longterm_memory': self.longterm_memory,
            'recent_experiences': recent_experiences,
            # Add any other state you want to persist
        }
        with open(file_path, 'wb') as f:
            pickle.dump(state, f)
        self.logger.info(f"Memory state saved to {file_path}")

    def load_memory_state(self, file_path='nimbus_memory.pkl'):
        """Load the entire memory state from a file."""
        try:
            with open(file_path, 'rb') as f:
                state = pickle.load(f)
            self.longterm_memory = state['longterm_memory']
            # Load other state components as needed
            self.logger.info(f"Memory state loaded from {file_path}")
            return True
        except FileNotFoundError:
            self.logger.info("No existing memory state found. Starting fresh.")
            return False

    async def log_interaction(self, source, action, details, improvement):
        """Log interactions with the knowledge base."""
        self.logger.info(f"Interaction logged from {source}: {action} with details: {details}")
        # Include context from long-term memory in interactions
        context = {"longterm_memory": self.longterm_memory}
        self.logger.info(f"Including context from long-term memory in interaction: {json.dumps(context, indent=2)}")
        implementation = await self.ollama.query_ollama(self.ollama.system_prompt, f"Implement this improvement: {improvement}", task="improvement_implementation")
        if implementation.get('knowledge_base_update'):
            await self.add_entry(f"improvement_{len(self.list_entries()) + 1}", implementation['knowledge_base_update'])
            self.logger.info(f"Improvement applied: {improvement}")
            return f"Applied improvement: {improvement}"
        self.logger.info(f"No knowledge base update for improvement: {improvement}")
        return f"No knowledge base update for improvement: {improvement}"

    def get_project_state(self):
        """
        Get the current project state.
        """
        return self.project_state

    def set_project_state(self, state):
        """
        Set the current project state.
        """
        self.project_state = state

    def set_current_project(self, project: Dict[str, Any]):
        """
        Set the current project details.
        """
        self.current_project = project
        self.logger.info(f"Current project set: {project['name']}")

    def get_current_project(self):
        """
        Get the current project details.
        """
        return self.current_project

    async def learn_from_experience(self, feedback: Dict[str, Any]):
        """Process experience data and extract learnings."""
        try:
            # Log the feedback for future reference
            await self.add_entry("experience_feedback", feedback)
            self.logger.info(f"Learned from experience: {feedback}")
        except Exception as e:
            self.logger.error(f"Error learning from experience: {e}")

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()