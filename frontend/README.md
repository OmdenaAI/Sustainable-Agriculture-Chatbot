# Next.js + Supabase RAG Frontend

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/pages/api-reference/create-next-app), and configured to work with [Supabase](https://supabase.com) for authentication and database access.

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
npm install
```

### 2. Set up environment variables

Create a `.env.local` file in the root directory and add:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Replace `your-project-id` and `your-anon-key` with your actual values from the **Supabase dashboard → Settings → API**.

---

### 3. Run the development server

```bash
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser to view the app.

---

## 📦 Project Structure

- `pages/index.tsx` – Main app page
- `pages/api/` – API routes (can be used for backend logic like RAG)
- `lib/` – Supabase client or utility functions
- `styles/` – Tailwind and global styles
- `public/` – Static assets

---

## 🔐 Test Authentication (Optional)

To test with Supabase auth (if enabled):

- **Email:** `test3@example.com`  
- **Password:** `password123`

---

## 🔗 Useful Links

- [Supabase Documentation](https://supabase.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### set up on the backend file .env

# Logging settings
LOG_LEVEL=INFO

ENVIRONMENT=development
SECURE_COOKIES=false

# Authentication bypass
BYPASS_AUTH=true
