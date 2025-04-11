# Sustainable Agriculture Chatbot

## Environment Setup

The project uses Supabase for authentication and database. We use a shared Supabase instance for the team.

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

3. Update `.env.development` with your personal GROQ API key:
- Get your GROQ API key from: https://console.groq.com
- The Supabase credentials are already included and safe to use

### API Keys and Security
- The Supabase URL and anon key are safe to share and are included in the example files
- Each developer needs their own GROQ API key
- Never commit your personal API keys to the repository
- The Supabase service role key is NOT included and should never be shared

[Rest of your README stays the same...]
