# TextGen-RAG (FastAPI + RAG + React)

A minimal production-ready starter repository for a Text Generation service with RAG (retrieval-augmented generation) using ChromaDB and sentence-transformers for embeddings. The service exposes a simple REST API and a minimal React UI.

## Features
- FastAPI backend with `/v1/generate` endpoint
- RAG using Chromadb (local) + sentence-transformers
- Prompt manager and templates
- Simple React UI for testing
- Docker & docker-compose for local dev

## Prerequisites
- Docker & docker-compose OR Python 3.10+ and Node 18+
- (Optional) An OpenAI API key for generation (set `OPENAI_API_KEY` in env). The backend can be extended to use local HF models.

## Quickstart (Docker)

1. Copy `.env.example` to `.env` and set values.
2. Build and run:
   ```bash
   docker-compose up --build
   ```
3. Backend will be on `http://localhost:8000` and frontend on `http://localhost:3000`.

## Quickstart (local Python + npm)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# set env vars in .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Usage
- Index documents:
  - `POST /v1/index` with multipart `file` or call the included `index_docs.py` to index `backend/app/docs`.
- Generate:
  - `POST /v1/generate` with JSON: `{ "query": "write a short blog about X", "options": { "length":"short", "tone":"friendly" } }`

## Environment variables (.env)
- `OPENAI_API_KEY` - (optional) for using OpenAI generation.
- `API_KEY` - a simple API key for the service (used by frontend).
- `CHROMA_DIR` - local directory where Chroma will store its DB (default `./chroma_db`).

## Files & Implementation notes
- `backend/app/generate.py` — handles retrieval, prompt composition, and model call.
- `backend/app/index_docs.py` — simple indexer for markdown/text files.
- `frontend` — Vite + React minimal app to call the API.

## Next steps
- Add authentication, rate limiting, user accounts, and template management UI.
- Add moderation step and logging/audit.
- Optionally, swap to a hosted vector DB (Weaviate / Milvus / Chroma Cloud) if scaling.

---
