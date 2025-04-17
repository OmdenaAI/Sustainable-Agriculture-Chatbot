from typing import List
from models.chunk import Chunk
from chunkers.base import AbstractChunker
import uuid

class OverlapChunks(AbstractChunker):
    def __init__(self, chunk_size: int = 1024, overlap_percentage: int = 20):
        self.chunk_size = chunk_size
        self.overlap_percentage = overlap_percentage #amount of overlap between chunks in percentage of chunk_size
        self.overlap_words = int(chunk_size * self.overlap_percentage / 100)

    def generate_chunks(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Generate overlapping chunks from a text based on the chunker-size and metadata
              chunker-size depends on the number of words for a given embedding model
           """
        words = text.split()
        chunks = []
        step = self.chunk_size - self.overlap_words
        for i in range(0, len(words), step):
            
            chunk_text = ' '.join(words[i:i + self.chunk_size])
            chunk = Chunk(
                id=str(uuid.uuid4()),
                text=chunk_text,
                metadata=metadata
            )
            chunks.append(chunk)

        return chunks
    

