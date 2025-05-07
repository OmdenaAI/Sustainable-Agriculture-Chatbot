import re
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Trim whitespace
    text = text.strip()
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to find a good breaking point (period, newline, etc.)
        break_point = text.rfind('. ', start, end)
        if break_point == -1:
            break_point = text.rfind(' ', start, end)
        if break_point == -1:
            break_point = end
        else:
            break_point += 1  # Include the space or period
        
        chunks.append(text[start:break_point])
        start = break_point - overlap  # Create overlap
        
        if start < 0:
            start = 0
    
    return chunks

def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results for inclusion in LLM prompt
    """
    if not results:
        return "No relevant information found."
    
    formatted = "Relevant information:\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"[{i}] {result['text']}\n\n"
    
    return formatted
