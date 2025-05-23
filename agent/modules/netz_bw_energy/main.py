# agent/modules/netz_bw_energy/main.py
"""
Netze BW Energy Knowledge Base Module (Simulated) for the Local Multimodal LLM Agent.

This module simulates querying a specialized knowledge base for information related to
Netze BW, particularly concerning energy costs, tariffs, and related company information.
It serves as a simple example of a domain-specific tool that the agent can consult.

The current implementation uses a hardcoded Python dictionary (`SIMULATED_KB`)
to store and retrieve information. It performs basic keyword matching against queries.
This module will be preserved as a simpler example, while a more advanced 'rag_module'
with actual Vector DB and SQL DB integration is planned based on user feedback.
"""

from typing import Dict, Any, Optional, List # Added List for query_keywords type hint

# Simulated Knowledge Base for Netze BW Energy
# In a real RAG system, this would connect to a vector DB and a larger database.
SIMULATED_KB: Dict[str, Dict[str, Any]] = {
    "residential_electricity_price": {
        "query_keywords": ["electricity price", "residential", "home", "household", "strompreis privatkunden"],
        "data": {
            "price_kwh_ct": 30.5,
            "base_fee_eur_month": 8.50,
            "tariff_name": "NetzeStrom Privat Plus",
            "valid_from": "2024-01-01",
            "source": "Simulated Netze BW internal document KBP-2024-01A"
        },
        "text_summary": "The current electricity price for residential customers under the NetzeStrom Privat Plus tariff is 30.5 ct/kWh with a monthly base fee of 8.50 EUR, valid from January 1, 2024."
    },
    "new_connection_contact": {
        "query_keywords": ["new connection", "contact", "anschluss", "netzanschluss"],
        "data": {
            "department": "Netzanschluss-Service",
            "phone": "0800-123-4567",
            "email": "netzanschluss@netze-bw-simulated.de",
            "website_info": "Visit www.netze-bw-simulated.de/netzanschluss for forms and details."
        },
        "text_summary": "For new connections, please contact Netze BW's Netzanschluss-Service at 0800-123-4567 or netzanschluss@netze-bw-simulated.de. Further information is available on their website."
    },
    "company_overview": {
        "query_keywords": ["about netze bw", "company information", "who is netze bw"],
        "data": {
            "full_name": "Netze BW GmbH",
            "role": "Distribution Network Operator (DNO) in Baden-Württemberg, Germany",
            "parent_company": "EnBW Energie Baden-Württemberg AG"
        },
        "text_summary": "Netze BW GmbH is the largest distribution network operator for electricity, gas, and water in Baden-Württemberg, Germany. It is a subsidiary of EnBW AG."
    }
}

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates querying a knowledge base for Netze BW energy information.

    This function takes an `input_data` dictionary which should contain a 'query' string.
    It performs a case-insensitive keyword search within the predefined `SIMULATED_KB`.
    If matching keywords are found for an entry, the entry's data and summary are returned.

    Args:
        input_data (Dict[str, Any]): A dictionary containing the input for the tool.
            Expected keys:
            - "query" (str): The question or topic to query within the Netze BW knowledge base.

    Returns:
        Dict[str, Any]: A dictionary containing the results of the simulated query.
            Includes:
            - "status" (str): A message indicating if information was retrieved or not.
            - "query_received" (str): The original query string (case-preserved).
            - "retrieved_info" (Optional[Dict[str, Any]]): The structured data from the KB if found,
              otherwise None.
            - "text_summary" (str): A human-readable summary of the findings or a message
              indicating no information was found.
            - "error" (str, optional): An error message if the query is missing.
    """
    original_query = input_data.get('query') # Preserve original case for echoed query
    query_lower = original_query.lower() if original_query else ""
    
    # print(f"[Netze BW KB Tool] Received query: '{original_query}' (searching as: '{query_lower}')") # Verbose

    if not original_query: # Check original_query for presence
        return {"error": "No query provided for Netze BW knowledge base.", 
                "retrieved_info": None, 
                "status": "Error - No query",
                "text_summary": "Query was empty."}

    found_entry: Optional[Dict[str, Any]] = None
    best_match_score = 0

    # Simple keyword matching simulation: count keyword occurrences in query.
    for kb_item_key, entry_content in SIMULATED_KB.items():
        current_score = 0
        keywords: List[str] = entry_content.get("query_keywords", [])
        for keyword in keywords:
            if keyword in query_lower:
                current_score += 1
        
        # Prefer entries with more matching keywords.
        if current_score > 0 and current_score > best_match_score:
            best_match_score = current_score
            found_entry = entry_content
        # Basic tie-breaking: if scores are equal, one found earlier might be kept.
        # More sophisticated scoring could be added (e.g., keyword importance).

    if found_entry:
        # print(f"[Netze BW KB Tool] Found matching entry. Summary: {found_entry['text_summary']}") # Verbose
        return {
            "status": "Information retrieved from Netze BW knowledge base (simulated).",
            "query_received": original_query,
            "retrieved_info": found_entry.get('data'), # Return only the 'data' part
            "text_summary": found_entry.get('text_summary')
        }
    else:
        summary = f"No specific information found in Netze BW knowledge base for query: '{original_query}'"
        # print(f"[Netze BW KB Tool] {summary}") # Verbose
        return {
            "status": "No information found in Netze BW knowledge base (simulated).",
            "query_received": original_query,
            "retrieved_info": None,
            "text_summary": summary
        }

if __name__ == '__main__':
    """
    Example usage of the run function when the script is executed directly.
    Demonstrates how the simulated Netze BW knowledge base responds to various queries.
    """
    print("--- Testing Netze BW Energy Knowledge Base Module (Simulated) ---")
    test_inputs = [
        {"query": "What is the residential electricity price from Netze BW?"},
        {"query": "Netze BW contact for new connection"},
        {"query": "information about netze bw company"},
        {"query": "Netze BW solar panel subsidies"}, # Expected: Not in KB
        {"query": "netzanschluss strompreis"}, # Should match multiple keywords from different entries
        {"query": None} # Error case
    ]

    for i, test_input in enumerate(test_inputs):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Input: {test_input}")
        actual_input_for_run = test_input if test_input.get("query") is not None else {"query": None}
        output = run(actual_input_for_run)
        print(f"Output: {output}")
```
