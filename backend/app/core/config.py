import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG Speech Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # LLM Configuration (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"
    
    # STT Configuration
    WHISPER_MODEL_SIZE: str = "base"
    
    # Database & Storage
    CHROMA_DB_PATH: str = "backend/data/vector_db"
    
    # Base Path (backend/app)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()