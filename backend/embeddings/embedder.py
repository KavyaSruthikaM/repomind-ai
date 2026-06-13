from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()
