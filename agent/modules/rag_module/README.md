# RAG Module (Knowledge Base Search)

This module implements a Retrieval Augmented Generation (RAG) pattern by combining semantic search over text embeddings with structured data retrieval from an SQL database. It allows the agent to answer queries using a specialized, pre-indexed knowledge base.

## Functionality

The RAG module is designed to provide precise answers based on a curated set of information. The workflow is as follows:

1.  **Query Embedding**: The input natural language query is converted into a dense vector embedding using an Ollama embedding model (e.g., `bge-m3`).
2.  **Vector Search**: This query embedding is used to search a ChromaDB vector database. ChromaDB stores embeddings of text chunks (documents) and returns the most similar ones based on cosine similarity (or other distance metrics).
3.  **Metadata Retrieval**: Each entry in ChromaDB is associated with metadata, crucially including a `source_document_id`.
4.  **SQL Data Fetching**: The retrieved `source_document_id`(s) are used to query an SQLite database. This SQL database holds detailed, structured information related to the original text chunks. For example, if a text chunk about "Netze BW tariffs 2024" is found via vector search, its `source_document_id` can be used to pull specific tariff tables (`hlzf_data`, `netzentgelte_data`) from SQLite.
5.  **Response Aggregation**: The information retrieved from both the vector search (e.g., text snippets) and the SQL database (structured data) is compiled and returned to the agent for formulating a final answer.

## Components

-   **`main.py`**: Contains the main `run(input_data: dict) -> dict` function that orchestrates the RAG workflow.
-   **`db_utils.py`**: Manages the SQLite database (`rag_sqlite.db` stored in a `database/` subdirectory). It handles schema creation (tables: `knowledge_sources`, `hlzf_data`, `netzentgelte_data`), data insertion, and querying.
-   **`vector_utils.py`**: Manages the ChromaDB vector database (stored in a `chroma_db/` subdirectory). It handles client/collection initialization, generating embeddings via Ollama's `/api/embed` endpoint (using the `bge-m3` model by default), adding documents with metadata, and performing similarity searches.
-   **`AGENT.md`**: Describes the module's capabilities, input parameters, and output structure for the agent's LLM-based controller, enabling it to decide when and how to use this tool.

## Data Model

1.  **`knowledge_sources` (SQLite Table):**
    -   `source_document_id` (TEXT PRIMARY KEY): Unique ID for a text chunk.
    -   `original_text_chunk` (TEXT): The actual text that is embedded and stored in ChromaDB.
    -   `source_description` (TEXT, optional): e.g., "Netze BW Tariff Document 2024, Page 5".

2.  **`hlzf_data` (SQLite Table - Example):**
    -   `id` (INTEGER PK AUTOINCREMENT)
    -   `dno_name` (TEXT), `year` (INTEGER), `timestamp` (INTEGER), `window_type` (TEXT), `time_value` (TEXT)
    -   `source_document_id` (TEXT FK to `knowledge_sources`)

3.  **`netzentgelte_data` (SQLite Table - Example):**
    -   `id` (INTEGER PK AUTOINCREMENT)
    -   `dno_name` (TEXT), `year` (INTEGER), `timestamp` (INTEGER), `voltage_level` (TEXT), `charge_type` (TEXT), `value` (REAL), `unit` (TEXT)
    -   `source_document_id` (TEXT FK to `knowledge_sources`)

4.  **ChromaDB Collection (`rag_collection`):**
    -   **Embeddings**: Vectors generated from `knowledge_sources.original_text_chunk`.
    -   **Documents**: The `original_text_chunk` itself is also stored alongside the embedding.
    -   **Metadatas**: A dictionary associated with each embedding, e.g., `{"source_document_id": "some_id", "category": "tariff_info"}`.
    -   **IDs**: Unique string ID for each entry in ChromaDB (can be the same as `source_document_id` if text chunks are unique per source ID).

## Setup & Data Population

1.  **Dependencies:**
    -   `chromadb`: The vector database. Install via `pip install chromadb`.
    -   `requests`: For communicating with the Ollama API to get embeddings. Install via `pip install requests`.
    -   (Ollama server must be running with the specified embedding model, e.g., `bge-m3`, pulled).

2.  **Database Initialization:**
    -   The SQLite database schema is created automatically when `db_utils.init_db()` is called. This happens if you run `python agent/modules/rag_module/db_utils.py` directly or the first time the module is used in a way that triggers `init_db()` (e.g. via `main.py`'s test block).
    -   The ChromaDB collection is created automatically by `vector_utils.VectorDBManager()` if it doesn't exist upon initialization.

3.  **Populating Data (Example):**
    -   The `if __name__ == '__main__':` block in `db_utils.py` provides an example of adding data to SQLite.
    -   The `if __name__ == '__main__':` block in `vector_utils.py` shows how to add documents and embeddings to ChromaDB (it requires text, metadata, and IDs).
    -   The `if __name__ == '__main__':` block in `main.py` includes a combined example of populating both SQLite and ChromaDB with sample data for testing purposes.
    -   **For production use, a dedicated data ingestion script would be required.** This script would:
        a.  Read data from source documents (PDFs, CSVs, other databases, etc.).
        b.  Chunk text appropriately for embedding.
        c.  Store structured data into SQLite, generating unique `source_document_id`s.
        d.  Store the text chunks into `knowledge_sources` table in SQLite with their IDs.
        e.  Generate embeddings for these text chunks.
        f.  Add the embeddings and corresponding metadata (including the `source_document_id`) to ChromaDB.

## Frameworks Used & Alternatives

-   **Vector Database:**
    -   **Used:** `ChromaDB`. Chosen for its Python-native feel, ease of local file-based persistence (similar to SQLite), and quick setup.
    -   **Alternatives:**
        -   `FAISS`: Highly performant, developed by Facebook AI. More of a library, often requires more setup for storage/serving.
        -   `Weaviate`: Open-source vector search engine with GraphQL API, can be self-hosted or cloud-managed.
        -   `Pinecone`: Managed vector database service (cloud-based).
        -   PostgreSQL with `pgvector` extension: Allows adding vector similarity search capabilities to a standard PostgreSQL database.

-   **SQL Database:**
    -   **Used:** `SQLite`. Chosen for its serverless, file-based nature, making it extremely easy to integrate and manage for local applications. Python has built-in support via the `sqlite3` module.
    -   **Alternatives:**
        -   `PostgreSQL`: Full-featured open-source relational database. Suitable for larger, more complex datasets and concurrent access.
        -   `MySQL`: Another popular open-source relational database.
        -   Dedicated NoSQL databases (e.g., MongoDB) if the structured data is non-relational, though for this module, SQL seems appropriate for the example data.

-   **Embedding Model:**
    -   **Used:** `bge-m3` via Ollama's `/api/embed` endpoint. This keeps the embedding generation within the local Ollama ecosystem.
    -   **Alternatives:**
        -   Other Ollama embedding models (e.g., `nomic-embed-text`, `all-minilm`).
        -   `sentence-transformers` library: Provides easy access to a wide range of pre-trained embedding models that can be downloaded and run locally.
        -   Cloud-based embedding APIs (OpenAI, Cohere, Google Vertex AI, etc.).

-   **Orchestration Frameworks (for more complex RAG):**
    -   While this module implements RAG from scratch for clarity, frameworks can simplify development:
    -   `LangChain`: A popular framework for developing applications powered by language models, with extensive RAG components.
    -   `LlamaIndex`: A data framework for LLM applications, particularly strong for connecting LLMs to custom data sources and building RAG pipelines.

## Future Enhancements

-   Develop a robust data ingestion pipeline.
-   Implement more sophisticated query parsing and generation of SQL queries based on LLM understanding.
-   Allow for updates and deletions in the knowledge base.
-   Improve error handling and logging.
-   Add UI for managing the knowledge base content.
```
