import chromadb


class ChromaStore:
    def __init__(self, persist_path: str) -> None:
        self.client = chromadb.PersistentClient(path=persist_path)

    def _collection_name(self, repository_id: str) -> str:
        return f"repo_{repository_id}"

    def index_chunks(self, repository_id: str, chunks: list[dict], vectors: list[list[float]]) -> int:
        collection = self.client.get_or_create_collection(name=self._collection_name(repository_id))
        ids = [f"{repository_id}_{i}" for i in range(len(chunks))]
        docs = [chunk["content"] for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata = {
                "file_path": chunk["file_path"],
                "language": chunk["language"],
                "chunk_type": chunk["chunk_type"],
                "name": chunk["name"],
            }
            if chunk.get("entity_type"):
                metadata["entity_type"] = chunk["entity_type"]
            metadatas.append(metadata)
        collection.upsert(ids=ids, documents=docs, embeddings=vectors, metadatas=metadatas)
        return len(ids)

    def query(self, repository_id: str, vector: list[float], top_k: int = 6) -> list[dict]:
        collection = self.client.get_or_create_collection(name=self._collection_name(repository_id))
        result = collection.query(query_embeddings=[vector], n_results=top_k)
        if not result["documents"] or not result["documents"][0]:
            return []
        rows = []
        for i, text in enumerate(result["documents"][0]):
            rows.append(
                {
                    "content": text,
                    "metadata": result["metadatas"][0][i],
                    "distance": result["distances"][0][i] if result.get("distances") else None,
                }
            )
        return rows
