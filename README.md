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

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill in provider credentials as needed.
Local state (uploads, vector store, SQLite DB, exports) lives in `data/` and is gitignored.
