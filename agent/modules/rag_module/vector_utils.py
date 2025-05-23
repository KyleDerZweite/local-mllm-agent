# agent/modules/rag_module/vector_utils.py
"""
Vector database utilities for the RAG module, using ChromaDB and Ollama embeddings.

Handles:
- Initialization of a ChromaDB client and collection.
- Generation of text embeddings using a specified Ollama model (e.g., bge-m3).
- Adding documents (text chunks with metadata) to the ChromaDB collection.
- Searching the collection for documents similar to a query embedding.
"""

import chromadb
import requests
import json
from typing import List, Dict, Any, Optional
import os

# Attempt to import Ollama configuration from the agent's core config
try:
    from core.config import OLLAMA_API_BASE_URL
except ImportError:
    print("vector_utils: Could not import OLLAMA_API_BASE_URL from core.config. Using default.")
    OLLAMA_API_BASE_URL = "http://localhost:11434/api"

CHROMA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'chroma_db') # Store Chroma data in 'chroma_db' subfolder
DEFAULT_COLLECTION_NAME = "rag_collection"
EMBEDDING_MODEL_NAME = "bge-m3" # As specified by user

def get_ollama_embedding(text: str, model_name: str = EMBEDDING_MODEL_NAME, ollama_base_url: str = OLLAMA_API_BASE_URL) -> Optional[List[float]]:
    """
    Generates an embedding for the given text using a specified Ollama model via the /api/embed endpoint.

    Args:
        text (str): The text to embed.
        model_name (str): The name of the Ollama embedding model to use (e.g., 'bge-m3').
        ollama_base_url (str): The base URL for the Ollama API.

    Returns:
        Optional[List[float]]: The generated embedding (a list of floats), or None if an error occurs.
    """
    embed_url = f"{ollama_base_url}/embed" # Corrected endpoint name
    payload = {
        "model": model_name,
        "prompt": text # For some models, 'prompt' is used, for others 'text'. '/embed' typically uses 'prompt'.
    }
    # print(f"VectorUtils: Getting embedding for text: '{text[:50]}...' from model: {model_name} at {embed_url}") # Verbose
    try:
        response = requests.post(embed_url, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        embedding = response_data.get("embedding")
        if not isinstance(embedding, list) or not all(isinstance(n, (float, int)) for n in embedding):
            print(f"VectorUtils Error: Ollama embedding response did not contain a valid list of floats. Response: {response_data}")
            return None
        return [float(n) for n in embedding]
    except requests.exceptions.Timeout as e:
        print(f"VectorUtils Error: Timeout connecting to Ollama at {embed_url} for embeddings: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"VectorUtils Error: Could not connect to Ollama at {embed_url} for embeddings: {e}")
        return None
    except json.JSONDecodeError:
        print(f"VectorUtils Error: Could not decode JSON response from Ollama embeddings. Response: {response.text[:200]}...")
        return None
    except KeyError:
        print(f"VectorUtils Error: 'embedding' key missing in Ollama response: {response.json() if response else 'No response'}")
        return None

class VectorDBManager:
    """
    Manages interactions with a ChromaDB vector database.
    Provides methods for initializing, adding documents, and searching.
    """
    def __init__(self, path: str = CHROMA_DIRECTORY, collection_name: str = DEFAULT_COLLECTION_NAME):
        """
        Initializes the VectorDBManager.

        Args:
            path (str): The directory path where ChromaDB data will be persisted.
            collection_name (str): The name of the collection to use within ChromaDB.
        """
        print(f"VectorDBManager: Initializing ChromaDB client at path: {path}")
        # Ensure the ChromaDB directory exists
        os.makedirs(path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name)
        print(f"VectorDBManager: Collection '{collection_name}' loaded/created. Document count: {self.collection.count()}")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> bool:
        """
        Adds documents (text chunks) and their embeddings to the ChromaDB collection.
        Embeddings are generated using the configured Ollama model.

        Args:
            documents (List[str]): A list of text strings to embed and store.
            metadatas (List[Dict[str, Any]]): A list of metadata dictionaries, one for each document.
                                             Must include a 'source_document_id' for linking to SQL DB.
            ids (List[str]): A list of unique IDs, one for each document.

        Returns:
            bool: True if documents were added successfully, False otherwise.
        """
        if not (len(documents) == len(metadatas) == len(ids)):
            print("VectorDBManager Error: Documents, metadatas, and ids lists must have the same length.")
            return False

        embeddings: List[List[float]] = []
        valid_documents = []
        valid_metadatas = []
        valid_ids = []

        print(f"VectorDBManager: Generating embeddings for {len(documents)} documents...")
        for i, doc_text in enumerate(documents):
            embedding = get_ollama_embedding(doc_text)
            if embedding:
                embeddings.append(embedding)
                valid_documents.append(doc_text)
                valid_metadatas.append(metadatas[i])
                valid_ids.append(ids[i])
            else:
                print(f"VectorDBManager Warning: Failed to generate embedding for document ID {ids[i]}. Skipping.")
        
        if not valid_documents:
            print("VectorDBManager Error: No valid embeddings generated. No documents added.")
            return False

        try:
            print(f"VectorDBManager: Adding {len(valid_documents)} documents to collection '{self.collection_name}'.")
            self.collection.add(
                embeddings=embeddings,
                documents=valid_documents, # Store the original text for reference if needed
                metadatas=valid_metadatas,
                ids=valid_ids
            )
            print(f"VectorDBManager: Documents added. New count: {self.collection.count()}")
            return True
        except Exception as e:
            # ChromaDB can raise various exceptions, e.g., for duplicate IDs if not handled by get_or_create.
            # For `add`, if an ID already exists, it should ideally update. If that's not desired,
            # an `upsert` or a check-then-add/update logic would be needed.
            # ChromaDB's default `add` behavior for existing IDs might vary or error; consult its docs.
            # For simplicity, we'll catch a general exception here.
            print(f"VectorDBManager Error: Failed to add documents to ChromaDB: {e}")
            return False

    def search_documents(self, query_text: str, n_results: int = 3) -> Optional[Dict[str, List[Any]]]:
        """
        Searches the collection for documents similar to the query text.

        Args:
            query_text (str): The text to search for.
            n_results (int): The number of top similar results to return.

        Returns:
            Optional[Dict[str, List[Any]]]: A dictionary containing lists of 'ids',
            'documents' (text), 'metadatas', and 'distances' for the found results.
            Returns None if the query embedding fails or search fails.
            ChromaDB query results typically look like:
            `{'ids': [[id1, id2]], 'documents': [[doc1, doc2]], 'metadatas': [[meta1, meta2]], 'distances': [[dist1, dist2]]}`
            This method flattens these lists for easier use if results are found.
        """
        print(f"VectorDBManager: Searching for documents similar to: '{query_text[:50]}...' (top {n_results})")
        query_embedding = get_ollama_embedding(query_text)
        if not query_embedding:
            print("VectorDBManager Error: Could not generate embedding for query text. Search aborted.")
            return None

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances'] # Specify what to include
            )
            # print(f"VectorDBManager: Raw search results: {results}") # Verbose
            
            # Flatten results if not empty (ChromaDB returns lists of lists)
            # Check if results are valid and not empty before trying to access indices
            if results and all(isinstance(results.get(key), list) and len(results.get(key, [])) > 0 for key in ['ids', 'documents', 'metadatas', 'distances']):
                return {
                    'ids': results['ids'][0],
                    'documents': results['documents'][0],
                    'metadatas': results['metadatas'][0],
                    'distances': results['distances'][0]
                }
            else:
                print("VectorDBManager: Search returned no results or results format is unexpected.")
                return {'ids': [], 'documents': [], 'metadatas': [], 'distances': []}

        except Exception as e:
            print(f"VectorDBManager Error: Error querying ChromaDB collection: {e}")
            return None

if __name__ == '__main__':
    """
    Example usage: Initializes the VectorDBManager, adds some sample documents,
    and performs a search. Requires Ollama server to be running with the embedding model.
    """
    print("--- Testing VectorDB Utilities (ChromaDB & Ollama Embeddings) ---")
    print(f"Ensure Ollama is running and model '{EMBEDDING_MODEL_NAME}' is available.")

    # Test embedding function directly
    print("\n--- Test 1: Get Ollama Embedding ---")
    sample_text_for_embedding = "This is a test sentence for Ollama bge-m3 embedding."
    embedding = get_ollama_embedding(sample_text_for_embedding)
    if embedding:
        print(f"Successfully got embedding for sample text. Length: {len(embedding)}. First 3 dims: {embedding[:3]}")
    else:
        print("Failed to get embedding for sample text. Check Ollama server and model.")

    # Test VectorDBManager
    print("\n--- Test 2: VectorDBManager Initialization, Adding Docs, Searching ---")
    # Use a temporary path for testing to avoid conflicts with a real DB
    test_chroma_path = os.path.join(os.path.dirname(__file__), 'chroma_db_test_data')
    test_collection_name = "test_rag_collection"

    try:
        # Initialize manager (will create db if not exists)
        db_manager = VectorDBManager(path=test_chroma_path, collection_name=test_collection_name)
        initial_count = db_manager.collection.count()
        print(f"Initial document count in '{test_collection_name}': {initial_count}")

        # Sample documents for testing
        docs_to_add = [
            "Information about Netze BW peak load windows (Hochlastzeitfenster) for 2024.",
            "Details on Netze BW network charges (Netzentgelte), including Arbeitspreis and Leistungspreis.",
            "General company overview of Netze BW GmbH, its role as a DNO in Baden-Württemberg."
        ]
        metadatas_to_add = [
            {"source_document_id": "netze_bw_doc_001", "category": "peak_load_windows"},
            {"source_document_id": "netze_bw_doc_001", "category": "network_charges"}, # Same doc_id, different aspect
            {"source_document_id": "netze_bw_doc_002", "category": "company_info"}
        ]
        ids_to_add = ["text_chunk_001", "text_chunk_002", "text_chunk_003"]

        # Check if these IDs already exist to make test idempotent for add
        existing_ids_in_test_collection = set(db_manager.collection.get(ids=ids_to_add)['ids'])
        if not existing_ids_in_test_collection.issuperset(set(ids_to_add)):
            print("Adding new documents to test collection...")
            add_success = db_manager.add_documents(docs_to_add, metadatas_to_add, ids_to_add)
            if add_success:
                print("Documents added successfully to test collection.")
            else:
                print("Failed to add documents to test collection.")
        else:
            print("Test documents already seem to exist in the test collection. Skipping add.")
        print(f"Document count after potential add: {db_manager.collection.count()}")

        # Perform a search
        if db_manager.collection.count() > 0:
            search_query = "What are the peak load window times for Netze BW?"
            search_results = db_manager.search_documents(search_query, n_results=2)
            if search_results:
                print(f"\nSearch results for query: '{search_query}'")
                for i in range(len(search_results['ids'])):
                    print(f"  Result {i+1}:")
                    print(f"    ID: {search_results['ids'][i]}")
                    print(f"    Distance: {search_results['distances'][i]:.4f}")
                    print(f"    Document: '{search_results['documents'][i][:100]}...' ")
                    print(f"    Metadata: {search_results['metadatas'][i]}")
            else:
                print("Search did not return results or failed.")
        else:
            print("Skipping search test as no documents are in the test collection.")

    except Exception as e_main:
        print(f"An error occurred during VectorDBManager testing: {e_main}")
        print("Ensure ChromaDB is installed ('pip install chromadb') and Ollama is running.")
    finally:
        # Cleanup: Delete the test database directory
        import shutil
        if os.path.exists(test_chroma_path):
            try:
                # Attempt to delete client/collection first if needed by Chroma version, then rmtree
                # For PersistentClient, removing the directory is usually enough.
                if 'db_manager' in locals() and db_manager.client:
                    # db_manager.client.delete_collection(test_collection_name) # If needed
                    # db_manager.client.reset() # Resets the entire database, good for cleanup
                    pass # client cleanup if any specific method is needed
                shutil.rmtree(test_chroma_path)
                print(f"\nCleaned up test ChromaDB directory: {test_chroma_path}")
            except Exception as e_cleanup:
                print(f"Error cleaning up test ChromaDB directory {test_chroma_path}: {e_cleanup}")

    print("\nVectorDB utilities testing finished.")
```
