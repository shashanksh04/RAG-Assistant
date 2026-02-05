import pypdf
from typing import Any, Dict

class DocumentParser:
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text preserving structure"""
        text = ""
        try:
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() or "" + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
        return text

    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract title, author, dates"""
        try:
            reader = pypdf.PdfReader(pdf_path)
            info = reader.metadata
            return {
                "title": info.title if info and info.title else "Unknown",
                "author": info.author if info and info.author else "Unknown",
                "pages": len(reader.pages)
            }
        except Exception:
            return {"title": "Unknown", "author": "Unknown", "pages": 0}