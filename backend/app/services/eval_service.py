from typing import List, Dict, Any
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger

from app.core.config import settings

class RAGEvaluator:
    def __init__(self):
        logger.info("Initializing RAG Evaluator with local LLM...")
        # RAGAS uses these for calculating metrics
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=0  # Deterministic for evaluation
        )
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def evaluate_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluates RAG results using RAGAS metrics.
        
        Args:
            test_results: List of dicts containing:
                - question: str
                - answer: str
                - contexts: List[str] (retrieved chunks)
                - ground_truth: str
                
        Returns:
            Dictionary of metric scores.
        """
        if not test_results:
            logger.warning("No test results to evaluate.")
            return {}

        # Prepare data for RAGAS
        data = {
            "question": [item["question"] for item in test_results],
            "answer": [item["answer"] for item in test_results],
            "contexts": [item["contexts"] for item in test_results],
            "ground_truth": [item["ground_truth"] for item in test_results],
        }
        
        dataset = Dataset.from_dict(data)
        
        logger.info(f"Starting evaluation on {len(test_results)} samples...")
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=self.llm,
                embeddings=self.embeddings
            )
            
            logger.info(f"Evaluation complete. Metrics: {results}")
            return results
            
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            raise e

    def save_report(self, results: Dict[str, float], output_path: str = "evaluation_report.csv"):
        # RAGAS results object behaves like a dict but might need conversion
        df = pd.DataFrame([dict(results)])
        df.to_csv(output_path, index=False)
        logger.info(f"Report saved to {output_path}")