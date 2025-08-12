import json
import re

def visualize_script_output(file_path):
    """
    Parses the JSON output from the script generation and displays the
    retrieved context in a readable format.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        result = data.get("result", {})
        retrieved_context = result.get("retrieved_context", "")

        print("--- Retrieved Context for Script Generation ---")

        # Split the context into individual function and concept blocks
        blocks = re.split(r'\n\n(?=Function:|Concept:)', retrieved_context)

        for block in blocks:
            if not block.strip():
                continue

            # Clean up the block content
            block = block.replace('\\n', '\n').strip()
            
            if block.startswith("Function:"):
                # Further split to handle multiple descriptions under one function heading
                parts = block.split("Description:")
                print(f"\n--- {parts[0].strip()} ---")
                if len(parts) > 1:
                    description = "Description:" + parts[1]
                    # Clean up asterisks and extra whitespace
                    description = re.sub(r'\n\s*\*\s*', '\n  - ', description)
                    print(description.strip())

            elif block.startswith("Concept:"):
                parts = block.split("Description:")
                print(f"\n--- {parts[0].strip()} ---")
                if len(parts) > 1:
                    description = "Description:" + parts[1]
                    # Clean up markdown headings
                    description = description.replace("# ", "### ")
                    print(description.strip())
            else:
                print(block)

if __name__ == "__main__":
    visualize_script_output("/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI/script_generation_output.json")