import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from tqdm import tqdm

load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_URL")
COLLECTION_NAME = "ws1-mergedparagraphs"

client = QdrantClient(
    url=QDRANT_HOST,
    api_key=QDRANT_API_KEY
)

total_points = client.count(collection_name=COLLECTION_NAME).count
print(f"Total number of documents: {total_points}")

#stats = client.get_collection(collection_name=COLLECTION_NAME)
#print(stats)

limit = 100
offset = None
seen_chunk_ids = set()

with open("tools/evaluate_qdrant/data/chunk_ids.txt", "w") as f:
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            offset=offset,
            with_payload=True
        )

        if not points:
            break

        for point in tqdm(points):
            #print(point.id)
            metadata = point.payload
            if metadata and "chunk_id" in metadata["metadata"]:
                cid = metadata["metadata"]["chunk_id"]
                if cid in seen_chunk_ids:
                    pass
                    #print("Duplicate chunk_id found, stopping scroll.")
                    #exit(0)  # or break outer loop in a cleaner way
                #seen_chunk_ids.add(cid)
                #f.write(str(cid) + "\n")


