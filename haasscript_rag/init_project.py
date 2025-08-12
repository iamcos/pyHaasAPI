
import requests
import pymongo

# --- Configuration ---
PROJECT_NAME = "pyHaasAPI"
RAG_SERVER_URL = "http://localhost:5001"
MONGO_HOST = "localhost"
MONGO_PORT = 27017

def main():
    """Initializes the project with the RAG server and creates the text index."""
    # 1. Initialize the project via the RAG server
    try:
        response = requests.post(f"{RAG_SERVER_URL}/project", json={"project_name": PROJECT_NAME})
        response.raise_for_status()
        print(f"Successfully initialized project: {PROJECT_NAME}")
        print(response.json()["message"])
    except requests.exceptions.RequestException as e:
        print(f"Error initializing project: {e}")
        return

    # 2. Create the text index in MongoDB
    try:
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        db = client[f"rag_{PROJECT_NAME}"]
        db.memories.create_index([("content", pymongo.TEXT)])
        print("Successfully created text index on 'content' field.")
    except Exception as e:
        print(f"Error creating text index: {e}")

if __name__ == "__main__":
    main()
