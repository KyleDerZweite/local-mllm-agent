# agent/modules/rag_module/main.py
"""
Main execution logic for the RAG (Retrieval Augmented Generation) Module.

This module coordinates the process of:
1. Receiving a user query.
2. Generating an embedding for the query using `vector_utils` (Ollama bge-m3).
3. Searching a vector database (ChromaDB via `vector_utils`) for relevant text chunks.
4. Retrieving `source_document_id`s from the search results.
5. Fetching structured data from an SQLite database (`db_utils`) using these IDs.
6. Formatting and returning the combined information.
"""

from typing import Dict, Any, List, Optional
import json # For pretty printing results in __main__
import sqlite3 # For the __main__ block data population
import sys # For the __main__ block error exit

try:
    # Attempt to import from the same package (rag_module)
    from . import db_utils
    from . import vector_utils
except ImportError:
    # Fallback for cases where the script might be run directly for testing
    # or the Python path isn't set up for relative imports from '.'
    print("RAG Main: Could not perform relative imports. Attempting direct imports for db_utils and vector_utils.")
    import db_utils
    import vector_utils

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the RAG process for a given user query.

    Args:
        input_data (Dict[str, Any]): A dictionary containing the input for the tool.
            Expected keys:
            - "query" (str): The user's natural language query.
            - "top_n_vector_results" (int, optional): Number of results to fetch from vector search.
                                                       Defaults to 3.

    Returns:
        Dict[str, Any]: A dictionary containing the results of the RAG process.
            Includes:
            - "status" (str): Overall status of the operation.
            - "query_received" (str): The original query.
            - "vector_search_results_summary" (List[Dict]): Summary of top vector search hits.
            - "retrieved_sql_data" (Dict[str, List[Dict]]): Data fetched from SQL for relevant source_ids.
            - "combined_summary" (str): A textual summary of findings.
            - "error" (str, optional): Error message if the process fails at any critical step.
    """
    original_query = input_data.get('query')
    top_n_vector_results = input_data.get('top_n_vector_results', 3)

    # print(f"[RAG Module] Received query: '{original_query}', top_n: {top_n_vector_results}") # Verbose

    if not original_query:
        return {"error": "No query provided for RAG module.", "status": "Error - No query"}

    # 1. Initialize VectorDBManager (uses default path and collection)
    try:
        vec_db_manager = vector_utils.VectorDBManager()
    except Exception as e:
        return {"error": f"Failed to initialize VectorDBManager: {e}", "status": "Error - Vector DB init failed"}

    # 2. Search documents in ChromaDB based on the query
    #    get_ollama_embedding is called by search_documents inside vector_utils
    vector_search_results = vec_db_manager.search_documents(query_text=original_query, n_results=top_n_vector_results)

    if vector_search_results is None or not vector_search_results.get('ids'):
        summary = f"No relevant documents found in the vector database for query: '{original_query}'"
        # print(f"[RAG Module] {summary}") # Verbose
        return {
            "status": "No vector documents found.",
            "query_received": original_query,
            "vector_search_results_summary": [],
            "retrieved_sql_data": {},
            "combined_summary": summary
        }

    # print(f"[RAG Module] Vector search found {len(vector_search_results['ids'])} potential matches.") # Verbose

    # 3. Process results: Get source_document_ids and fetch from SQLite
    retrieved_sql_data_by_source: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    vector_hits_summary: List[Dict[str, Any]] = []
    # unique_source_document_ids = set() # Not strictly needed as dict keys are unique

    for i in range(len(vector_search_results['ids'])):
        doc_id = vector_search_results['ids'][i] # This is the ChromaDB ID
        doc_text_preview = vector_search_results['documents'][i] 
        metadata = vector_search_results['metadatas'][i]
        distance = vector_search_results['distances'][i]
        source_document_id = metadata.get('source_document_id') # This is the ID linking to SQLite

        vector_hits_summary.append({
            "vector_db_id": doc_id,
            "text_preview": doc_text_preview[:150] + "..." if len(doc_text_preview) > 150 else doc_text_preview,
            "distance": f"{distance:.4f}",
            "metadata": metadata # Includes the source_document_id
        })

        if source_document_id:
            # unique_source_document_ids.add(source_document_id) # Not needed
            if source_document_id not in retrieved_sql_data_by_source:
                # Fetch data from SQLite for this source_document_id
                sql_data = db_utils.get_data_by_source_id(source_document_id)
                # Also fetch the original text chunk that was embedded and stored in SQLite
                original_text_from_sql = db_utils.get_knowledge_source_text(source_document_id)
                retrieved_sql_data_by_source[source_document_id] = {
                    "original_embedded_text_from_sql": original_text_from_sql or "N/A", # Text from knowledge_sources table
                    "hlzf_data": sql_data.get("hlzf_data", []),
                    "netzentgelte_data": sql_data.get("netzentgelte_data", [])
                }
        else:
            print(f"[RAG Module] Warning: Vector DB entry {doc_id} missing 'source_document_id' in metadata.")

    if not retrieved_sql_data_by_source:
        summary = f"Vector search found documents, but no linked SQL data could be retrieved for query: '{original_query}' (perhaps missing source_document_id in metadata or no corresponding SQL entries)."
    else:
        summary = f"Successfully retrieved information from vector and SQL databases for query: '{original_query}'"

    # print(f"[RAG Module] {summary}") # Verbose

    return {
        "status": "RAG process complete.",
        "query_received": original_query,
        "vector_search_results_summary": vector_hits_summary,
        "retrieved_sql_data": retrieved_sql_data_by_source,
        "combined_summary": summary
    }

if __name__ == '__main__':
    """
    Example usage of the RAG module's run function.
    Assumes that the SQLite database (rag_sqlite.db) and ChromaDB collection 
    have been initialized and populated with sample data (e.g., by running db_utils.py 
    and vector_utils.py or a dedicated data loading script).
    """
    print("--- Testing RAG Module --- ")
    print("IMPORTANT: This test assumes that `db_utils.init_db()` has been run to create the SQLite schema,")
    print("and that `vector_utils.VectorDBManager` has been used to add relevant embeddings")
    print("(e.g., via a separate data loading script or its own __main__ block if it adds data).")
    print(f"For this test to be meaningful, ensure sample data for source_id '{db_utils.DB_NAME}' (SQLite) and '{vector_utils.CHROMA_DIRECTORY}' (Chroma) is loaded.") # Corrected constants

    # Ensure DB is initialized (idempotent)
    print("\nInitializing databases (creates if not exist)...")
    db_utils.init_db() # Initializes SQLite
    # VectorDBManager init is called inside run(), which also creates if not exist.

    # --- Populate Data (Simplified for this test, ideally use a separate script) ---
    # This section is crucial for the test to work. It adds the specific sample data.
    print("\nPopulating sample data for RAG test...")
    # Using a unique source_id for this test to avoid conflicts if other tests use similar IDs
    sample_source_id_for_rag_main = "netze_bw_doc_rag_main_test_001" 
    sample_text_chunk = "Dno Verteilnetzbetreiber Netze-BW Hochlastzeifenster Netzentgelte. Information about Netze BW peak load windows (Hochlastzeitfenster) and network charges (Netzentgelte) for the year 2024."
    
    # Add to SQLite
    db_utils.add_knowledge_source(sample_source_id_for_rag_main, sample_text_chunk, "Netze BW Combined Info 2024 (RAG Main Test)")
    # Clear potential old data for this specific test source_id before adding
    with sqlite3.connect(db_utils.DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hlzf_data WHERE source_document_id = ?", (sample_source_id_for_rag_main,))
        cursor.execute("DELETE FROM netzentgelte_data WHERE source_document_id = ?", (sample_source_id_for_rag_main,))
        conn.commit()
    db_utils.add_hlzf_entry("netze-bw", 2024, 1745056892, "Winter_RAG_Test_Start", "06:30:00", sample_source_id_for_rag_main)
    db_utils.add_hlzf_entry("netze-bw", 2024, 1745056892, "Winter_RAG_Test_Ende", "21:30:00", sample_source_id_for_rag_main)
    db_utils.add_netzentgelte_entry("netze-bw", 2024, 1745056892, "hs_rag_test", "Leistung", 60.00, "EUR/kW", sample_source_id_for_rag_main)
    db_utils.add_netzentgelte_entry("netze-bw", 2024, 1745056892, "hs_rag_test", "Arbeit", 1.30, "ct/kWh", sample_source_id_for_rag_main)
    print(f"SQLite data populated for source_id: {sample_source_id_for_rag_main}")

    # Add to ChromaDB
    try:
        # Using default path/collection from vector_utils for the test manager
        vdb_manager_test = vector_utils.VectorDBManager() 
        # Check if this specific document ID already exists in Chroma to avoid error on re-run
        # Here, the Chroma ID is the same as the SQLite source_document_id for simplicity.
        existing_doc = vdb_manager_test.collection.get(ids=[sample_source_id_for_rag_main])
        if not existing_doc or not existing_doc['ids']:
            vdb_manager_test.add_documents(
                documents=[sample_text_chunk],
                metadatas=[{"source_document_id": sample_source_id_for_rag_main, "category": "netze_bw_combined_rag_test"}],
                ids=[sample_source_id_for_rag_main] 
            )
            print(f"ChromaDB data populated for ID: {sample_source_id_for_rag_main}")
        else:
            print(f"ChromaDB entry for ID {sample_source_id_for_rag_main} already exists. Skipping add.")
    except Exception as e_vdb_populate:
        print(f"Error populating ChromaDB for test: {e_vdb_populate}. Ollama server running with '{vector_utils.EMBEDDING_MODEL_NAME}' required.")
        sys.exit(1) # Exit if Chroma population fails, as RAG tests will be meaningless.

    print("--- Sample Data Population Complete ---")

    test_queries = [
        "Tell me about Netze-BW Hochlastzeifenster", # Should hit the sample_text_chunk
        "What are the Netzentgelte from Netze-BW for hs_rag_test?", # Should hit
        "Information on DNO Verteilnetzbetreiber Netze-BW", # Should hit
        "Details about something not in the database like solar panel support" # Should not find specific SQL data
    ]

    for i, t_query in enumerate(test_queries):
        print(f"\n--- RAG Test Case {i+1} ---")
        test_input = {"query": t_query, "top_n_vector_results": 1} # Fetch top 1 for focused test
        print(f"Input: {test_input}")
        output = run(test_input)
        print("Output:")
        try:
            print(json.dumps(output, indent=2, default=str))
        except TypeError: # Fallback if json.dumps fails for some reason
            print(output) 
    
    print("\n--- RAG Module Testing Finished ---")
```
