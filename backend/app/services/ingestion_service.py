import os
import shutil
import uuid
import tempfile
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from fastapi import UploadFile
from loguru import logger
from app.utils.pdf_parser import DocumentParser
from app.utils.chunking import DocumentChunker
from app.core.config import settings

class IngestionService:
    def __init__(self):
        # Ensure data directories exist
        # Align path logic with RAGService
        backend_root = settings.BASE_DIR.parent
        db_path_setting = Path(settings.CHROMA_DB_PATH)
        
        if db_path_setting.is_absolute():
            self.db_path = str(db_path_setting)
        else:
            if len(db_path_setting.parts) > 0 and db_path_setting.parts[0] == 'backend' and backend_root.name == 'backend':
                db_path_setting = Path(*db_path_setting.parts[1:])
            self.db_path = str(backend_root / db_path_setting)
            
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="rag_documents",
            embedding_function=self.embedding_fn
        )
        
        self.parser = DocumentParser()
        self.chunker = DocumentChunker()

    async def ingest_document(self, file: UploadFile):
        logger.info(f"Starting ingestion for file: {file.filename}")
        # Use tempfile to handle upload safely and avoid path/permission issues
        suffix = Path(file.filename).suffix if file.filename else ".pdf"
        
        # Create temp file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
        
        try:
            # Save uploaded file content
            # Using await file.read() is safer for FastAPI UploadFile than copyfileobj on file.file
            content = await file.read()
            with open(tmp_path, "wb") as f:
                f.write(content)
            
            logger.info(f"File saved to temp path: {tmp_path}, size: {len(content)} bytes")

            # Extract text and metadata
            text = self.parser.extract_text_from_pdf(tmp_path)
            if not text.strip():
                logger.error("Extracted text is empty")
                raise ValueError("Could not extract text from PDF (file might be empty or scanned image)")
                
            metadata = self.parser.extract_metadata(tmp_path)
            safe_filename = file.filename or f"upload_{uuid.uuid4()}{suffix}"
            metadata["filename"] = safe_filename
            metadata["source"] = safe_filename
            
            # Chunk text
            chunks = self.chunker.semantic_chunking(text)
            logger.info(f"Generated {len(chunks)} chunks")
            
            # Prepare for Vector DB
            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [{"chunk_index": i, **metadata} for i in range(len(chunks))]
            
            # Add to ChromaDB
            self.collection.add(documents=chunks, metadatas=metadatas, ids=ids)
            logger.info("Chunks added to ChromaDB")
            
            return {"filename": safe_filename, "chunks_ingested": len(chunks), "status": "success"}
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            raise e
            
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def list_documents(self):
        """List all ingested documents."""
        try:
            # Fetch all metadata to find unique sources
            result = self.collection.get(include=['metadatas'])
            metadatas = result.get('metadatas', []) or []
            
            unique_files = {}
            for meta in metadatas:
                source = meta.get('source', 'Unknown')
                if source not in unique_files:
                    unique_files[source] = {
                        "filename": source,
                        "chunk_count": 0,
                        "total_pages": meta.get("pages", 0),
                        "title": meta.get("title", "Unknown"),
                        "author": meta.get("author", "Unknown")
                    }
                unique_files[source]["chunk_count"] += 1
                
            return list(unique_files.values())
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []