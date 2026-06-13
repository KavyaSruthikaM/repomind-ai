# RepoMind AI Architecture

## Overview
- **Frontend (`Next.js`)**: auth + dashboard + upload + file explorer + chat.
- **Backend (`FastAPI`)**: repository ingestion, parsing, embeddings, retrieval, and LLM orchestration.
- **RAG pipeline**: Tree-sitter chunking -> sentence-transformers embeddings -> ChromaDB retrieval -> Ollama answer generation.

## Key Backend Modules
- `services/repository_service.py`: clone/extract and sanitize repositories.
- `parser/tree_sitter_parser.py`: metadata-aware structural chunk extraction.
- `embeddings/*`: embedding generation and vector persistence.
- `retrieval/retriever.py`: semantic retrieval by repository scope.
- `llm/*`: provider abstraction with default Ollama implementation.
- `services/chat_service.py`: prompt assembly and answer generation.

## Future-Ready Extension Points
- LLM provider abstraction can add OpenRouter/OpenAI/Groq providers.
- Add graph builders in `services/` for dependency or architecture maps.
- Add local-only mode flag to bypass external network calls and use local models only.
- Add repository lifecycle cleanup scheduler for temporary storage limits.
