from pathlib import Path

from embeddings.chroma_store import ChromaStore
from embeddings.embedder import Embedder
from parser.tree_sitter_parser import TreeSitterParser


class IndexingService:
    def __init__(self, parser: TreeSitterParser, embedder: Embedder, store: ChromaStore) -> None:
        self.parser = parser
        self.embedder = embedder
        self.store = store

    def index_repository(self, repository_id: str, repo_path: Path) -> dict:
        result = self.parser.parse_repository(repo_path)
        chunks = result["chunks"]
        routes = result["routes"]
        relationships = result.get("relationships", [])
        
        all_items = chunks + routes
        if not all_items:
            return {"chunk_count": 0, "indexed_count": 0, "files": []}

        vectors = self.embedder.embed([c["content"] for c in all_items])
        indexed_count = self.store.index_chunks(repository_id=repository_id, chunks=all_items, vectors=vectors)
        files = sorted({c["file_path"] for c in all_items})
        return {
            "chunk_count": len(chunks),
            "route_count": len(routes),
            "relationship_count": len(relationships),
            "indexed_count": indexed_count,
            "files": files
        }
