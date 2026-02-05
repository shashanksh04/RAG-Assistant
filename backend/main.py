import json
import shutil
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.rag_service import RAGService
from app.services.stt_service import WhisperSTTService

app = FastAPI()

# Configure CORS to allow requests from your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Default Vite port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
# These will load models upon startup
rag_service = RAGService()
stt_service = WhisperSTTService()

# This is the health check endpoint you requested
@app.get("/")
async def root():
    return {"status": "online"}

# --- API V1 Router ---
api_router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    chat_history: List[Dict[str, str]] = []
    use_rag: bool = True
    filters: Optional[Dict[str, Any]] = None

@api_router.get("/")
async def api_v1_root():
    return {"status": "online", "version": "v1"}

@api_router.post("/ask")
async def ask(request: ChatRequest):
    try:
        response = await rag_service.generate_answer(
            query=request.query,
            chat_history=request.chat_history,
            use_rag=request.use_rag,
            filters=request.filters
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ask-audio")
async def ask_audio(
    file: UploadFile = File(...),
    chat_history: str = Form("[]"),
    use_rag: bool = Form(True)
):
    try:
        # 1. Save uploaded file temporarily
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Transcribe Audio
        transcription = stt_service.transcribe_audio(temp_filename)
        query_text = transcription["text"]
        
        # 3. Generate Answer using RAG
        # Parse chat_history from JSON string
        history_list = json.loads(chat_history)
        
        response = await rag_service.generate_answer(
            query=query_text,
            chat_history=history_list,
            use_rag=use_rag
        )
        
        # Return combined response
        return {
            "query": query_text,
            "transcription_details": transcription,
            **response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

app.include_router(api_router, prefix="/api/v1")