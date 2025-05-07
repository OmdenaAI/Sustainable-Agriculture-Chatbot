# Agriculture Knowledge Assistant

An AI-powered assistant for agriculture-related questions, powered by RAG (Retrieval Augmented Generation) and the latest research and knowledge.

## Project Structure

The project is divided into two main parts:

### Frontend (Next.js)

The frontend is built with Next.js and includes:

- Authentication (login/signup)
- Chat interface
- Landing page

### Backend (FastAPI)

The backend is built with FastAPI and includes:

- Authentication with Supabase for user management and session handling
- RAG (Retrieval Augmented Generation) system for knowledge-based responses
- Integration with Groq for LLM capabilities (using LLaMA 3 model)
- Document ingestion and retrieval for agricultural knowledge
- Qdrant vector database for storing and searching document embeddings
- OpenAI embeddings API for converting text to vector representations
- Asynchronous processing for improved performance
- Structured logging for monitoring and debugging

Qdrant specifically serves as the vector database that:
- Stores document embeddings (vector representations of text)
- Enables semantic search through cosine similarity
- Retrieves the most relevant documents for user queries
- Supports the RAG pipeline by finding context for the LLM

## Setup Instructions

### Frontend

1. Navigate to the frontend directory
2. Install dependencies: `npm install`
3. Create a `.env.local` file with the following variables:
   \`\`\`
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   NEXT_PUBLIC_API_URL=http://localhost:8000
   \`\`\`
4. Run the development server: `npm run dev`

### Backend

1. Navigate to the backend directory
2. install Poetry: `curl -sSL https://install.python-poetry.org | python3` 
3. Update your PATH (if needed): `export PATH="$HOME/.local/bin:$PATH"`
4. Install dependencies: `poetry install`
5. Create a `.env` file based on `.env.example`
6. Run the server: `poetry run uvicorn main:app --reload`

> Note: Poetry automatically manages the virtual environment, so you don't need to activate it manually.
\`\`\`

## API Endpoints

The backend provides the following key endpoints:

### Health Check

- **URL**: `/health`
- **Method**: GET
- **Description**: Check if the API is running
- **Response**: Status and version information


### Chat

- **URL**: `/api/chat`
- **Method**: POST
- **Description**: Send a message to the chatbot and get a response
- **Request Body**:
```json
{
 "message": "How do I control aphids on my tomato plants?",
 "history": [
   {"role": "user", "content": "previous message"},
   {"role": "assistant", "content": "previous response"}
 ],
 "session_id": "optional-session-id"
}

Response:
{
  "response": "To control aphids on tomato plants, you can try several methods...",
  "session_id": "session-id"
}

## Testing the API

### Using curl

1. **Health Check**:

curl http://localhost:8000/health

2. **Chat**:

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are sustainable farming practices?", "history": []}'

3. **Document Ingestion**:

curl -X POST http://localhost:8000/api/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Sustainable farming practices include crop rotation, which helps maintain soil health...",
    "title": "Sustainable Farming Guide",
    "source": "Agricultural Extension Office"
  }'
  

### Using Swagger UI

The API includes Swagger documentation that allows you to test endpoints directly in your browser:

1. Open "http://localhost:8000/docs](http://localhost:8000/docs) in your browser"
2. Browse the available endpoints
3. Click on an endpoint to expand it
4. Click the "Try it out" button
5. Fill in the required parameters
. Click "Execute" to send the request 

### Using Postman or Insomnia

For more complex testing, you can use API tools like Postman or Insomnia:

1. Create a new request with the appropriate HTTP method
2. Set the URL to the endpoint you want to test
3. Add any required headers (usually Content-Type: application/json)
4. Add the request body in JSON format
5. Send the request and view the response