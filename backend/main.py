from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import build_router
from config import settings
from embeddings.chroma_store import ChromaStore
from embeddings.embedder import Embedder
from llm.factory import LLMFactory
from parser.tree_sitter_parser import TreeSitterParser
from retrieval.retriever import Retriever
from services.chat_service import ChatService
from services.file_intelligence_service import FileIntelligenceService
from services.file_tree_service import FileTreeService
from services.indexing_service import IndexingService
from services.repository_service import RepositoryService
from services.state_service import StateService
from services.summary_service import SummaryService

app = FastAPI(title="RepoMind AI Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repos_root = Path(settings.repos_path)
repository_service = RepositoryService(repos_root=repos_root)
parser = TreeSitterParser(max_chunk_size=settings.max_chunk_size)
embedder = Embedder()
store = ChromaStore(persist_path=settings.chroma_path)
indexing_service = IndexingService(parser=parser, embedder=embedder, store=store)
retriever = Retriever(embedder=embedder, store=store)
llm_provider = LLMFactory.create_default_provider()
chat_service = ChatService(retriever=retriever, llm_provider=llm_provider)
summary_service = SummaryService(llm_provider=llm_provider)
state_service = StateService(state_path=settings.state_path)
file_tree_service = FileTreeService()
file_intelligence_service = FileIntelligenceService(
    file_tree_service=file_tree_service,
    retriever=retriever,
    llm_provider=llm_provider,
)

app.include_router(
    build_router(
        repository_service=repository_service,
        indexing_service=indexing_service,
        chat_service=chat_service,
        summary_service=summary_service,
        state_service=state_service,
        file_tree_service=file_tree_service,
        file_intelligence_service=file_intelligence_service,
    )
)
