# RAG-Based Speech-to-Text Knowledge Assistant

This project implements a Retrieval-Augmented Generation (RAG) system that converts speech to text and answers questions using private documents.

## Prerequisites

1.  **Python 3.10+**
2.  **Node.js & npm**
3.  **Ollama**: Download from [ollama.com](https://ollama.com/).
4.  **FFmpeg**: Required for Whisper audio processing.
    *   Windows: `winget install ffmpeg`
    *   Mac: `brew install ffmpeg`
    *   Linux: `sudo apt install ffmpeg`

## Setup Guide

### 1. Model Setup
Ensure Ollama is running and pull the model configured in `backend/.env` (default is `deepseek-r1:8b`):
```bash
ollama pull deepseek-r1:8b
```

### 2. Backend Setup
Navigate to the `backend` directory:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the server:
```bash
uvicorn app.main:app --reload
```

### 3. Frontend Setup
Navigate to the `frontend` directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Run the development server:
```bash
npm run dev
```

## Usage

1.  **Ingest**: Go to "Manage Documents" and upload PDF files.
2.  **Chat**: Go to "Chat Assistant" to ask questions via text or voice.