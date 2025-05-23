# Tool: RAG Module (Knowledge Base Search)

This tool performs a search against a specialized knowledge base that combines semantic vector search with structured data retrieval from an SQL database. It is designed to answer queries requiring specific, factual, and potentially complex pre-indexed information, particularly for topics like 'Netze-BW', 'Hochlastzeitfenster', and 'Netzentgelte'.

## When to use:

Use this tool *as a primary option* when the user's prompt asks about or mentions:
- Specific entities or datasets known to be in the knowledge base (e.g., "Netze-BW").
- Terms like "Hochlastzeitfenster" (peak load windows), "Netzentgelte" (network charges), "DNO" (Distribution Network Operator), "Verteilnetzbetreiber".
- Queries seeking factual data that might be structured, such as tariffs, specific time windows, or detailed company-related data points.
- Any query where precise, pre-existing information is likely to provide a better answer than a general web search.

If this tool returns a 'No relevant documents found' or similar negative status, or if the retrieved information is insufficient, then other tools (like a general web search) might be considered as a fallback or for supplementary information.

## Input Parameters:

- `query` (string, required): The user's natural language question or search topic (e.g., "What are the Hochlastzeitfenster for Netze-BW in Winter 2024?", "Netzentgelte Leistung HS Netze-BW").
- `top_n_vector_results` (integer, optional): The number of top matching documents to retrieve from the initial vector search phase. Defaults to 3 if not specified. A smaller number (e.g., 1-3) is often good for focused queries.

## Output:

The tool returns a dictionary containing:
- `status` (string): Overall status of the operation (e.g., "RAG process complete.", "No vector documents found.").
- `query_received` (string): The original query from the input.
- `vector_search_results_summary` (list of dicts): A summary of the top N documents found by the vector search. Each item includes:
    - `vector_db_id` (string): Internal ID from the vector database.
    - `text_preview` (string): A snippet of the text that was embedded and matched.
    - `distance` (float): The similarity distance (lower is typically better).
    - `metadata` (dict): Metadata stored with the vector, including the crucial `source_document_id`.
- `retrieved_sql_data` (dict): A dictionary where keys are `source_document_id`s. Each value is another dictionary containing:
    - `original_embedded_text` (string): The full text chunk that was originally embedded for this source ID.
    - `hlzf_data` (list of dicts): Relevant structured data from the 'hlzf_data' SQL table.
    - `netzentgelte_data` (list of dicts): Relevant structured data from the 'netzentgelte_data' SQL table.
- `combined_summary` (string): A textual summary of the overall findings or status.
- `error` (string, optional): An error message if the process failed critically.

The agent should primarily use the `retrieved_sql_data` (which contains the detailed, structured information) and the `text_summary` from the `original_embedded_text` or `combined_summary` to formulate its answer. The `vector_search_results_summary` can be used for context or if SQL data is sparse.
