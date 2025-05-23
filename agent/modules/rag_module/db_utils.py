# agent/modules/rag_module/db_utils.py
"""
SQLite database utilities for the RAG module.

Handles creation of tables, insertion of data, and querying of data for
the structured information part of the RAG system.
The database will store detailed records linked to text chunks whose embeddings
are stored in a vector database.
"""

import sqlite3
from typing import List, Dict, Any, Tuple, Optional
import os

DB_DIRECTORY = os.path.join(os.path.dirname(__file__), 'database') # Store DB in a 'database' subfolder
DB_NAME = os.path.join(DB_DIRECTORY, 'rag_sqlite.db')

def init_db(db_path: str = DB_NAME) -> None:
    """
    Initializes the SQLite database and creates tables if they don't exist.

    The database schema includes:
    - `knowledge_sources`: Stores the original text chunks and their source document IDs.
    - `hlzf_data`: Stores peak load window data (Hochlastzeitfenster).
    - `netzentgelte_data`: Stores network charge data (Netzentgelte).

    Args:
        db_path (str): The path to the SQLite database file.
    """
    # Ensure the database directory exists
    os.makedirs(DB_DIRECTORY, exist_ok=True)

    print(f"Initializing SQLite database at: {db_path}")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Table for original text sources and their IDs (linking to vector DB)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_sources (
            source_document_id TEXT PRIMARY KEY,
            original_text_chunk TEXT NOT NULL,
            source_description TEXT
        )
        """)

        # Table for Hochlastzeitfenster (Peak Load Windows) data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hlzf_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dno_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            timestamp INTEGER, 
            window_type TEXT NOT NULL, 
            time_value TEXT,
            source_document_id TEXT NOT NULL,
            FOREIGN KEY (source_document_id) REFERENCES knowledge_sources (source_document_id)
        )
        """)

        # Table for Netzentgelte (Network Charges) data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS netzentgelte_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dno_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            timestamp INTEGER,
            voltage_level TEXT NOT NULL,
            charge_type TEXT NOT NULL, 
            value REAL NOT NULL,
            unit TEXT,
            source_document_id TEXT NOT NULL,
            FOREIGN KEY (source_document_id) REFERENCES knowledge_sources (source_document_id)
        )
        """)
        conn.commit()
    print("Database initialized successfully.")

def add_knowledge_source(source_document_id: str, original_text_chunk: str, source_description: Optional[str] = None, db_path: str = DB_NAME) -> None:
    """
    Adds a new knowledge source text chunk to the database.

    Args:
        source_document_id (str): The unique ID for this text chunk (will be used in Vector DB).
        original_text_chunk (str): The actual text content that will be embedded.
        source_description (Optional[str]): A brief description of the source (e.g., document name, URL).
        db_path (str): Path to the SQLite database file.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO knowledge_sources (source_document_id, original_text_chunk, source_description) VALUES (?, ?, ?)",
                           (source_document_id, original_text_chunk, source_description))
            conn.commit()
            # print(f"Added knowledge source: {source_document_id}") # Verbose
        except sqlite3.IntegrityError:
            print(f"Warning: Knowledge source with ID '{source_document_id}' already exists. Not adding again.")

def add_hlzf_entry(dno_name: str, year: int, timestamp: int, window_type: str, time_value: Optional[str], source_document_id: str, db_path: str = DB_NAME) -> None:
    """
    Adds a new entry to the hlzf_data table.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hlzf_data (dno_name, year, timestamp, window_type, time_value, source_document_id) VALUES (?, ?, ?, ?, ?, ?)",
                       (dno_name, year, timestamp, window_type, time_value, source_document_id))
        conn.commit()

def add_netzentgelte_entry(dno_name: str, year: int, timestamp: int, voltage_level: str, charge_type: str, value: float, unit: Optional[str], source_document_id: str, db_path: str = DB_NAME) -> None:
    """
    Adds a new entry to the netzentgelte_data table.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO netzentgelte_data (dno_name, year, timestamp, voltage_level, charge_type, value, unit, source_document_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (dno_name, year, timestamp, voltage_level, charge_type, value, unit, source_document_id))
        conn.commit()

def get_data_by_source_id(source_document_id: str, db_path: str = DB_NAME) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves all data entries from hlzf_data and netzentgelte_data associated with a given source_document_id.

    Args:
        source_document_id (str): The ID of the source document.
        db_path (str): Path to the SQLite database file.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary with keys 'hlzf_data' and 'netzentgelte_data',
                                         each containing a list of rows (as dicts) from the respective tables.
    """
    results: Dict[str, List[Dict[str, Any]]] = {
        "hlzf_data": [],
        "netzentgelte_data": []
    }
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()

        # Fetch from hlzf_data
        cursor.execute("SELECT * FROM hlzf_data WHERE source_document_id = ?", (source_document_id,))
        for row in cursor.fetchall():
            results["hlzf_data"].append(dict(row))

        # Fetch from netzentgelte_data
        cursor.execute("SELECT * FROM netzentgelte_data WHERE source_document_id = ?", (source_document_id,))
        for row in cursor.fetchall():
            results["netzentgelte_data"].append(dict(row))
            
    return results

def get_knowledge_source_text(source_document_id: str, db_path: str = DB_NAME) -> Optional[str]:
    """
    Retrieves the original text chunk for a given source_document_id.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT original_text_chunk FROM knowledge_sources WHERE source_document_id = ?", (source_document_id,))
        row = cursor.fetchone()
        return row['original_text_chunk'] if row else None

if __name__ == '__main__':
    """
    Example usage: Initializes the database and adds some sample data.
    This block can be run to set up the initial DB schema.
    """
    print(f"Running db_utils.py directly to initialize database at {DB_NAME}...")
    init_db() # Ensure tables are created
    print("--- Database Initialization Example --- (Should only create tables if not exist)")

    # Example of adding data (idempotent for knowledge_sources due to check)
    sample_source_id = "netze_bw_doc_001"
    sample_text = "Information about Netze BW peak load windows (Hochlastzeitfenster) and network charges (Netzentgelte) for the year 2024."
    add_knowledge_source(sample_source_id, sample_text, "Netze BW Tariff Document 2024 Excerpt")
    add_knowledge_source(sample_source_id, sample_text, "Netze BW Tariff Document 2024 Excerpt") # Test duplicate add

    # Clear existing data for these specific source_document_ids before adding new test data
    # to make this __main__ block more idempotent for hlzf and netzentgelte if run multiple times.
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        print(f"Deleting existing hlzf_data & netzentgelte_data for source_id: {sample_source_id} before adding samples...")
        cursor.execute("DELETE FROM hlzf_data WHERE source_document_id = ?", (sample_source_id,))
        cursor.execute("DELETE FROM netzentgelte_data WHERE source_document_id = ?", (sample_source_id,))
        conn.commit()

    print(f"Adding sample entries for source_id: {sample_source_id}")
    add_hlzf_entry("netze-bw", 2024, 1745056892, "Winter_1_Start", "06:00:00", sample_source_id)
    add_hlzf_entry("netze-bw", 2024, 1745056892, "Winter_1_Ende", "22:00:00", sample_source_id)
    add_hlzf_entry("netze-bw", 2024, 1745056892, "Sommer_1_Start", None, sample_source_id) # Example with NULL time_value

    add_netzentgelte_entry("netze-bw", 2024, 1745056892, "hs", "Leistung", 58.21, "EUR/kW", sample_source_id)
    add_netzentgelte_entry("netze-bw", 2024, 1745056892, "hs", "Arbeit", 1.26, "ct/kWh", sample_source_id)
    add_netzentgelte_entry("netze-bw", 2024, 1745056892, "ms/ns", "Leistung", 142.11, "EUR/kW", sample_source_id)
    print("Sample data added.")

    print("\n--- Retrieving data for source_id: netze_bw_doc_001 ---")
    retrieved_data = get_data_by_source_id(sample_source_id)
    print(f"HLZF Data: {retrieved_data['hlzf_data']}")
    print(f"Netzentgelte Data: {retrieved_data['netzentgelte_data']}")

    print("\n--- Retrieving original text for source_id: netze_bw_doc_001 ---")
    original_text = get_knowledge_source_text(sample_source_id)
    print(f"Original Text: {original_text}")

    print("\n--- Retrieving data for non-existent source_id: fake_id ---")
    retrieved_data_fake = get_data_by_source_id("fake_id")
    print(f"HLZF Data (fake): {retrieved_data_fake['hlzf_data']}")
    print(f"Netzentgelte Data (fake): {retrieved_data_fake['netzentgelte_data']}")
    original_text_fake = get_knowledge_source_text("fake_id")
    print(f"Original Text (fake): {original_text_fake}")

    print("\ndb_utils.py example execution finished.")
```
