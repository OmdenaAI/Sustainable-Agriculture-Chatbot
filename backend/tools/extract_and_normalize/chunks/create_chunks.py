import os
import json
from chunkers.overlap_chunker import OverlapChunks
from chunkers.token_chunker import TokenChunks
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
    all_chunks = []
    
    metadata = get_metadata(dir_path)
    metadata.update({
        "chunker": chunker
    })

    if chunker == "overlap":
        overlap_percentage = 20
        chunker = OverlapChunks(chunk_size, overlap_percentage)

    for file in os.listdir(dir_path):
        if file.endswith('txt'):
            text = get_text(f"{dir_path}/{file}")
            chunks = chunker.generate_chunks(text, metadata)
            all_chunks.extend(chunks)
    return all_chunks

if __name__ == "__main__":
    files_dir = "../output"
    chunk_size = models_to_chunk_size_mapping["text-embedding-3-small"]
    chunker = "overlap"
    # chunker = "token"
    
    chunks = create_chunks_from_text_file(files_dir, chunker, chunk_size,)
    import pdb; pdb.set_trace()

    print(chunks)