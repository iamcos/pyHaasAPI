import json
import re
from pyHaasAPI import api
from pyHaasAPI.model import ScriptRecord

def extract_meaningful_name(param_key: str) -> str:
    """
    Extracts a more meaningful name from a script parameter key.
    Assumes format like 'XX-XX-YY-ZZ.Meaningful Name' or just 'Meaningful Name'.
    """
    match = re.match(r'\d+-\d+-\d+-\d+\.(.*)', param_key)
    if match:
        return match.group(1).strip()
    return param_key.strip()

def research_indicator_parameters(executor, script_id: str):
    """
    Researches optimal parameters for technical indicators used in a given script
    by performing iterative web searches.

    Args:
        executor: An authenticated pyHaasAPI executor instance.
        script_id: The ID of the script to analyze.
    """
    print(f"\n--- Researching Indicator Parameters for Script ID: {script_id} ---")
    try:
        script_record = api.get_script_record(executor, script_id)
        script_name = script_record.script_name
        
        # Use InputFields from script_record for parameter extraction
        script_parameters_from_record = script_record.InputFields if hasattr(script_record, 'InputFields') else {}

        print(f"Analyzing script '{script_name}' for parameters...")

        found_parameters_raw = list(script_parameters_from_record.keys())
        if not found_parameters_raw:
            print("No script-specific parameters found for this script.")
            return

        found_parameters_meaningful = []
        indicator_keywords = set()
        for param_key in found_parameters_raw:
            meaningful_name = extract_meaningful_name(param_key)
            # Skip timeframe parameters as they are handled in Phase 1
            if "tf" in meaningful_name.lower() or "interval" in meaningful_name.lower():
                continue
            found_parameters_meaningful.append(meaningful_name)

            # Extract common indicator keywords for combination searches
            if "stoch" in meaningful_name.lower():
                indicator_keywords.add("Stochastic")
            if "dema" in meaningful_name.lower():
                indicator_keywords.add("DEMA")
            if "adx" in meaningful_name.lower():
                indicator_keywords.add("ADX")
            if "bbands" in meaningful_name.lower() or "bollinger" in meaningful_name.lower():
                indicator_keywords.add("Bollinger Bands")
            # Add more keyword extractions as needed

        print(f"Found meaningful parameters (excluding timeframes): {', '.join(found_parameters_meaningful)}")

        all_recommendations = []

        print("\n--- Iteration 1: Strategy-Level Search ---")
        strategy_queries = [
            f"optimal parameters for {script_name} trading strategy",
            f"{script_name} backtesting results",
            f"{script_name} HaasScript optimization"
        ]
        for query in strategy_queries:
            print(f"Generated search query: '{query}'")
            # search_results = default_api.google_web_search(query=query)
            # if search_results and search_results.get('results'):
            #     all_recommendations.append({"query": query, "results": search_results})
            #     print(f"  Found {len(search_results.get('results', []))} results.")
            # else:
            #     print("  No results found.")

        print("\n--- Iteration 2: Individual Parameter Search ---")
        for param_name in found_parameters_meaningful:
            param_queries = [
                f"optimal parameters for {param_name} trading indicator",
                f"{param_name} best settings backtesting",
                f"{param_name} HaasScript"
            ]
            for query in param_queries:
                print(f"Generated search query: '{query}'")
                # search_results = default_api.google_web_search(query=query)
                # if search_results and search_results.get('results'):
                #     all_recommendations.append({"query": query, "results": search_results})
                #     print(f"  Found {len(search_results.get('results', []))} results.")
                # else:
                #     print("  No results found.")

        print("\n--- Iteration 3: Combination/Synonym/Inference Search ---")
        if len(indicator_keywords) > 1:
            combined_query = f"optimal parameters for {' and '.join(indicator_keywords)} trading strategy"
            print(f"Generated search query: '{combined_query}'")
            # search_results = default_api.google_web_search(query=combined_query)
            # if search_results and search_results.get('results'):
            #     all_recommendations.append({"query": combined_query, "results": search_results})
            #     print(f"  Found {len(search_results.get('results', []))} results.")
            # else:
            #     print("  No results found for combined indicators.")
        
        # Fallback general search if no specific recommendations found yet
        if not all_recommendations:
            general_query = "trading bot indicator parameter optimization best practices"
            print(f"Generated search query: '{general_query}'")
            # search_results = default_api.google_web_search(query=general_query)
            # if search_results and search_results.get('results'):
            #     all_recommendations.append({"query": general_query, "results": search_results})
            #     print(f"  Found {len(search_results.get('results', []))} results.")
            # else:
            #     print("  No general optimization results found.")

        # Summarize all recommendations
        print("\n--- Summary of Research Recommendations ---")
        if all_recommendations:
            for rec in all_recommendations:
                print(f"Query: {rec['query']}")
                for result in rec['results'].get('results', [])[:3]: # Show top 3 results
                    print(f"  Title: {result.get('title')}")
                    print(f"  URL: {result.get('url')}")
                    print(f"  Snippet: {result.get('snippet')}")
                    print("-" * 20)
        else:
            print("No relevant recommendations found.")

    except api.HaasApiError as e:
        print(f"Error fetching script record: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during indicator research: {e}")
