import os
import asyncio
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional, List
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.services.stt_service import WhisperSTTService
from app.api.models import AskRequest, AnswerResponse, TranscriptionResponse, DocumentInfo

router = APIRouter()

# Initialize Services
ingestion_service = IngestionService()
rag_service = RAGService()
stt_service = WhisperSTTService()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Upload PDF to vector database"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        result = await ingestion_service.ingest_document(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio file"""
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            
        result = await asyncio.to_thread(stt_service.transcribe_audio, tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: AskRequest):
    """Ask a question based on ingested documents"""
    try:
        response = await rag_service.generate_answer(
            query=request.query,
            enable_query_expansion=request.enable_query_expansion,
            enable_hyde=request.enable_hyde
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask-audio", response_model=AnswerResponse)
async def ask_from_audio(file: UploadFile = File(...)):
    """Transcribe audio and ask question based on ingested documents"""
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            
        try:
            # Transcribe
            transcription_result = await asyncio.to_thread(stt_service.transcribe_audio, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        # Handle transcription result
        if isinstance(transcription_result, dict):
            query_text = transcription_result.get("text", "")
        else:
            query_text = getattr(transcription_result, "text", "")
            
        if not query_text.strip():
             raise HTTPException(status_code=400, detail="Could not transcribe audio or audio was empty")

        # Ask RAG
        response = await rag_service.generate_answer(
            query=query_text
        )
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all ingested documents"""
    return ingestion_service.list_documents()

@router.get("/health")
async def health_check():
    return {"status": "ok"}