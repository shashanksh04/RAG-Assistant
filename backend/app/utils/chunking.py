from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentChunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def semantic_chunking(self, text: str):
        """Split by semantic boundaries"""
        return self.splitter.split_text(text)