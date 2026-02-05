import sys
import os
from pathlib import Path
import argparse
import hashlib
from tqdm import tqdm

# Add the backend directory to sys.path to allow imports from app
# This resolves to the 'backend' directory
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from loguru import logger

from app.core.config import settings
from app.utils.pdf_parser import DocumentParser
from app.utils.chunking import DocumentChunker

# --- Helper Functions ---

def _generate_chunk_ids(chunks: list[Document]) -> list[str]:
    """Generates deterministic IDs for document chunks."""
    return [
        hashlib.sha256(
            f"{chunk.metadata['source']}-{chunk.metadata['page']}-{chunk.page_content}".encode()
        ).hexdigest()
        for chunk in chunks
    ]

def get_vector_db_client() -> Chroma:
    """Initializes and returns the ChromaDB client."""
    backend_root = backend_path
    if Path(settings.CHROMA_DB_PATH).is_absolute():
        vector_db_path = settings.CHROMA_DB_PATH
    else:
        db_path_setting = Path(settings.CHROMA_DB_PATH)
        if len(db_path_setting.parts) > 0 and db_path_setting.parts[0] == 'backend' and backend_root.name == 'backend':
            db_path_setting = Path(*db_path_setting.parts[1:])
        vector_db_path = str(backend_root / db_path_setting)

    logger.info("Initializing embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    logger.info(f"Initializing Vector DB at {vector_db_path}...")
    return Chroma(
        persist_directory=vector_db_path,
        embedding_function=embeddings,
        collection_name="rag_documents"
    )

# --- Core Logic Functions ---

def ingest_logic(files_to_process: list[Path], vector_db: Chroma, reingest: bool):
    """Handles the ingestion of documents."""
    parser = DocumentParser()
    chunker = DocumentChunker()

    logger.info(f"Processing {len(files_to_process)} file(s)...")
    for pdf_file in tqdm(files_to_process, desc="Ingesting Documents"):
        try:
            if reingest:
                logger.info(f"Re-ingesting: Deleting existing entries for {pdf_file.name}...")
                delete_logic(pdf_file.name, vector_db)

            logger.info(f"Processing {pdf_file.name}...")
            documents = parser.parse_pdf(pdf_file)
            chunks = chunker.chunk_documents(documents)
            
            if chunks:
                chunk_ids = _generate_chunk_ids(chunks)
                vector_db.add_documents(documents=chunks, ids=chunk_ids)
                if hasattr(vector_db, "persist"):
                    vector_db.persist()
                logger.info(f"Successfully ingested {len(chunks)} chunks from {pdf_file.name}")
            else:
                logger.warning(f"No chunks created for {pdf_file.name}")

        except Exception as e:
            logger.error(f"Failed to ingest {pdf_file.name}: {e}")

def delete_logic(filename: str, vector_db: Chroma):
    """Handles the deletion of a document."""
    if not filename:
        logger.error("A filename must be provided to delete.")
        return

    try:
        ids_to_delete = vector_db.get(where={"source": filename})['ids']
        if ids_to_delete:
            logger.info(f"Found {len(ids_to_delete)} chunks to delete for {filename}.")
            vector_db.delete(ids=ids_to_delete)
            if hasattr(vector_db, "persist"):
                vector_db.persist()
            logger.success(f"Successfully deleted document: {filename}")
        else:
            logger.warning(f"No document found with filename: {filename}")
    except Exception as e:
        logger.error(f"Failed to delete {filename}: {e}")

def list_logic(vector_db: Chroma):
    """Lists all ingested documents."""
    try:
        all_docs = vector_db.get()
        if not all_docs or not all_docs['ids']:
            logger.info("No documents found in the vector store.")
            return

        sources = sorted(list(set(meta['source'] for meta in all_docs['metadatas'] if 'source' in meta)))
        
        logger.info(f"Found {len(sources)} ingested documents:")
        for source in sources:
            print(f"- {source}")
            
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Document Ingestion and Management Script for RAG Assistant")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the vector store.")
    ingest_parser.add_argument("--file", type=str, help="Path to a specific PDF file to ingest.")
    ingest_parser.add_argument("--reingest", action="store_true", help="Force re-ingestion by deleting the document first.")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a document from the vector store.")
    delete_parser.add_argument("--file", type=str, required=True, help="Filename of the document to delete (e.g., 'my_doc.pdf').")

    # List command
    subparsers.add_parser("list", help="List all ingested documents.")

    args = parser.parse_args()

    vector_db = get_vector_db_client()
    docs_path = backend_path / "data" / "documents"

    if args.command == "ingest":
        files_to_process = []
        if args.file:
            file_path = Path(args.file)
            if file_path.exists():
                files_to_process.append(file_path)
            else:
                logger.error(f"Specified file does not exist: {args.file}")
                return
        else:
            if not docs_path.exists():
                logger.error(f"Documents directory does not exist: {docs_path}")
                return
            files_to_process = list(docs_path.glob("*.pdf"))

        if not files_to_process:
            logger.warning("No PDF files found to ingest.")
            return
            
        ingest_logic(files_to_process, vector_db, args.reingest)

    elif args.command == "delete":
        delete_logic(args.file, vector_db)
        
    elif args.command == "list":
        list_logic(vector_db)

    logger.info("Script execution finished.")

if __name__ == "__main__":
    main()