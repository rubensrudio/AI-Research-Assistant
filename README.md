# AI Research Assistant

API de pesquisa assistida por IA com RAG local — documentos indexados via Qdrant, respondidos por modelos de linguagem locais (LM Studio), com autenticação JWT e persistência em SQLite.

## Stack

| Layer        | Technology                            |
|--------------|---------------------------------------|
| **API**      | FastAPI + Uvicorn (Python 3.11)       |
| **RAG**      | Qdrant (vectordb) + Nomic Embed       |
| **LLM**      | LM Studio local (Llama 3.1 8B)         |
| **Auth**     | JWT (python-jose) + bcrypt           |
| **DB**       | SQLite + SQLAlchemy 2.0               |
| **Infra**    | Docker Compose                        |
| **Testing**  | pytest + httpx                        |

## Features

- **Autenticação** — Registro, login e refresh JWT (access + refresh tokens)
- **Projetos** — CRUD com ownership por usuário
- **Documentos** — Upload (multipart), listagem por projeto e deletção
- **Indexação RAG** — Chunking semântico + embedding via Nomic Embed → Qdrant
- **Busca RAG** — Query por similaridade com contexto recuperado, respondida pelo LLM local
- **LLM direto** — Chat endpoint smoke test contra modelo local
- **Health check** — `/health`

## Quick Start

```bash
# 1. Subir Qdrant + API
docker compose -f infra/docker-compose.yml up -d

# 2. Verificar
curl http://localhost:8000/health

# 3. API docs
open http://localhost:8000/docs
```

### Requisitos para LLM local

LM Studio rodando em `http://localhost:1234` com os modelos:
- **Chat:** `dolphin3.0-llama3.1-8b`
- **Embedding:** `text-embedding-nomic-embed-text-v1.5`

### Variáveis de ambiente

| Variável                   | Default                                 |
|----------------------------|-----------------------------------------|
| `APP_ENV`                  | `dev`                                   |
| `SQLITE_PATH`              | `./app.db`                              |
| `QDRANT_HOST`              | `localhost`                             |
| `QDRANT_PORT`              | `6333`                                  |
| `JWT_SECRET`               | — (obrigatório)                         |
| `LMSTUDIO_BASE_URL`        | `http://localhost:1234/v1`              |
| `LMSTUDIO_API_KEY`         | `lm-studio`                             |
| `LMSTUDIO_CHAT_MODEL`      | `dolphin3.0-llama3.1-8b`                |
| `LMSTUDIO_EMBED_MODEL`     | `text-embedding-nomic-embed-text-v1.5`  |

## Estrutura

```
AI-Research-Assistant/
├── apps/
│   └── backend-api/
│       ├── app/
│       │   ├── api/routes/        # Endpoints (auth, projects, documents, rag, llm, health)
│       │   ├── auth.py            # JWT utilities
│       │   ├── core/config.py     # Settings via pydantic-settings
│       │   ├── db/                # SQLAlchemy models + engine
│       │   ├── main.py            # FastAPI app factory
│       │   ├── schemas.py         # Pydantic request/response models
│       │   └── services/          # Qdrant, chunking, indexing, LM Studio client
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
└── infra/
    └── docker-compose.yml
```

## Running tests

```bash
cd apps/backend-api
pytest -v
```

## Architecture

```
User → FastAPI → JWT Auth → SQLite (users, projects, documents)
                     ↓
              Qdrant (vector embeddings)
                     ↓
              LM Studio (local LLM inference)
```
