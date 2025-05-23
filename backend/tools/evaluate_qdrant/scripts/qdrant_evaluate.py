import argparse
import yaml
from pathlib import Path
from dotenv import load_dotenv
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import jsonlines
from typing import List, Dict, Any
import os
from bert_score import BERTScorer
from sklearn.metrics import ndcg_score
import json
from tqdm import tqdm
from keybert import KeyBERT
from utils import stop_words, instructional_stop_words
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch


class Evaluator:
    def __init__(self, qdrant_collection ="ws1-test", extract_kw=False, reranking=True, qdrant_limit=5):
        logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("QdrantQuery")

        self.config_path = "tools/evaluate_qdrant/config/config.yaml"
        self.qdrant_config = self.load_config()

        print(self.qdrant_config)

        self.kw_model = KeyBERT()
        self.tokenizer = AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.model = AutoModelForSequenceClassification.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.qdrant_model = SentenceTransformer(self.qdrant_config["qdrant"]["embedding_model"])
        self.scorer = BERTScorer(lang="en")

        self.qa_json_path = "tools/evaluate_qdrant/data/qa_datasets/generated_questions_farmer_persona.jsonl"

        self.qdrant_url = self.qdrant_config["qdrant"]["qdrant_url"]
        self.qdrant_collection = qdrant_collection
        

        self.qa_pairs = self.load_qa_pairs()
        self.extract_kw = extract_kw
        self.reranking = reranking
        self.qdrant_limit = qdrant_limit

        self.client = self.connect_to_qdrant(self.qdrant_config)

        # Uncomment for debugging to clear collection
        #clear_collection(client, args.collection)   

        if (self.client is None):
            self.logger.error("Failed to connect to Qdrant")
            raise Exception("Failed to connect to Qdrant")



    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)

            env_path = Path(config.get("env_path")).expanduser()

            # Validate that the .env file exists
            if not env_path or not os.path.isfile(env_path):
                self.logger.error(f".env file not found at {env_path}")
                raise FileNotFoundError(".env path is invalid or not found in config.yaml")

            self.logger.info(f"Loading environment variables from: {env_path}")
                
            # Load environment variables from the .env file
            load_dotenv(env_path)

            # Validate required environment variables
            if not os.getenv("QDRANT_API_KEY"):
                raise ValueError("Missing required environment variable: QDRANT_API_KEY")
            
            return config
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise


    def load_qa_pairs(self) -> List[Dict[str, Any]]:
        """Load question-answer pairs from JSONL file"""
        qa_pairs = []
        try:
            with jsonlines.open(self.qa_json_path) as reader:
                for obj in reader:
                    if "question" in obj and "answer" in obj:
                        qa_pairs.append(obj)
                    else:
                        self.logger.warning(f"Skipping invalid entry: {obj}")
            return qa_pairs
        except Exception as e:
            self.logger.error(f"Error loading QA pairs: {str(e)}")
            raise


    def connect_to_qdrant(self, config: dict):
        """"Connect to qdrant"""
        url = self.qdrant_url
        api_key = os.getenv("QDRANT_API_KEY")
        client = QdrantClient(
                url=url,
                api_key=api_key)
        return client


    def extract_keywords(self, query) -> list:
        """"This function cleans queries from stop words and linguistic noise"""
        keywords = self.kw_model.extract_keywords(query)
        keywords_range = [word for word in keywords if word[0] not in stop_words and word [0] not in instructional_stop_words]
        keywords_ex = [word[0] for word in keywords_range]
        return keywords_ex 


    def evaluate_results_with_context(self, 
                                      enhanced_results: List[Dict[str, Any]], 
                                      ground_truth: str, 
                                      ground_truth_chunk_id: str, 
                                      with_ranking=True) -> Dict[str, Any]:
        """Evaluate search results with context against ground truth using BERTScore"""
        try:        
            # Prepare lists for BERTScore while preserving metadata
            candidates = []
            metadata = []
            retrieved_chunk_ids = []
            
            for enhanced_hit in enhanced_results:
                hit = enhanced_hit["main"]
                candidates.append(hit.payload.get("content", ""))
                
                # Extract metadata from the main hit
                hit_metadata = hit.payload.get("metadata", {})
                chunk_id = hit_metadata.get("chunk_id")  
                retrieved_chunk_ids.append(chunk_id)

                metadata.append({
                    "doc_id": hit_metadata.get("doc_id"),
                    "section_title": hit_metadata.get("section_title"),
                    "chunk_index": hit_metadata.get("chunk_index"),
                    "paragraph_id": hit_metadata.get("paragraph_id"),
                    "paragraph_index": hit_metadata.get("paragraph_index"),
                    "title": hit_metadata.get("title"),
                    "source_url": hit_metadata.get("source_url"),
                    "qdrant_score": hit.score
                })
            
            references = [ground_truth] * len(candidates)
            
            # Calculate BERTScore
            P, R, F1 = self.scorer.score(candidates, references)
            
            # Convert tensors to lists properly
            P_list = [score.item() for score in P]
            R_list = [score.item() for score in R]
            F1_list = [score.item() for score in F1]
            
            # Get the best matching chunk
            best_match_idx = F1.argmax().item()
            best_match_score = F1[best_match_idx].item()
            best_match_content = candidates[best_match_idx]
            best_match_metadata = metadata[best_match_idx]

            # === nDCG Calculation ===


            if with_ranking:

                # Create binary relevance vector: 1 if chunk_id matches, else 0
                y_true = [[1 if cid == ground_truth_chunk_id else 0 for cid in retrieved_chunk_ids]]
                y_score = [list(reversed(range(1, len(retrieved_chunk_ids) + 1)))]  # ideal rank order

                try:
                    ndcg = ndcg_score(y_true, y_score)
                except ValueError as e:
                    ndcg = 0.0
                    self.logger.warning(f"nDCG calculation failed: {e}")


                # === MRR Calculation ===
                try:
                    if ground_truth_chunk_id in retrieved_chunk_ids:
                        rank = retrieved_chunk_ids.index(ground_truth_chunk_id) + 1  # 1-based index
                        mrr = 1.0 / rank
                    else:
                        mrr = 0.0
                except Exception as e:
                    mrr = 0.0
                    self.logger.warning(f"MRR calculation failed: {e}")
            
                return {
                    "total_chunks": len(enhanced_results),
                    "ndcg": ndcg,
                    "mrr": mrr,
                    "best_match_score": best_match_score,
                    "best_match_content": best_match_content[:200] + "..." if len(best_match_content) > 200 else best_match_content,
                    "best_match_metadata": best_match_metadata,
                    "average_f1": F1.mean().item(),
                    "average_precision": P.mean().item(),
                    "average_recall": R.mean().item(),
                    "all_scores": {
                        "precision": P_list,
                        "recall": R_list,
                        "f1": F1_list,
                        "metadata": metadata
                    }
                }

            else: 
                return {
                    "total_chunks": len(enhanced_results),
                    #"ndcg": ndcg,
                    #"mrr": mrr,
                    "best_match_score": best_match_score,
                    "best_match_content": best_match_content[:200] + "..." if len(best_match_content) > 200 else best_match_content,
                    "best_match_metadata": best_match_metadata,
                    "average_f1": F1.mean().item(),
                    "average_precision": P.mean().item(),
                    "average_recall": R.mean().item(),
                    "all_scores": {
                        "precision": P_list,
                        "recall": R_list,
                        "f1": F1_list,
                        "metadata": metadata
                    }
                }

        except Exception as e:
            self.logger.error(f"Error in BERTScore evaluation: {str(e)}")
            return {
                "error": str(e),
                "total_chunks": len(enhanced_results)
            }
    

    def rerank_candidates(self, query, enhanced_results, top_k=5):
        """
        Rerank enhanced Qdrant results using a cross-encoder and return top_k most relevant with metadata.

        Args:
            query (str): The user question.
            enhanced_results (List[Dict]): List of dicts containing "main" Qdrant hits and metadata.
            top_k (int): Number of top passages to return.

        Returns:
            List[Dict]: Top-k reranked enhanced results (same structure as input).
        """
        
        candidates = []
        
        # Extract content for scoring
        for enhanced_hit in enhanced_results:
            hit = enhanced_hit["main"]
            candidates.append(hit.payload.get("content", ""))

        # Cross-encoder input formatting
        inputs = self.tokenizer(
            [(query, passage) for passage in candidates],
            padding=True,
            truncation=True,
            return_tensors="pt"
        )

        # Compute relevance scores
        with torch.no_grad():
            scores = self.model(**inputs).logits.squeeze(-1)

        # Get indices of top_k results
        top_indices = torch.topk(scores, k=top_k).indices.tolist()

        # Return corresponding full enhanced hits
        return [enhanced_results[i] for i in top_indices]


    def clear_collection(self, client: QdrantClient, collection_name: str) -> None:
        """
        Clear all points from a Qdrant collection.
        
        Args:
            client: QdrantClient instance
            collection_name: Name of the collection to clear
        """
        try:
            # First check if collection exists
            collections = client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if collection_name not in collection_names:
                self.logger.warning(f"Collection {collection_name} does not exist")
                return
                
            # Clear all points
            client.clear_payload(
                collection_name=collection_name,
                points_selector=models.Filter(
                    must=[]  # Empty filter matches all points
                )
            )
            self.logger.info(f"Cleared all points from collection {collection_name}")
                
        except Exception as e:
            self.logger.error(f"Error clearing collection {collection_name}: {str(e)}")
            raise

    
    def get_adjacent_paragraphs(self, search_result, context_window=1):
        enhanced_results = []

        for hit in search_result:
            metadata = hit.payload.get('metadata', {})
            doc_id = metadata.get('doc_id')
            paragraph_id = metadata.get('paragraph_id')
            paragraph_index = metadata.get('paragraph_index')

            if doc_id and paragraph_index is not None:
                # Get adjacent paragraphs
                adjacent_paragraphs = []
                for offset in range(-context_window, context_window + 1):
                    if offset == 0:
                        continue  # Skip the current paragraph

                    # Search for adjacent paragraph
                    adjacent_result = self.client.scroll(
                        collection_name=self.qdrant_collection,
                        scroll_filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="metadata.doc_id",
                                    match=models.MatchValue(value=doc_id)
                                ),
                                models.FieldCondition(
                                    key="metadata.paragraph_id",
                                    match=models.MatchValue(value=paragraph_id)
                                ),
                                models.FieldCondition(
                                    key="metadata.paragraph_index",
                                    match=models.MatchValue(value=paragraph_index + offset)
                                )
                            ]
                        ),
                        limit=1,
                        with_payload=True,
                        with_vectors=False
                    )

                    if adjacent_result[0]:  # If an adjacent paragraph is found
                        adjacent_paragraphs.append(adjacent_result[0][0])

                if hit.payload.get('content', '').strip():
                    enhanced_hit = {
                        "main": hit,
                        "adjacent": adjacent_paragraphs
                    }
                    enhanced_results.append(enhanced_hit)
            else:
                if hit.payload.get('content', '').strip():
                    enhanced_results.append({"main": hit, "adjacent": []})

        return enhanced_results



    def evaluate_qa_pair(self, qa_pair):
        question = qa_pair["question"]
        answer = qa_pair["answer"]
        ground_truth_chunk_id = qa_pair["chunk_id"]
        doc_id = qa_pair["doc_id"]
        larger_context = qa_pair["context"]

        # Encode the question (optionally with extracted keywords)
        query_text = ' '.join(self.extract_keywords(question)) if self.extract_kw else question
        query_embedding = self.qdrant_model.encode(query_text)

        # Set search limit depending on reranking
        limit = 20 if self.reranking else self.qdrant_limit

        # Search Qdrant
        search_result = self.client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding.tolist(),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        # Optionally enhance with adjacent paragraphs
        enhanced_results = self.get_adjacent_paragraphs(search_result)

        # Optional reranking
        if self.reranking:
            enhanced_results = self.rerank_candidates(question, enhanced_results)

        # Evaluate results
        evaluation = self.evaluate_results_with_context(
            enhanced_results, answer, ground_truth_chunk_id
        )

        # Collect results
        candidates = [hit["main"].payload.get("content", "") for hit in enhanced_results]

        return {
            "question": question,
            "answer": answer,
            "larger_context": larger_context,
            "ground_truth_chunk_id": ground_truth_chunk_id,
            "doc_id": doc_id,
            "ncdg": evaluation.get("ndcg"),
            "mrr": evaluation.get("mrr"),
            "best_match_score": evaluation.get("best_match_score"),
            "average_f1": evaluation.get("average_f1"),
            "average_precision": evaluation.get("average_precision"),
            "average_recall": evaluation.get("average_recall"),
            "candidates": candidates,
        }
    

    def write_eval_to_file(self, output_eval: str):

        for i, qa_pair in tqdm(enumerate(self.qa_pairs, 1)):

            file_exists = os.path.isfile(output_eval)
            try:
                row = self.evaluate_qa_pair(qa_pair)
            # Write as JSONL
                with open(output_eval, "a", encoding="utf-8") as f:
                    if file_exists:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception as e:
                self.logger.error(f"Error during query: {str(e)}")
                raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation and write output to file.")
    parser.add_argument(
        "--output_path",
        type=str,
        default="tools/evaluate_qdrant/data/eval_output/ws1_wosmallparagraphs_eval.jsonl",
        help="Path to save the evaluation results."
    )
    args = parser.parse_args()

    evaluator = Evaluator(qdrant_collection="ws1-wosmallparagraphs", reranking=False)
    evaluator.write_eval_to_file(args.output_path)
