import os
import json
import re
from chunkers.overlap_paragraph_chunker import OverlapChunks
from settings import models_to_chunk_size_mapping

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


def create_chunks_from_text_file(dir_path, chunker, chunk_size, metadata=None,):
    """Creating chunks from text files in a directory"""
    

    for file in os.listdir(dir_path):
        if file.endswith('json'):
            file_prefix = re.match(r'(.+?)_base_payload.json', file).group(1)
            break
    
   
    all_chunks = []
    
    metadata = get_metadata(dir_path)

    final_text_to_overlap = ""

    if chunker == "overlap":
        overlap_percentage = 20
        chunker = OverlapChunks(chunk_size, overlap_percentage)

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
    files_to_chunk_dir = "../extract_and_normalize/output"
    chunk_store_file = "output_chunks/chunks.json"
    chunk_size = models_to_chunk_size_mapping["text-embedding-3-small"]
    chunker = "overlap"
    
    chunks = create_chunks_from_text_file(files_to_chunk_dir, chunker, chunk_size,)
    store_chunks(chunks, chunk_store_file)