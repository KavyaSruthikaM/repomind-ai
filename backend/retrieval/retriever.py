from embeddings.chroma_store import ChromaStore
from embeddings.embedder import Embedder


class Retriever:
    def __init__(self, embedder: Embedder, store: ChromaStore) -> None:
        self.embedder = embedder
        self.store = store

    def retrieve(self, repository_id: str, question: str, top_k: int = 6) -> list[dict]:
        vector = self.embedder.embed([question])[0]
        return self.store.query(repository_id=repository_id, vector=vector, top_k=top_k)
