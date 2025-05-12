import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
from app.core.config import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Load the embedding model
        Initialize the RAG service with Qdrant connection"""
        try:
            #Embedding model
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            try:
                self.EMBEDDING_DIMENSION = self.model.encode("test", normalize_embeddings=True).size #to get the true embedding size without hardcoding
            except:
               self.EMBEDDING_DIMENSION = settings.EMBEDDING_DIMENSION 

            print(self.EMBEDDING_DIMENSION, "DIMENSION")
            # Connect to Qdrant
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]

            print(settings.QDRANT_COLLECTION, "COLLECTION NAME")
            
            # Create collection if it doesn't exist
            if settings.QDRANT_COLLECTION not in collection_names:
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=self.EMBEDDING_DIMENSION, 
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION}")
            
            logger.info("Connected to Qdrant successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise

    async def generate_embedding(self, text):
        """
        Generate an embedding for the given text using OpenAI API
        
        Args:
            text: The text to embed
            
        Returns:
            list: The embedding vector
        """
        try:
            embedding = self.model.encode(text)
            print("QUERY EMB SIZE", embedding.size)

            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def add_documents(self, documents):
        """
        Add documents to Qdrant
        
        Args:
            documents: List of document chunks with content and metadata
            
        Returns:
            int: Number of documents added
        """
        try:
            # Log the operation
            logger.info(f"Adding {len(documents)} documents to Qdrant")
            
            points = []
            for doc in documents:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                # Generate embedding for the content
                embedding = await self.generate_embedding(content)
                
                # Create a point for Qdrant
                import uuid
                doc_id = str(uuid.uuid4())
                
                points.append(models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        "metadata": metadata
                    }
                ))
            
            # Batch insert into Qdrant
            self.client.upsert(
                collection_name='ws1-test',    #settings.QDRANT_COLLECTION UNCOMMENT WHEN INGESTING TO THE WORKING COLLECTION
                points=points
            )
            
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding documents to Qdrant: {str(e)}")
            raise

    #async def store_document(self, content, embedding, metadata):
    #    """
    #    Store a single document and its embedding in Qdrant
        
    #    Args:
    #        content: The document content
    #        embedding: The embedding vector
    #       metadata: Additional metadata
            
    #    Returns:
    #        str: The document ID
    #    """
    #    try:
    #        import uuid
    #        doc_id = str(uuid.uuid4())
    #        
    #        self.client.upsert(
    #            collection_name=settings.QDRANT_COLLECTION,
    #            points=[models.PointStruct(
    #                id=doc_id,
    #                vector=embedding,
    #                payload={
    #                    "content": content,
    #                    "metadata": metadata
    #                }
    #            )]
    #        )
            
    #        logger.info(f"Stored document {doc_id} in Qdrant")
    #       return doc_id
    #    except Exception as e:
    #        logger.error(f"Error storing document in Qdrant: {str(e)}")
    #        raise

    async def retrieve(self, query, limit=5): #settings.LIMIT_RETRIEVAL):
        """
        Retrieve relevant documents for a query from Qdrant
        
        Args:
            query: The query text
            limit: Maximum number of results to return
            
        Returns:
            list: Relevant documents
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.generate_embedding(query)
            
            # Search Qdrant
            search_result = self.client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                results.append({
                    "doc_id": str(scored_point.id),
                    "text": scored_point.payload.get("content", ""),
                    "metadata": scored_point.payload.get("metadata", {}),
                    "score": scored_point.score
                })

            print(results[0])
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {str(e)}")
            raise