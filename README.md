# RepoMind AI

AI-powered codebase understanding platform with repository ingestion, structural parsing, semantic retrieval, and LLM chat.

## Stack
- Frontend: Next.js App Router, TypeScript, Tailwind CSS, shadcn-style UI primitives
- Backend: FastAPI, async REST APIs
- AI/RAG: Tree-sitter, sentence-transformers (`all-MiniLM-L6-v2`), ChromaDB, Ollama (`mistral`)
- Auth: Supabase Auth

## Project Structure
```text
repo-mind-ai/
├── frontend/
├── backend/
│   ├── api/
│   ├── parser/
│   ├── embeddings/
│   ├── retrieval/
│   ├── llm/
│   ├── github/
│   ├── services/
│   └── repos/
└── docs/
```

## Implemented Backend Endpoints
- `POST /upload-repo`
- `POST /upload-zip`
- `POST /chat`
- `GET /summary?repository_id=...`
- `GET /files?repository_id=...`
- `GET /health`

## Local Setup

### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd ..
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### 3) Ollama
```bash
ollama pull mistral
ollama serve
```

## Supabase Auth Setup
Set frontend env vars:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

Enable Email/Password auth in your Supabase project.

## Security & Processing Notes
- Repository ingestion sanitizes:
  - `node_modules`, `dist`, `build`, `.git`, `venv`
- Sensitive files are removed during ingest if names include:
  - `.env`, `secrets`, `credentials`
- Repositories are stored temporarily in `backend/repos/`.

## Deploy Targets
- Frontend: Vercel
- Backend: Render

For deployment, set environment variables from `.env.example` in each platform dashboard.
