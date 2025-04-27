import os
import json
import re
from chunkers.overlap_paragraph_chunker import OverlapParagraphChunks
import argparse

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
    

    for file in os.listdir(dir_path):
        if file.endswith('json'):
            file_prefix = re.match(r'(.+?)_base_payload.json', file).group(1)
            break
    
   
    all_chunks = []
    
    metadata = get_metadata(dir_path)

    final_text_to_overlap = ""
    chunker = chunker
    sorted_pages = sorted([int(re.search(r'_page_(\d+)\.txt', file).group(1)) for file in os.listdir(dir_path) if file .startswith(file_prefix) and file.endswith('txt')])
    
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
        all_chunks.extend(chunks)

    return all_chunks

def store_chunks(chunks, file_path):
    """Storing chunks in a JSON file"""
    with open(file_path, "w") as f:
        json.dump([chunk for chunk in chunks], f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate chunks from text files and ingest metadata from a JSON file")
    parser.add_argument("--chunk_size", required=True, help="number of words for a given embedding model")
    parser.add_argument("--chunker_technique", default="overlap", help="chunker technique to use")
    parser.add_argument("--overlap_percentage", default=20, type=int, help="overlap percentage for the chunker")
    parser.add_argument("--input", required=True, help="input file")
    parser.add_argument("--output", required=True, help="output file")
    
    args = parser.parse_args()
    
    files_to_chunk_dir = args.input
    chunk_store_file = args.output + "/chunks.json"
    
    chunk_size = int(args.chunk_size)

    # include as many case as chunk techniques are defined (script in the chunkers folder) 
    if args.chunker_technique == "overlap":
        chunker = OverlapParagraphChunks(chunk_size, args.overlap_percentage)
    else:
        raise ValueError(f"Unknown chunker technique: {args.chunker_technique}")
    
    chunks = create_chunks_from_text_file(files_to_chunk_dir, chunker)
    store_chunks(chunks, chunk_store_file)