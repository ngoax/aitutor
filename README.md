# aitutor
**NOTE**: This repo is currently in active development.

A unified authoring interface for generating [OATutor](https://github.com/CAHLR/OATutor) tutoring content from course materials. Teachers upload their materials, a RAG-grounded LLM suggests task formats, drafts problems and adds hints, while teachers retain the ability to edit everything freely, and the tool exports valid OATutor `content-pool` JSON.


This project is part of a research project @ ETH Zurich, Learning and Instruction Lab.

## Stack

- **Backend**: Python / FastAPI / SQLModel (SQLite) / LangChain / ChromaDB
- **Frontend**: React + TypeScript (Vite)
- **LLMs**: multi-provider support via LangChain: OpenAI, Anthropic, and local models via Ollama

## Running locally

Backend (http://localhost:8000, docs at `/docs`):

```sh
cd backend
uv sync
uv run uvicorn app.main:app --port 8000 --reload
```

Frontend (http://localhost:5173):

```sh
cd frontend
npm install
npm run dev
```

## Checks

```sh
cd backend  && uv run pytest && uv run ruff check .
cd frontend && npx tsc --noEmit && npm run build
```

## Docker

A two-container test deployment: nginx serves the built frontend and proxies
`/api` to the backend, so only port 8080 is exposed and the API is same-origin.

```sh
cp .env.example .env   # add OPENAI_API_KEY and/or ANTHROPIC_API_KEY
docker compose up --build
```

The app is then at http://localhost:8080. State lives in the `data` volume
(SQLite, uploads, Chroma, exports); `docker compose down -v` deletes it.

Building for a Linux server from an ARM Mac needs an explicit platform:

```sh
docker buildx build --platform linux/amd64 -t aitutor-backend ./backend
docker buildx build --platform linux/amd64 -t aitutor-frontend ./frontend
```

`VITE_API_URL` is compiled into the frontend bundle at build time, so changing
the API location means rebuilding that image, not restarting it.

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill in provider credentials as needed.
Local state (uploads, vector store, SQLite DB, exports) lives in `data/` and is gitignored.
