from __future__ import annotations

import re
from pathlib import Path

from llm.base import LLMProvider
from retrieval.retriever import Retriever
from services.file_tree_service import FileTreeService

PYTHON_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
JS_IMPORT_RE = re.compile(
    r"(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\))",
    re.MULTILINE,
)
LAYER_FOLDER_HINTS: dict[str, tuple[str, ...]] = {
    "middleware": ("middleware", "middlewares"),
    "controller": ("controllers", "controller"),
    "service": ("services", "service"),
    "model": ("models", "model", "schemas", "entities"),
    "route": ("routes", "routers", "api", "endpoints"),
    "database": ("db", "database", "databases", "prisma", "migrations", "repositories"),
}


class FileIntelligenceService:
    def __init__(
        self,
        file_tree_service: FileTreeService,
        retriever: Retriever,
        llm_provider: LLMProvider,
    ) -> None:
        self.file_tree_service = file_tree_service
        self.retriever = retriever
        self.llm_provider = llm_provider

    async def analyze(
        self,
        repository_id: str,
        repo_path: Path,
        rel_path: str,
        indexed_files: list[str],
    ) -> dict:
        file_payload = self.file_tree_service.get_file_content(repo_path, rel_path)
        imports = self._extract_imports(repo_path, rel_path, file_payload["content"])
        architectural_role = self._infer_architectural_role(rel_path)

        retrieval_query = (
            f"Explain the purpose and responsibilities of file {rel_path}. "
            f"Include related modules, API usage, and architecture role."
        )
        contexts = self.retriever.retrieve(repository_id=repository_id, question=retrieval_query, top_k=8)
        related_modules = self._related_modules(rel_path, imports, indexed_files, contexts)
        context_text = "\n\n".join(
            f"[File: {item['metadata'].get('file_path')} | Type: {item['metadata'].get('chunk_type')}]\n{item['content']}"
            for item in contexts
        )
        prompt = (
            "You are RepoMind AI file intelligence.\n"
            "Explain the selected file's purpose using only provided context.\n"
            "Return a concise explanation with: purpose, architectural role, key behaviors, and how it connects to other modules.\n"
            "If uncertain, state assumptions clearly.\n\n"
            f"Selected file: {rel_path}\n"
            f"Detected language: {file_payload.get('language')}\n"
            f"Inferred architectural role: {architectural_role}\n"
            f"Imports/dependencies: {', '.join(imports[:20]) or 'none detected'}\n"
            f"Related modules: {', '.join([m['path'] for m in related_modules[:10]]) or 'none detected'}\n\n"
            f"File preview:\n{file_payload['content'][:5000]}\n\n"
            f"Retrieved repository context:\n{context_text}\n\n"
            "Explanation:"
        )
        explanation = await self.llm_provider.generate(prompt)
        references = [item["metadata"] for item in contexts]

        return {
            "file": file_payload,
            "explanation": explanation,
            "architectural_role": architectural_role,
            "imports": imports,
            "related_modules": related_modules,
            "references": references,
        }

    def _extract_imports(self, repo_path: Path, rel_path: str, content: str) -> list[str]:
        imports: set[str] = set()
        for match in PYTHON_IMPORT_RE.findall(content):
            mod = match[0] or match[1]
            if mod:
                imports.add(mod)
        file_path = repo_path / rel_path
        for match in JS_IMPORT_RE.findall(content):
            mod = match[0] or match[1]
            if mod.startswith("."):
                resolved = (file_path.parent / mod).resolve()
                try:
                    rel_target = str(resolved.relative_to(repo_path.resolve())).replace("\\", "/")
                    imports.add(rel_target)
                except ValueError:
                    imports.add(mod)
            else:
                imports.add(mod)
        return sorted(imports)

    def _infer_architectural_role(self, rel_path: str) -> str:
        lower = rel_path.lower().replace("\\", "/")
        for layer, hints in LAYER_FOLDER_HINTS.items():
            if any(f"/{hint}/" in lower or lower.startswith(f"{hint}/") for hint in hints):
                return layer
        stem = Path(rel_path).stem.lower()
        if "middleware" in stem:
            return "middleware"
        if "route" in stem or "router" in stem:
            return "route"
        if stem in {"index", "main", "app"}:
            return "entrypoint"
        return "module"

    def _related_modules(
        self,
        rel_path: str,
        imports: list[str],
        indexed_files: list[str],
        contexts: list[dict],
    ) -> list[dict[str, str]]:
        related: dict[str, dict[str, str]] = {}
        normalized_indexed = [f.replace("\\", "/") for f in indexed_files]

        for item in contexts:
            meta = item.get("metadata", {})
            file_path = str(meta.get("file_path", "")).replace("\\", "/")
            if not file_path or file_path == rel_path:
                continue
            related[file_path] = {
                "path": file_path,
                "name": Path(file_path).name,
                "reason": "Semantically related via repository embeddings",
            }

        for imp in imports:
            candidates = [f for f in normalized_indexed if imp in f or Path(f).stem == Path(imp).stem]
            for candidate in candidates[:3]:
                if candidate == rel_path:
                    continue
                related[candidate] = {
                    "path": candidate,
                    "name": Path(candidate).name,
                    "reason": "Referenced by import dependency",
                }

        return list(related.values())[:12]
