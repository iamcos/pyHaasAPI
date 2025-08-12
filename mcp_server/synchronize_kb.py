import os
import sys
import json
from dotenv import load_dotenv
import psycopg2
from psycopg2 import extras
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# Add project root to sys.path to import pyHaasAPI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pyHaasAPI import api
from pyHaasAPI.exceptions import HaasApiError

# --- Configuration ---
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env')))

DATABASE_URL = os.getenv("DATABASE_URL")
HAAS_API_HOST = os.getenv("API_HOST", "127.0.0.1")
HAAS_API_PORT = int(os.getenv("API_PORT", 8090))
HAAS_API_EMAIL = os.getenv("API_EMAIL")
HAAS_API_PASSWORD = os.getenv("API_PASSWORD")

# --- Database Helpers ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# --- Embedding Model Helper ---
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embedding(text: str) -> List[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()

# --- Synchronization Logic ---
def synchronize_haasscript_commands(executor):
    print("--- Synchronizing HaasScript Commands ---")
    try:
        commands = api.get_haasscript_commands(executor)
        if not commands:
            print("No commands found or error fetching commands.")
            return

        functions_to_insert = []
        for command_data in commands:
            command_name = command_data.get("CommandName")
            description = command_data.get("Description")
            category = command_data.get("Category")
            return_description = command_data.get("ReturnDescription", "")

            if command_name and description and category:
                functions_to_insert.append({
                    "name": command_name,
                    "description": description,
                    "syntax": "", 
                    "return_type": str(return_description),
                    "category": category,
                    "embedding": get_embedding(f"{command_name} {description}")
                })
                print(f"Lengths: Name={len(command_name)}, Description={len(description)}, ReturnType={len(str(return_description))}, Category={category}") # Debugging line
        
        print(f"Found {len(functions_to_insert)} commands to synchronize.")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                template = "(name, description, syntax, return_type, category, embedding)"
                data = [(f["name"], f["description"], f["syntax"], f["return_type"], f["category"], f["embedding"]) for f in functions_to_insert]
                extras.execute_values(cur, 
                                      f"INSERT INTO haasscript_functions {template} VALUES %s ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, syntax = EXCLUDED.syntax, return_type = EXCLUDED.return_type, category = EXCLUDED.category, embedding = EXCLUDED.embedding", 
                                      data)
            conn.commit()
        print("HaasScript commands synchronized successfully.")

    except HaasApiError as e:
        print(f"Error synchronizing commands: {e}")

def synchronize_haasscripts(executor):
    print("--- Synchronizing HaasScripts ---")
    try:
        scripts = api.get_all_scripts(executor)
        print(f"Scripts retrieved: {scripts}") # Added for debugging
        print(f"Found {len(scripts)} scripts to synchronize.")

        examples_to_insert = []
        for script in scripts:
            script_record = api.get_script_record(executor, script['script_id'])
            examples_to_insert.append({
                "title": script_record.script_name,
                "description": script_record.script_description,
                "script_content": script_record.script_content,
                "related_functions": [], # This could be improved later
                "strategy_type": "HaasOnline API",
                "embedding": get_embedding(f"{script_record.script_name} {script_record.script_description} {script_record.script_content}")
            })

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                template = "(title, description, script_content, related_functions, strategy_type, embedding)"
                data = [(e["title"], e["description"], e["script_content"], e["related_functions"], e["strategy_type"], e["embedding"]) for e in examples_to_insert]
                extras.execute_values(cur, 
                                      f"INSERT INTO haasscript_examples {template} VALUES %s ON CONFLICT (title) DO UPDATE SET description = EXCLUDED.description, script_content = EXCLUDED.script_content, related_functions = EXCLUDED.related_functions, strategy_type = EXCLUDED.strategy_type, embedding = EXCLUDED.embedding", 
                                      data)
            conn.commit()
        print("HaasScripts synchronized successfully.")

    except HaasApiError as e:
        print(f"Error synchronizing scripts: {e}")

def main():
    print("Starting knowledge base synchronization...")
    executor = api.RequestsExecutor(
        host=HAAS_API_HOST,
        port=HAAS_API_PORT,
        state=api.Guest()
    ).authenticate(
        email=HAAS_API_EMAIL,
        password=HAAS_API_PASSWORD
    )

    synchronize_haasscript_commands(executor)
    synchronize_haasscripts(executor)

    print("Knowledge base synchronization completed.")

if __name__ == "__main__":
    main()
