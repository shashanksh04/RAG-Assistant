import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from loguru import logger

from app.core.config import settings

class RunnableRetriever(BaseRetriever):
    """Wraps a Runnable (chain) to conform to the BaseRetriever interface."""
    runnable: Any
    
    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        return self.runnable.invoke(query)

class RAGService:
    def __init__(self):
        # Initialize Embeddings
        logger.info("Initializing RAG Service...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize Vector DB
        # settings.BASE_DIR is backend/app
        backend_root = settings.BASE_DIR.parent
        db_path_setting = Path(settings.CHROMA_DB_PATH)
        
        if db_path_setting.is_absolute():
            vector_db_path = str(db_path_setting)
        else:
            if len(db_path_setting.parts) > 0 and db_path_setting.parts[0] == 'backend' and backend_root.name == 'backend':
                db_path_setting = Path(*db_path_setting.parts[1:])
            vector_db_path = str(backend_root / db_path_setting)
            
        logger.info(f"Connecting to Vector DB at {vector_db_path}")
        self.vector_db = Chroma(
            persist_directory=vector_db_path,
            embedding_function=self.embeddings,
            collection_name="rag_documents"
        )
        
        # Initialize LLM
        logger.info(f"Initializing LLM: {settings.LLM_MODEL} at {settings.OLLAMA_BASE_URL}")
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=0.1
        )
        
        # Initialize Re-ranking Model (Cross-Encoder)
        logger.info("Initializing Cross-Encoder for re-ranking...")
        self.cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # Pre-compile prompts to save time per request
        self._setup_prompts()
        logger.info("RAG Service initialized successfully.")

    def _setup_prompts(self):
        """Initialize prompts for the RAG pipeline."""
        
        # 1. Contextualize question prompt
        # This chain reformulates the question based on chat history
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        self.contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # 2. Answer question prompt
        # This chain answers the question using retrieved context
        system_prompt = (
            "You are a helpful assistant for a knowledge base. "
            "Use the following pieces of retrieved context to answer "
            "the question. Think step by step to reason through the "
            "information provided. If you don't know the answer, say that you "
            "don't have enough information. Use three sentences maximum "
            "and keep the answer concise.\n\n"
            "Context:\n{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        self.question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # 3. HyDE Prompt
        hyde_system_prompt = (
            "You are an expert at generating hypothetical documents. "
            "Given a question, generate a concise paragraph that would answer the question. "
            "Do not include any explanations, just the hypothetical answer content."
        )
        self.hyde_prompt = ChatPromptTemplate.from_messages([
            ("system", hyde_system_prompt),
            ("human", "{input}"),
        ])

        # 4. Answer Validation Prompt
        validation_system_prompt = (
            "You are a fact-checking assistant. Given the following context and an answer, "
            "determine if the answer is supported by the context. "
            "Respond with only 'YES' or 'NO'."
        )
        self.validation_prompt = ChatPromptTemplate.from_messages([
            ("system", validation_system_prompt),
            ("human", "Context:\n{context}\n\nAnswer:\n{answer}"),
        ])

        # 5. Simple QA Prompt (No RAG)
        simple_system_prompt = (
            "You are a helpful assistant. Answer the user's question to the best of your ability."
        )
        self.simple_prompt = ChatPromptTemplate.from_messages([
            ("system", simple_system_prompt),
            ("human", "{input}"),
        ])
        self.simple_chain = self.simple_prompt | self.llm | StrOutputParser()

    def _get_rag_chain(self, filters: Optional[Dict[str, Any]] = None, enable_query_expansion: bool = False, enable_hyde: bool = False):
        """
        Constructs the RAG chain dynamically with optional filters and re-ranking.
        """
        # 1. Configure Base Retriever
        # Fetch more documents initially (fetch_k=20) to allow for re-ranking
        search_kwargs = {"k": 10, "fetch_k": 20}
        if filters:
            search_kwargs["filter"] = filters
            
        base_retriever = self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )
        
        # 2. Apply Advanced Retrieval Strategies
        if enable_hyde:
            logger.info("Enabling HyDE (Hypothetical Document Embeddings) retrieval.")
            # Chain: Generate HyDE Doc -> Retrieve using HyDE Doc
            hyde_chain = (
                self.hyde_prompt 
                | self.llm 
                | StrOutputParser() 
                | base_retriever
            )
            # Wrap as a retriever so it can be used in the next steps
            base_retriever = RunnableRetriever(runnable=hyde_chain)
            
        elif enable_query_expansion:
            logger.info("Enabling Query Expansion retrieval.")
            base_retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=self.llm
            )

        # 2. Configure Re-ranker
        # Select top 5 most relevant documents from the retrieved set
        compressor = CrossEncoderReranker(model=self.cross_encoder, top_n=5)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=base_retriever
        )
        
        # 3. Create History-Aware Retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm, compression_retriever, self.contextualize_q_prompt
        )
        
        # Combine into final RAG chain
        return create_retrieval_chain(history_aware_retriever, self.question_answer_chain)

    def _calculate_confidence(self, docs) -> float:
        """Calculates confidence score based on re-ranking logits."""
        if not docs:
            return 0.0
        # Extract relevance scores (logits) and apply sigmoid to normalize to 0-1
        scores = [doc.metadata.get("relevance_score", 0.0) for doc in docs]
        # Average probability
        avg_score = sum(1 / (1 + math.exp(-s)) for s in scores) / len(scores)
        return round(avg_score, 2)

    async def validate_answer(self, answer: str, context: List[Document]) -> bool:
        """
        Validates if the generated answer is grounded in the retrieved context.
        """
        if not context:
            return False
            
        context_text = "\n\n".join([doc.page_content for doc in context])
        # Simple chain for validation
        chain = self.validation_prompt | self.llm | StrOutputParser()
        
        try:
            response = await chain.ainvoke({
                "answer": answer,
                "context": context_text
            })
            return "yes" in response.strip().lower()
        except Exception as e:
            logger.warning(f"Answer validation failed: {e}")
            return False

    async def generate_answer(self, query: str, chat_history: List[Dict[str, str]] = [], filters: Optional[Dict[str, Any]] = None, enable_query_expansion: bool = False, enable_hyde: bool = False, use_rag: bool = True) -> Dict[str, Any]:
        """
        Generates an answer using RAG.
        
        Args:
            query: The user's question.
            chat_history: List of dicts with 'role' (user/assistant) and 'content'.
            filters: Optional metadata filters (e.g., {"source": "doc.pdf"}).
            enable_query_expansion: Enable MultiQueryRetriever.
            enable_hyde: Enable HyDE retrieval.
            use_rag: Whether to use retrieval or direct LLM generation.
            
        Returns:
            Dictionary containing answer, sources, and confidence (placeholder).
        """
        logger.info(f"Generating answer for query: {query}")
        
        # Convert chat history to LangChain format
        lc_history = []
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_history.append(AIMessage(content=content))
        
        try:
            if not use_rag:
                logger.info(f"Generating answer without RAG for query: {query}")
                answer = await self.simple_chain.ainvoke({"input": query})
                return {
                    "answer": answer,
                    "sources": [],
                    "confidence": 0.0,
                    "is_grounded": False,
                    "contexts": []
                }

            # Get chain configured with filters
            rag_chain = self._get_rag_chain(filters, enable_query_expansion, enable_hyde)
            
            # Invoke chain
            response = await rag_chain.ainvoke({
                "input": query,
                "chat_history": lc_history
            })
            
            answer = response["answer"]
            context_docs = response["context"]
            
            # Extract sources
            sources = []
            full_contexts = []
            for doc in context_docs:
                source_name = Path(doc.metadata.get("source", "unknown")).name
                page_num = doc.metadata.get("page", 0)
                sources.append({
                    "source": source_name,
                    "page": page_num,
                    "citation": f"{source_name} (p. {page_num})",
                    "snippet": doc.page_content[:200] + "...",
                    "relevance_score": doc.metadata.get("relevance_score", 0.0) # Added by re-ranker if available
                })
                full_contexts.append(doc.page_content)
            
            confidence = self._calculate_confidence(context_docs)
            
            # Validate Answer
            is_grounded = await self.validate_answer(answer, context_docs)
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "is_grounded": is_grounded,
                "contexts": full_contexts
            }
            
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            if "Connect call failed" in str(e) or "Cannot connect to host" in str(e):
                raise RuntimeError(
                    f"Connection to Ollama failed at {settings.OLLAMA_BASE_URL}. "
                    "Ensure Ollama is running and accessible."
                )
            raise RuntimeError(f"RAG generation failed: {e}")

    async def generate_answer_stream(self, query: str, chat_history: List[Dict[str, str]] = [], filters: Optional[Dict[str, Any]] = None, enable_query_expansion: bool = False, enable_hyde: bool = False) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generates an answer using RAG, streaming the response tokens.
        Yields dictionaries with keys 'type' ('token' or 'sources') and 'data'.
        """
        logger.info(f"Streaming answer for query: {query}")
        
        lc_history = []
        for msg in chat_history:
            if msg.get("role") == "user":
                lc_history.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "assistant":
                lc_history.append(AIMessage(content=msg.get("content")))

        try:
            rag_chain = self._get_rag_chain(filters, enable_query_expansion, enable_hyde)
            
            # astream yields chunks of the output dictionary
            async for chunk in rag_chain.astream({
                "input": query,
                "chat_history": lc_history
            }):
                if "context" in chunk:
                    sources = []
                    for doc in chunk["context"]:
                        sources.append({
                            "source": doc.metadata.get("source", "unknown"),
                            "page": doc.metadata.get("page", 0),
                            "snippet": doc.page_content[:200] + "..."
                        })
                    yield {"type": "sources", "data": sources}
                
                if "answer" in chunk:
                    yield {"type": "token", "data": chunk["answer"]}
                    
        except Exception as e:
            logger.error(f"RAG streaming failed: {e}")
            yield {"type": "error", "data": str(e)}