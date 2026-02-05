import sys
import asyncio
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from app.services.rag_service import RAGService
from app.services.eval_service import RAGEvaluator
from loguru import logger

# Sample Test Data (Ground Truth)
# TODO: Replace these with questions relevant to your ingested documents
TEST_DATASET = [
    {
        "question": "What is the purpose of this project?",
        "ground_truth": "To build a RAG-based speech-to-text knowledge assistant that answers questions from documents."
    },
    {
        "question": "Which libraries are used for the backend?",
        "ground_truth": "FastAPI, LangChain, ChromaDB, and Whisper are used for the backend."
    },
    {
        "question": "Hello",
        "ground_truth": "Hello! I am ready to answer questions about your documents."
    }
]

async def evaluate_scenario(rag_service, evaluator, dataset, use_rag=True):
    scenario_name = "With RAG" if use_rag else "Without RAG"
    logger.info(f"Running evaluation for scenario: {scenario_name}")
    
    results_for_eval = []
    
    for item in dataset:
        query = item["question"]
        ground_truth = item["ground_truth"]
        
        try:
            # Get answer
            response = await rag_service.generate_answer(query, use_rag=use_rag)
            
            answer = response["answer"]
            contexts = response.get("contexts", [])
            
            # For No-RAG, contexts are empty, which affects RAGAS metrics like faithfulness/context_recall
            # We include them anyway to see the contrast (expecting 0s)
            
            results_for_eval.append({
                "question": query,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth
            })
            
        except Exception as e:
            logger.error(f"Failed to generate answer for '{query}': {e}")
            
    if not results_for_eval:
        return None

    logger.info(f"Calculating metrics for {scenario_name}...")
    ragas_result = evaluator.evaluate_results(results_for_eval)
    
    # Convert to pandas DF for easier handling
    df = ragas_result.to_pandas()
    df["scenario"] = scenario_name
    return df

def generate_visualizations(combined_df, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Melt dataframe for seaborn
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    # Filter only existing columns
    metrics = [m for m in metrics if m in combined_df.columns]
    
    melted_df = combined_df.melt(
        id_vars=["scenario"], 
        value_vars=metrics, 
        var_name="metric", 
        value_name="score"
    )
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=melted_df, x="metric", y="score", hue="scenario", palette="viridis")
    plt.title("RAG vs No-RAG Performance Comparison")
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plot_path = output_dir / "rag_comparison_plot.png"
    plt.savefig(plot_path)
    logger.info(f"Saved comparison plot to {plot_path}")

async def run_evaluation():
    rag_service = RAGService()
    evaluator = RAGEvaluator()
    
    # 1. Evaluate With RAG
    df_rag = await evaluate_scenario(rag_service, evaluator, TEST_DATASET, use_rag=True)
    
    # 2. Evaluate Without RAG
    df_no_rag = await evaluate_scenario(rag_service, evaluator, TEST_DATASET, use_rag=False)
    
    if df_rag is not None and df_no_rag is not None:
        combined_df = pd.concat([df_rag, df_no_rag], ignore_index=True)
        
        # Save raw data
        docs_dir = backend_path.parent / "docs"
        combined_df.to_csv(docs_dir / "evaluation_results.csv", index=False)
        
        # Generate Visualizations
        generate_visualizations(combined_df, docs_dir)
        
        # Print Summary
        summary = combined_df.groupby("scenario")[["faithfulness", "answer_relevancy"]].mean()
        print("\n=== Evaluation Summary ===")
        print(summary)


if __name__ == "__main__":
    asyncio.run(run_evaluation())