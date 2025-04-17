from typing import List
from models.chunk import Chunk
from chunkers.base import AbstractChunker
import uuid

class TokenChunks(AbstractChunker):
    def __init__(self, chunk_size: int = 1024):
        self.chunk_size = chunk_size

    def generate_chunks(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Generate chunks from a text based on the chunker-size and metadata
           chunker-size depends on the number of tokens for a given embedding model
           """
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size):
            chunk_text = ' '.join(words[i:i + self.chunk_size])
            chunk = Chunk(
                id = str(uuid.uuid4()),
                text=chunk_text,
                metadata=metadata
            )
            chunks.append(chunk)
        return chunks
           
                       
            
         