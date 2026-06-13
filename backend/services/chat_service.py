from llm.base import LLMProvider
from retrieval.retriever import Retriever


class ChatService:
    def __init__(self, retriever: Retriever, llm_provider: LLMProvider) -> None:
        self.retriever = retriever
        self.llm_provider = llm_provider

    async def answer(self, repository_id: str, question: str, file_path: str | None = None, file_context: str | None = None) -> dict:
        contexts = self.retriever.retrieve(repository_id=repository_id, question=question, top_k=6)
        context_text = "\n\n".join(
            f"[File: {item['metadata'].get('file_path')} | Type: {item['metadata'].get('chunk_type')}]\n{item['content']}"
            for item in contexts
        )
        selected_file_block = ""
        if file_path and file_context:
            selected_file_block = (
                f"\n\nSelected file context:\n[File: {file_path}]\n{file_context[:6000]}\n"
            )
        prompt = (
            "You are RepoMind AI, a codebase intelligence assistant.\n"
            "Use only the provided context to answer. If unknown, say so.\n"
            "Always reference file names and explain architecture/API/auth/database impacts clearly.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context_text}"
            f"{selected_file_block}\n\n"
            "Answer:"
        )
        answer = await self.llm_provider.generate(prompt)
        references = [item["metadata"] for item in contexts]
        return {"answer": answer, "references": references}
