from typing import List, Dict, Tuple
from uuid import uuid4
from chunkers.base import AbstractChunker
import copy
import json
import jsonschema
from jsonschema import validate
from pathlib import Path
import logging
class OverlapParagraphChunks(AbstractChunker):
    def __init__(self, logger: logging.Logger, chunk_size: int = 1024, overlap_percentage: int = 20):
        self.logger = logger
        self.chunk_size = chunk_size
        self.overlap_percentage = overlap_percentage
        self.overlap_words = int(chunk_size * self.overlap_percentage / 100)
        self.schema = self._load_schema(Path("schemas/sustainable_agriculture.schema.json"))

    def _load_schema(self, schema_path: Path):
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        return schema

    def _create_chunk(self, chunk_text: str, chunk_idx: int, chunk_schema: dict) -> dict:
        """Create a chunk with only schema-defined fields"""
        section_title = chunk_schema.get("section_title", "Unknown Section")
        # Do not invlude section title in text if its Unknown or contains what looks like a page number from a headrt
        text = chunk_text if section_title == "Unknown Section" or section_title.startswith("Page") else f'{section_title}\n\n{chunk_text}'
        chunk = {
                    "title": chunk_schema.get("title", "Unknown"),
                    "source_url": chunk_schema.get("source_url", "Unknown"),
                    "date_published": chunk_schema.get("date_published", "Unknown"),
                    "language": chunk_schema.get("language", "Unknown"),
                    "region_or_country": chunk_schema.get("region_or_country", "Unknown"),
                    "document_type": chunk_schema.get("document_type", "Unknown"),
                    "sustainability_dimensions": chunk_schema.get("sustainability_dimensions", []),
                    "key_topics": chunk_schema.get("key_topics", []),
                    "contains_harmful_practices": chunk_schema.get("contains_harmful_practices", "Unknown"),
                    "intended_audience": chunk_schema.get("intended_audience", []),
                    "source_name": chunk_schema.get("source_name", "Unknown"),
                    "doc_id": chunk_schema.get("doc_id", ""),
                    "chunk_id": chunk_schema["chunk_id"],
                    "chunk_index": chunk_idx,  # Preserve existing chunk_index behavior
                    "section_title": section_title,
                    "text": text,
                    "paragraph_id": chunk_schema["paragraph_id"],
                    "paragraph_index": chunk_schema["paragraph_index"]
                }
                
        try:
            validate(instance=chunk, schema=self.schema)
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Validation failed for chunk: {e.message}")
            raise ValueError(f"Validation failed for chunk: {e.message}") 
        
        return chunk

    def generate_chunks(self, text: str, metadata: dict = None) -> List[dict]:
        """Generate overlapping chunks from a text based on the chunker-size and metadata
           chunker-size depends on the number of words for a given embedding model
        """
        chunks = []
        paragraphs = text.split('\n\n')
        final_text_to_overlap = ""
        
        for paragraph in paragraphs:
            paragraph_id = str(uuid4())  # Generate unique ID for this paragraph
            paragraph_text = final_text_to_overlap + paragraph
            words = paragraph_text.split()
            
            # Check if paragraph needs to be split
            if len(words) <= self.chunk_size:
                # Paragraph fits in one chunk
                chunk_text = ' '.join(words)
                chunk_schema = copy.deepcopy(metadata) if metadata else {}
                chunk_schema.update({
                    "chunk_id": str(uuid4()),
                    "paragraph_id": paragraph_id,
                    "paragraph_index": 0
                })

                chunk = self._create_chunk(chunk_text, len(chunks), chunk_schema)               
                chunks.append(chunk)
                final_text_to_overlap = ""
            else:
                # Paragraph needs to be split
                step = self.chunk_size - self.overlap_words
                split_count = 0
                
                for start in range(0, len(words), step):
                    chunk_text = ' '.join(words[start:start + self.chunk_size])
                    chunk_schema = copy.deepcopy(metadata) if metadata else {}
                    chunk_schema.update({
                        "chunk_id": str(uuid4()),
                        "paragraph_id": paragraph_id,
                        "paragraph_index": split_count
                    })

                    chunk = self._create_chunk(chunk_text, len(chunks), chunk_schema)                   
                    chunks.append(chunk)
                    final_text_to_overlap = ' '.join(chunk_text.split()[-self.overlap_words:])
                    split_count += 1
        
        return chunks, final_text_to_overlap
    

