# Sustainable Agriculture Chatbot

## Current Status

**Important**: For information about the current implementation and development compromises, please read [DEVELOPMENT_COMPROMISES.md](DEVELOPMENT_COMPROMISES.md).

The chatbot currently uses in-memory storage instead of Supabase due to integration challenges. This means:
- No database setup is required to run the application
- Chat history is stored in memory and will be lost when the server restarts
- Authentication is bypassed automatically for development

## Environment Setup

The project was designed to use Supabase for authentication and database, but currently works with an in-memory implementation for easier development and testing.

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Copy the example environment file:
```bash
cp .env.local.example .env.local
```

The Supabase credentials are already included in the example file and are safe to use.

### Backend Setup
1. Navigate to the backend directory:
```bash
cd backend
```

2. Copy the example environment file:
```bash
cp .env.development.example .env.development
```

3. No need to update any API keys for basic functionality. The system will use pre-defined responses.

### Running the Application
1. Start the backend server:
```bash
cd backend
source venv/bin/activate  # If using venv
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend server:
```bash
cd frontend
npm run dev
```

3. Access the application at http://localhost:3000/chat

### Testing the Chatbot
The chatbot has pre-defined responses for various agricultural topics. See [DEVELOPMENT_COMPROMISES.md](DEVELOPMENT_COMPROMISES.md) for a list of topics you can ask about, such as:
- Permaculture
- Organic farming
- Soil health
- Crop rotation
- and many more

### Full Database Setup (Optional)
If you want to set up the full database functionality with Supabase:

1. Make sure your `.env.development` file has the following variables:
```
SUPABASE_URL=https://qnhzebttgovojzpuabyi.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

2. To set up the required database tables in Supabase, you need to run SQL commands to create:
   - `chat_sessions` - Stores chat session data
   - `chat_messages` - Stores individual messages within sessions

3. Modify the code to use Supabase instead of in-memory storage

### API Keys and Security
- The Supabase URL and anon key are safe to share and are included in the example files
- Each developer needs their own GROQ API key for AI functionality
- Never commit your personal API keys to the repository

