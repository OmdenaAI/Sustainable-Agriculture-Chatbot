import os
import json
import re
from chunkers.overlap_paragraph_chunker import OverlapParagraphChunks
import argparse
from pathlib import Path
import logging

# Configure logging to display messages with timestamps and severity levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CreateChunks")

def validating_file(dir_path):
    if not os.path.isdir(dir_path):
        logger.error(f"Invalid directory path: {dir_path}")
        raise ValueError(f"Invalid directory path: {dir_path}") 
    if not any(file.endswith('.json') for file in os.listdir(dir_path)):
        logger.error(f"No JSON files found in the directory: {dir_path}")
        raise ValueError(f"No JSON files found in the directory: {dir_path}")
    if not any(file.endswith('.txt') for file in os.listdir(dir_path)):
        logger.error(f"No text files found in the directory: {dir_path}")
        raise ValueError(f"No text files found in the directory: {dir_path}")
    return True

def get_text(file_path):
    """read text from a .tex file """
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


def get_metadata(dir_path):
    """read metadata from a .json file """
    json_file = next((f for f in os.listdir(dir_path) if f.endswith('.json')), None)
    if json_file:
        with open(os.path.join(dir_path, json_file), 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def create_chunks_from_text_file(dir_path, chunker, metadata=None):
    """Creating chunks from text files in a directory"""

    file = next((f for f in os.listdir(dir_path) if f.endswith('.json')), None)
    file_prefix = re.match(r'(.+?)_base_payload.json', file).group(1)

    all_chunks = []
    
    metadata = get_metadata(dir_path)

    final_text_to_overlap = ""

    chunker = chunker
    sorted_pages = sorted([int(re.search(r'_page_(\d+)\.txt', file).group(1)) for file in os.listdir(dir_path) if file .startswith(file_prefix) and file.endswith('txt')])
    chunk_index = 0
    for index in sorted_pages:
        
        file = f"{file_prefix}_page_{index}.txt"

        file_metadata = metadata.copy()
        
        page_text = get_text(f"{dir_path}/{file}")
        """extrat the first line of the text file as title"""
        file_metadata["section_title"] = page_text.split('\n')[0].strip('- ')
        text_without_first_line = re.sub(r'^[^\n]*\n', '', page_text)
        text = final_text_to_overlap + text_without_first_line
        
        chunks, final_text_to_overlap = chunker.generate_chunks(text, file_metadata)
        final_text_to_overlap = final_text_to_overlap.replace('\n', ' ')
        for chunk in chunks:
            chunk["chunk_index"] = chunk_index
            chunk_index += 1 

        all_chunks.extend(chunks)

    return all_chunks

def store_chunks(chunks, file_path):
    """Storing chunks in a JSON file, creating directory if it doesn't exist"""
    # Convert file_path to Path object and get its parent directory
    path = Path(file_path)
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump([chunk for chunk in chunks], f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate chunks from text files and ingest metadata from a JSON file")
    parser.add_argument("--chunk_size", required=True, help="number of words for a given embedding model")
    parser.add_argument("--chunker_technique", default="overlap", help="chunker technique to use")
    parser.add_argument("--overlap_percentage", default=20, type=int, help="overlap percentage for the chunker")
    parser.add_argument("--input", required=True, help="input file")
    parser.add_argument("--output", required=True, help="output file")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config YAML")
    
    try:
        args = parser.parse_args()
        
        files_to_chunk_dir = args.input
        chunk_store_file = args.output + "/chunks.json"
        
        chunk_size = int(args.chunk_size)

        # include as many case as chunk techniques are defined (script in the chunkers folder) 
        if args.chunker_technique == "overlap":
            chunker = OverlapParagraphChunks(logger, chunk_size, args.overlap_percentage)
        else:
            logger.error(f"Unknown chunker technique: {args.chunker_technique}")
            raise ValueError(f"Unknown chunker technique: {args.chunker_technique}")
        
        file_validation = validating_file(files_to_chunk_dir)

        chunks = create_chunks_from_text_file(files_to_chunk_dir, chunker)
        store_chunks(chunks, chunk_store_file)

    except Exception as e:
        logger.error(f"Chunker failed to generate chunks: {e}")
            
        exit(1)