import os
import sys
import json
import re
import glob
from dotenv import load_dotenv
import psycopg2
from psycopg2 import extras
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import markdown # For basic Markdown parsing
import subprocess # For curl check

# Add project root to sys.path to import pyHaasAPI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pyHaasAPI import api
from pyHaasAPI.exceptions import HaasApiError

# --- Configuration ---
# Load environment variables from the project root's .env file
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env')))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

HAAS_API_HOST = os.getenv("API_HOST", "127.0.0.1")
HAAS_API_PORT = int(os.getenv("API_PORT", 8090))
HAAS_API_EMAIL = os.getenv("API_EMAIL")
HAAS_API_PASSWORD = os.getenv("API_PASSWORD")

if not all([HAAS_API_EMAIL, HAAS_API_PASSWORD]):
    print("Warning: HaasOnline API credentials not fully set in .env. Skipping API data ingestion.")
    HAAS_API_ENABLED = False
else:
    HAAS_API_ENABLED = True

GUIDE_CONTENT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Data', 'guide_content'))

# --- Database Helpers ---
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# --- Embedding Model Helper ---
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded.")
    return _model

def get_embedding(text: str) -> List[float]:
    model = get_embedding_model()
    # Ensure text is not empty, as empty strings can cause issues with some models
    if not text.strip():
        return [0.0] * model.get_sentence_embedding_dimension() # Return zero vector for empty text
    embeddings = model.encode(text)
    return embeddings.tolist()

# --- HaasOnline API Helper ---
def get_haas_api_executor():
    if not HAAS_API_ENABLED:
        return None
    
    print("Checking FastAPI wrapper status...")
    try:
        # Use curl to check FastAPI status endpoint
        result = subprocess.run(['curl', '-s', 'http://localhost:8000/status'], capture_output=True, text=True, check=True)
        status_output = json.loads(result.stdout)
        if status_output.get("status") == "authenticated" and status_output.get("haas_api_connected"):
            print("FastAPI wrapper is running and connected to HaasOnline API.")
        else:
            print(f"FastAPI wrapper status: {status_output.get('status')}. HaasOnline API connection: {status_output.get('haas_api_connected')}.")
            print("Skipping HaasOnline API authentication.")
            return None
    except (subprocess.CalledProcessError, json.JSONDecodeError, ConnectionRefusedError) as e:
        print(f"Could not connect to FastAPI wrapper at http://localhost:8000/status: {e}")
        print("Please ensure the FastAPI server is running.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while checking FastAPI status: {e}")
        return None

    print("Authenticating with HaasOnline API...")
    try:
        executor = api.RequestsExecutor(
            host=HAAS_API_HOST,
            port=HAAS_API_PORT,
            state=api.Guest()
        ).authenticate(
            email=HAAS_API_EMAIL,
            password=HAAS_API_PASSWORD
        )
        print("HaasOnline API authenticated.")
        return executor
    except HaasApiError as e:
        print(f"HaasOnline API authentication failed: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during HaasOnline API authentication: {e}")
        return None

# --- Content Parsing Functions ---

def clean_filename(filename: str) -> str:
    """Cleans a filename to be used as a title/name."""
    return os.path.splitext(filename)[0].replace('_', ' ').title()

def parse_function_md(file_path: str, content: str) -> Optional[List[Dict[str, Any]]]:
    """Parses a Markdown file expected to contain HaasScript function definitions."""
    functions_data = []
    # Split content by ### headings to find individual function definitions
    parts = re.split(r'###\s*(.+?)\n', content)
    
    # The first part is usually empty or preamble, skip it
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        details = parts[i+1].strip()

        description_match = re.match(r'^(.*?)\n\s*\*\s*Parameters:', details, re.DOTALL)
        description = description_match.group(1).strip() if description_match else details.split('* Parameters:')[0].strip()

        syntax_match = re.search(r'\*\s*Syntax:\s*`(.+?)`', details)
        syntax = syntax_match.group(1).strip() if syntax_match else None

        return_type_match = re.search(r'\*\s*Returns:\s*`?(.+?)`?\s*-', details)
        return_type = return_type_match.group(1).strip() if return_type_match else None

        # Extract category from parent directory
        category = os.path.basename(os.path.dirname(file_path))
        if category == 'built_in_functions': # If directly under built_in_functions, use filename as category
            category = clean_filename(os.path.basename(file_path))
        
        functions_data.append({
            "name": name,
            "description": description,
            "syntax": syntax,
            "return_type": return_type,
            "category": category,
            "embedding": get_embedding(f"{name} {description}")
        })
    return functions_data if functions_data else None

def parse_example_md(file_path: str, content: str) -> Optional[Dict[str, Any]]:
    """Parses a Markdown file expected to contain HaasScript code examples."""
    script_blocks = re.findall(r'```haasscript\n(.*?)```', content, re.DOTALL)
    if not script_blocks:
        return None # No HaasScript code found

    # Try to get title from first H1 heading
    title_match = re.match(r'#\s*(.+?)\n', content)
    title = title_match.group(1).strip() if title_match else clean_filename(os.path.basename(file_path))

    # Extract description by removing code blocks
    description = re.sub(r'```haasscript\n.*?```', '', content, flags=re.DOTALL).strip()
    
    # Determine strategy_type from parent directory
    strategy_type = os.path.basename(os.path.dirname(file_path))
    if strategy_type == 'strategies': # If directly under strategies, use filename as strategy_type
        strategy_type = clean_filename(os.path.basename(file_path))

    # Combine all script blocks into one content string
    full_script_content = "\n\n".join(script_blocks)

    return {
        "title": title,
        "description": description,
        "script_content": full_script_content,
        "related_functions": [], # To be filled if we implement function linking
        "strategy_type": strategy_type,
        "embedding": get_embedding(f"{title} {description} {full_script_content}")
    }

def parse_concept_md(file_path: str, content: str) -> Optional[Dict[str, Any]]:
    """Parses a Markdown file as a general concept or discussion."""
    # Try to get concept_name from first H1 heading
    concept_name_match = re.match(r'#\s*(.+?)\n', content)
    concept_name = concept_name_match.group(1).strip() if concept_name_match else clean_filename(os.path.basename(file_path))
    
    # If it looks like a chat log, append " (Discussion)"
    if re.search(r'\[\d{13}\]\s*\d+:', content): # Simple heuristic for chat logs
        concept_name += " (Discussion)"

    return {
        "concept_name": concept_name,
        "description": content.strip(),
        "embedding": get_embedding(content.strip())
    }

# --- Main Ingestion Logic ---
def ingest_local_markdown_data():
    print(f"Starting ingestion of local Markdown data from: {GUIDE_CONTENT_PATH}")
    
    all_md_files = glob.glob(os.path.join(GUIDE_CONTENT_PATH, '**', '*.md'), recursive=True)
    
    functions_to_insert = {}
    examples_to_insert = {}
    concepts_to_insert = {}

    for file_path in all_md_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        relative_path = os.path.relpath(file_path, GUIDE_CONTENT_PATH)
        print(f"Processing: {relative_path}")

        # Heuristic-based parsing
        if "built_in_functions" in relative_path:
            # Attempt to parse as function
            parsed_functions = parse_function_md(file_path, content)
            if parsed_functions:
                for func in parsed_functions:
                    functions_to_insert[func["name"]] = func # Use name as key for de-duplication
                print(f"  -> Parsed as {len(parsed_functions)} function(s).")
                continue # Move to next file if successfully parsed as function
        
        # Attempt to parse as example (if it contains haasscript code blocks)
        script_blocks = re.findall(r'```haasscript\n(.*?)```', content, re.DOTALL)
        if script_blocks: # Check for script blocks first
            parsed_example = parse_example_md(file_path, content)
            if parsed_example:
                examples_to_insert[parsed_example["title"]] = parsed_example # Use title as key for de-duplication
                print(f"  -> Parsed as example.")
                continue # Move to next file if successfully parsed as example

        # Otherwise, parse as a general concept/discussion
        parsed_concept = parse_concept_md(file_path, content)
        if parsed_concept:
            concepts_to_insert[parsed_concept["concept_name"]] = parsed_concept # Use concept_name as key for de-duplication
            print(f"  -> Parsed as concept.")
            
    # Convert dicts to lists for insertion
    functions_list = list(functions_to_insert.values())
    examples_list = list(examples_to_insert.values())
    concepts_list = list(concepts_to_insert.values())

    print(f"Parsed {len(functions_list)} unique functions, {len(examples_list)} unique examples, {len(concepts_list)} unique concepts from local Markdown.")
    
    # Call the insertion function
    insert_parsed_data_into_db(functions_list, examples_list, concepts_list)


def ingest_haas_api_scripts_data():
    print("Starting ingestion of HaasOnline API scripts data...")
    executor = get_haas_api_executor()
    if not executor:
        print("Skipping HaasOnline API script ingestion due to authentication failure or disabled API.")
        return

    try:
        all_scripts = api.get_all_scripts(executor)
        print(f"Fetched {len(all_scripts)} scripts from HaasOnline API.")
        
        api_examples_to_insert = {}
        api_concepts_to_insert = {}

        for script in all_scripts:
            # Fetch script content (assuming there's an API for this, or it's in the initial response)
            # For now, we'll use a placeholder for script content
            # In a real scenario, you'd call api.get_script_content(executor, script.script_id) if available
            script_content = f"// HaasScript content for {script.script_name}\n// Script ID: {script.script_id}\n// Description: {script.script_description}"
            
            # Heuristic: If script_description is empty or very short, and it's a "bot" type, treat as example
            # Otherwise, if it has a description, treat as a concept
            # ScriptType: 0=Bot, 1=Indicator, 2=Safety, 3=Insurance, 4=CustomCommand, 5=MarketMaker, 6=Arbitrage, 7=ZoneRecovery
            # ScriptStatus: 0=OK, 1=Error, 2=Warning
            if script.script_type == 0 or script.script_type == 5 or script.script_type == 6 or script.script_type == 7: # Bot, MarketMaker, Arbitrage, ZoneRecovery
                api_examples_to_insert[script.script_name] = {
                    "title": script.script_name,
                    "description": script.script_description or "No description provided.",
                    "script_content": script_content, # Placeholder
                    "related_functions": [],
                    "strategy_type": f"HaasOnline API {script.script_name}", # Use script name as strategy type
                    "embedding": get_embedding(f"{script.script_name} {script.script_description} {script_content}")
                }
            else: # Treat other script types as concepts for now
                api_concepts_to_insert[script.script_name] = {
                    "concept_name": script.script_name,
                    "description": script.script_description or "No description provided.",
                    "embedding": get_embedding(f"{script.script_name} {script.script_description}")
                }
        
        print(f"Parsed {len(api_examples_to_insert)} examples and {len(api_concepts_to_insert)} concepts from HaasOnline API.")
        
        # Call the insertion function for API data
        insert_parsed_data_into_db(None, list(api_examples_to_insert.values()), list(api_concepts_to_insert.values()))

    except HaasApiError as e:
        print(f"Error fetching scripts from HaasOnline API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during HaasOnline API script ingestion: {e}")


def insert_parsed_data_into_db(functions: Optional[List[Dict[str, Any]]], 
                               examples: Optional[List[Dict[str, Any]]], 
                               concepts: Optional[List[Dict[str, Any]]]):
    """Inserts parsed data into the PostgreSQL database."""
    print("Inserting parsed data into database...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if functions:
                    print(f"  Inserting {len(functions)} functions...")
                    # Using psycopg2.extras.execute_values for efficient bulk insertion
                    # Note: UUIDs are generated by the DB, so we don't include 'id'
                    template = "(name, description, syntax, return_type, category, embedding)"
                    data = [(f["name"], f["description"], f["syntax"], f["return_type"], f["category"], f["embedding"]) for f in functions]
                    extras.execute_values(cur, 
                                          f"INSERT INTO haasscript_functions {template} VALUES %s ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, syntax = EXCLUDED.syntax, return_type = EXCLUDED.return_type, category = EXCLUDED.category, embedding = EXCLUDED.embedding", 
                                          data)

                if examples:
                    print(f"  Inserting {len(examples)} examples...")
                    template = "(title, description, script_content, related_functions, strategy_type, embedding)"
                    data = [(e["title"], e["description"], e["script_content"], e["related_functions"], e["strategy_type"], e["embedding"]) for e in examples]
                    # For ON CONFLICT, we need a unique constraint. Assuming 'title' is unique enough for examples.
                    # If titles are not unique, this needs adjustment (e.g., composite unique key or just DO NOTHING)
                    extras.execute_values(cur, 
                                          f"INSERT INTO haasscript_examples {template} VALUES %s ON CONFLICT (title) DO UPDATE SET description = EXCLUDED.description, script_content = EXCLUDED.script_content, related_functions = EXCLUDED.related_functions, strategy_type = EXCLUDED.strategy_type, embedding = EXCLUDED.embedding", 
                                          data)

                if concepts:
                    print(f"  Inserting {len(concepts)} concepts...")
                    template = "(concept_name, description, embedding)"
                    data = [(c["concept_name"], c["description"], c["embedding"]) for c in concepts]
                    extras.execute_values(cur, 
                                          f"INSERT INTO haasscript_concepts {template} VALUES %s ON CONFLICT (concept_name) DO UPDATE SET description = EXCLUDED.description, embedding = EXCLUDED.embedding", 
                                          data)
            conn.commit()
            print("Data insertion complete.")
    except Exception as e:
        print(f"Error inserting data into database: {e}")
        if conn: conn.rollback()


def main():
    print("Starting data ingestion process...")
    
    # Test DB connection
    try:
        with get_db_connection() as conn:
            print("Successfully connected to PostgreSQL database.")
    except Exception as e:
        print(f"Failed to connect to PostgreSQL database: {e}")
        print("Please ensure PostgreSQL is running and DATABASE_URL is correct in .env.")
        return

    # Test embedding model
    try:
        sample_embedding = get_embedding("test string")
        print(f"Successfully generated sample embedding of dimension: {len(sample_embedding)}")
    except Exception as e:
        print(f"Failed to load embedding model or generate embedding: {e}")
        print("Please ensure 'sentence-transformers' is installed and model can be downloaded.")
        return

    # Ingest local Markdown data
    ingest_local_markdown_data()

    # Ingest HaasOnline API scripts data
    ingest_haas_api_scripts_data()

    print("Data ingestion process completed.")

if __name__ == "__main__":
    main()