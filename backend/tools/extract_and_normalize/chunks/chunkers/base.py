from abc import ABC
from typing import List
from models.chunk import Chunk


class AbstractChunker(ABC):
    """General structure for chunkers"""
    def generate_chunks(self, text: str, metadata: dict) -> List[Chunk]:
        """
        Generate chunks from the given text.
        Args:
            text (str): The text to be chunked.
        Returns:
            List[AbstractChunk]: A list of generated chunks.
        """
        
        pass
