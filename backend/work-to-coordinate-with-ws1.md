### WS1 Coordination Points: Agriculture Chatbot

### Vector Database (Qdrant) Integration ###
File: `backend/db/qdrant.py`

_qdrant_client.create_collection(
    collection_name=settings.QDRANT_COLLECTION,
    vectors_config=models.VectorParams(
        size=settings.EMBEDDING_DIMENSION,
        distance=models.Distance.COSINE,
    )
)

**Coordination Points:**

- collection name: `agriculture_docs`
- Verify vector dimension: `1536`
- Confirm distance metric: `COSINE`
- Determine who creates/manages the collection


## Search Parameters
search_result = self.client.search(
    collection_name=self.collection_name,
    query_vector=query_embedding,
    limit=limit
)

**Coordination Points:**

- Default search limit: `5`
- Additional filters needed?
- Score threshold for relevance?


### Embedding Generation ###

**File: `backend/services/rag_service.py`**

Embedding Model

self.embedding_model = "text-embedding-3-small"
self.embedding_api_url = "https://api.openai.com/v1/embeddings"

**Coordination Points:**

- Confirm embedding model: `text-embedding-3-small`
- API provider: OpenAI
- API key management

# Embedding Request

response = await client.post(
    self.embedding_api_url,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.embedding_api_key}"
    },
    json={
        "model": self.embedding_model,
        "input": text
    },
    timeout=10.0
)

**Coordination Points:**

- Request timeout: `10.0` seconds
- Error handling strategy
- Rate limiting considerations

### Document Processing ###

**File: `backend/utils/document_processor.py`**
chunking Strategy

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:

**Coordination Points:**

- Chunk size: `1000` tokens
- Overlap size: `200` tokens
- Breaking strategy (periods, spaces)
- Special content handling (tables, lists)


### Document Preparation ###
def prepare_document(text: str, metadata: Dict[str, Any] = {}, chunk_size: int = 1000) -> List[Dict[str, Any]]:
    # Create document objects
    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            "text": chunk,
            "metadata": {
                **metadata,
                "chunk": i,
                "total_chunks": len(chunks)
            }
        }
        documents.append(doc)

**Coordination Points:**

- Metadata structure
- Chunk indexing approach
- Text cleaning process

### Document Ingestion ###
File: `backend/api/routes/documents.py`

metadata = {
    "title": document_request.title,
    "source": document_request.source,
    "author": document_request.author,
    "user_id": current_user.id,
    **document_request.metadata
}

**Coordination Points:**

- Required metadata fields
- Optional metadata fields
- User association strategy
- Custom metadata handling

### Ingestion Process ###

# Add documents to RAG system
count = await rag_service.add_documents(documents)

**Coordination Points:**
- Batch size limits
- Rate limiting
- Duplicate detection
- Versioning strategy

### Document Schema ###

**File: `backend/models/schemas.py`**

Document Request Schema

class DocumentIngestionRequest(BaseModel):
    content: str
    title: str
    source: Optional[str] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = {}
    chunk_size: Optional[int] = None

**Coordination Points:**

- Required vs. optional fields
- Validation rules
- Custom chunk size allowance
- Metadata constraints


### Retrieval Strategy ###

**File: `backend/services/rag.py`**


Document Retrieval

async def retrieve(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:

**Coordination Points:**

- Default retrieval limit: `3`
- Relevance scoring
- Fallback strategy
- Result format


### Fallback Content ###

def _fallback_content(self) -> List[Dict[str, Any]]:
    """
    Return fallback content when retrieval fails
    """
    return [
        {
            "text": "Sustainable farming practices include crop rotation...",
            "metadata": {
                "source": "Sustainable Farming Guide",
                "relevance": 0.92
            },
            "score": 0.92
        },
        # More fallback content...
    ]

**Coordination Points:**

- Fallback content management
- When to use fallbacks
- Fallback content updates


### Context Integration ###

**File: `backend/services/ai_service.py`**

### Context Formatting
# Format context for the prompt
context_text = ""
if context and len(context) > 0:
    context_text = "\n\n".join([doc["text"] for doc in context])

**Coordination Points:**

- Context formatting approach
- Metadata inclusion in context
- Context ordering strategy

### System Prompt ###

system_message = f"""You are an agriculture expert assistant. 
Your goal is to provide helpful, accurate information about farming, crops, livestock, and agricultural practices.
Always base your answers on the provided context when available.

When you don't know the answer or don't have enough context, admit it and suggest what information might help.
Keep responses concise, practical, and focused on helping farmers and agricultural professionals.

Context information:
{context_text}"""

**Coordination Points:**

- System prompt design
- Context integration approach
- Response style guidelines

### Configuration Settings ###

**File: `backend/core/config.py`**

Environment Variables

# Qdrant settings
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "agriculture_docs")
EMBEDDING_DIMENSION: int = 1536  # OpenAI embedding dimension

# AI settings
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


### API Integration ###

**File: `backend/api/routes/chat.py`**

### Chat Endpoint

@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    # Retrieve relevant documents using RAG
    relevant_docs = await rag_service.retrieve(chat_request.message)
    
    # Generate response using AI service
    response = await ai_service.generate_response(
        message=chat_request.message,
        context=relevant_docs,
        history=chat_request.history,
        user_id=current_user.id
    )

**Coordination Points:**

- Authentication requirements
- Rate limiting
- Response format
- Error handling


### Summary of Required Information from WS1 ###

1. **Vector Database Access**

1. Qdrant URL
2. API key
3. Collection name (or creation permissions)



2. **Embedding Configuration**

1. Embedding model details
2. API access credentials
3. Dimension specifications



3. **Document Processing**

1. Preferred chunking strategy
2. Metadata schema requirements
3. Document validation rules



4. **Retrieval Parameters**

1. Optimal number of documents to retrieve
2. Relevance thresholds
3. Fallback strategies



5. **Agricultural Domain Knowledge**

1. Key agricultural topics to cover
2. Domain-specific terminology
3. Geographic or seasonal considerations

******************************************

**`backend/api/docs.py`**
- It enhances the API documentation with security schemes, error responses, etc.

**`backend/api/routes/documents.py`**

- This file implements the API endpoints for document ingestion
- It contains routes for adding documents to your RAG system

**i didn't include the file (backend/utils/document_processor.py)**

This file contains utilities for processing documents
It handles text cleaning, chunking, and preparation for ingestion (ws1 have to coordinate with ws1)

