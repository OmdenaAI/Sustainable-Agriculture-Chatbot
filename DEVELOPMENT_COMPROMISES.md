# Development Compromises Log

This document tracks the compromises made during development to keep the system functional in the face of dependency and integration challenges.

## Current Compromises (Updated: May 11, 2025)

### 1. Database Implementation
- **Original Design**: Supabase for authentication and chat history storage
- **Current Implementation**: In-memory storage due to Supabase connection issues
- **Impact**: Chat history is lost when the server restarts
- **Resolution Plan**: Properly configure Supabase or implement a different database solution

### 2. Authentication
- **Original Design**: Full JWT-based authentication with Supabase
- **Current Implementation**: Simplified mock user system with `BYPASS_AUTH=true`
- **Impact**: No need to log in, reduced security but easier for development/testing
- **Resolution Plan**: Re-implement proper authentication when database issues are resolved

### 3. AI Implementation
- **Original Design**: Integration with Groq/OpenAI API
- **Current Implementation**: Mock AI service with pre-defined responses for agricultural topics
- **Impact**: Limited but functional responses without external API dependencies
- **Resolution Plan**: Set up proper API keys and integrate with Groq or OpenAI

### 4. RAG (Retrieval Augmented Generation)
- **Original Design**: Document retrieval from vector database (Qdrant)
- **Current Implementation**: Simplified mock implementation returning empty context
- **Impact**: No true RAG capabilities, but the chat interface still works
- **Resolution Plan**: Set up and populate a vector database for document retrieval

## Using the Current Implementation

The current implementation works well for:
- Frontend development and UI testing
- Basic chat functionality testing
- Developing new features without external dependencies

To use the system in its current state:
1. Start the backend (`cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`)
2. Start the frontend (`cd frontend && npm run dev`)
3. Access the chat interface at `http://localhost:3000/chat`

No login is required, and you can ask questions about various agricultural topics like permaculture, organic farming, soil health, etc.

## How to Test Agriculture Topics

The system currently responds to these specific topics (try asking about them):
- Permaculture
- Organic farming
- Soil health
- Crop rotation
- Sustainable agriculture
- Regenerative agriculture
- Companion planting
- Composting
- Cover crops
- Hydroponics
- Carrots (and other specific crops)
- Mountain farming
- Himalayan agriculture

Example queries:
- "Tell me about permaculture"
- "How does crop rotation work?"
- "What are the benefits of composting?"
- "Can I grow carrots in the Himalayas?"

## Enabling Real RAG Implementation

The codebase includes a proper implementation of the RAG system using Qdrant. To enable it:

1. **Set up Qdrant**:
   - Option 1: Run locally with Docker: `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant`
   - Option 2: Use [Qdrant Cloud](https://cloud.qdrant.io/)

2. **Update environment variables**:
   - Edit `.env.development` file
   - Set `QDRANT_URL` to your Qdrant instance URL
   - Set `QDRANT_API_KEY` to your API key (if using Qdrant Cloud)
   - Set `OPENAI_API_KEY` to your OpenAI API key
   - Set `USE_MOCK_RAG=false` to disable the mock implementation

3. **Install required Python packages**:
   ```bash
   cd backend
   pip install qdrant-client openai
   ```

4. **Populate the vector database**:
   - Use the scripts in `backend/tools/insert_db` to add documents to the database
   - Or develop a script to ingest your own documents

5. **Restart the backend**:
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

Once these steps are completed, the chatbot will use real document retrieval to provide more accurate and contextually relevant answers. 