# Netze BW Energy Knowledge Base Module

This module provides the agent with access to a specialized, simulated knowledge base focused on Netze BW, particularly concerning energy costs, tariffs, and related company information.

## Functionality

The primary role of this module is to act as a first-pass information source for queries specifically related to Netze BW. Instead of immediately resorting to general web searches, the agent can consult this curated knowledge base. This aligns with the concept of Retrieval Augmented Generation (RAG), where a system retrieves relevant information from a dedicated store before generating a response.

**Current Implementation (Simulated):**
The current `main.py` simulates this knowledge base. It contains a hardcoded Python dictionary (`SIMULATED_KB`) with sample information about Netze BW's residential electricity prices, new connection contacts, and a company overview. The `run` function performs a simple keyword matching against this dictionary to find and return relevant entries. This allows for testing the agent's ability to use a specialized data source tool before attempting more general ones.

## `AGENT.md`

The `AGENT.md` file for this module is critical for guiding the `AgentController`'s LLM:
- **Tool Name:** "Netze BW Energy Knowledge Base"
- **Description:** Explains that the tool queries a specialized knowledge base for Netze BW information (energy costs, tariffs, company details) and should be used before general web searches for such topics.
- **When to use:** Instructs the LLM to use this tool first for queries about Netze BW energy costs, tariffs, specific programs, or any factual data likely to be pre-indexed. It also notes that a web search could be a fallback.
- **Input Parameters:**
    - `query` (string, required): The specific question or topic to query (e.g., "current electricity price for residential customers").
- **Output:** Retrieved information (text snippets, structured data) or a statement if no information is found.

## `main.py`

The `main.py` script implements the simulated knowledge base lookup.

### `run(input_data: dict) -> dict` function:

- **Input (`input_data` dict):**
    - Expects a dictionary with a `"query"` key containing the user's question or search topic.
- **Output (dict):**
    - Returns a dictionary containing:
        - `status` (string): Message indicating the outcome (e.g., "Information retrieved from Netze BW knowledge base (simulated).").
        - `query_received` (string): The original query.
        - `retrieved_info` (dict or None): The structured data found in the knowledge base, or `None` if no match.
        - `text_summary` (string): A human-readable summary of the findings or a message indicating no information was found.
        - `error` (string, optional): If an error occurs (e.g., no query provided).

### Standalone Execution:
Running `python agent/modules/netz_bw_energy/main.py` directly will execute a test block within its `if __name__ == '__main__':` section, demonstrating how it responds to various queries based on its simulated data.

## Future Enhancements (for a real RAG implementation):

As per user feedback, the vision for this module is a full RAG system. This would involve:
- **Vector Database:** Implementing or integrating a vector database (e.g., FAISS, ChromaDB, Weaviate) to store embeddings of text chunks from a larger Netze BW information corpus.
- **Data Ingestion Pipeline:** Creating a process to load, chunk, and generate embeddings for documents and data related to Netze BW.
- **"Big Database" Integration:** Connecting the vector search results (which would yield IDs or references) to a more extensive, structured database (e.g., SQL, NoSQL) to retrieve the full, detailed information.
- **Semantic Search:** The `run` function would convert the input query into an embedding, perform a similarity search in the vector DB, and then use the results to fetch data from the main database.
- **Contextual Summarization:** Potentially using an LLM to summarize or synthesize information retrieved from multiple sources within the knowledge base.
