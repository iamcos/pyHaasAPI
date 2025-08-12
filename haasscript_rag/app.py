
from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "HaasScript RAG Server is running!"}), 200

# --- MongoDB Configuration ---
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
client = MongoClient(MONGO_HOST, MONGO_PORT)

def get_project_db(project_name):
    """Gets the database for a specific project."""
    return client[f"rag_{project_name}"]

# --- API Endpoints ---
@app.route('/project', methods=['POST'])
def init_project():
    """Initializes a new project, creating a database for it."""
    data = request.get_json()
    project_name = data.get('project_name')
    if not project_name:
        return jsonify({"error": "Project name is required"}), 400

    try:
        # Simply creating a collection initializes the database
        db = get_project_db(project_name)
        db.memories.insert_one({"system": "Project initialized"})
        return jsonify({"message": f"Project '{project_name}' initialized."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/memory', methods=['POST'])
def add_memory():
    """Adds a new memory to a project's database."""
    data = request.get_json()
    project_name = data.get('project_name')
    memory_content = data.get('memory')

    if not project_name or not memory_content:
        return jsonify({"error": "Project name and memory content are required"}), 400

    try:
        db = get_project_db(project_name)
        db.memories.insert_one({"content": memory_content})
        return jsonify({"message": "Memory added."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory', methods=['GET'])
def search_memory():
    """Searches for memories in a project's database."""
    project_name = request.args.get('project_name')
    query = request.args.get('query')

    if not project_name or not query:
        return jsonify({"error": "Project name and query are required"}), 400

    try:
        db = get_project_db(project_name)
        # Simple text search for now
        results = list(db.memories.find({"$text": {"$search": query}}))
        # Convert ObjectId to string for JSON serialization
        for result in results:
            result['_id'] = str(result['_id'])
        return jsonify(results), 200
    except Exception as e:
        # This will happen if the text index is not created yet
        if "text index required" in str(e):
             # Simple text search for now
            results = list(db.memories.find({"content": {"$regex": query}}))
            # Convert ObjectId to string for JSON serialization
            for result in results:
                result['_id'] = str(result['_id'])
            return jsonify(results), 200
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
