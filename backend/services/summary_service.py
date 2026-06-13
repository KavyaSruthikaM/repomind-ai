from pathlib import Path

from llm.base import LLMProvider
from services.architecture_analyzer import ArchitectureAnalyzer

class SummaryService:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider
        self.analyzer = ArchitectureAnalyzer()

    async def summarize(self, repository_id: str, repo_path: Path, files: list[str]) -> dict:
        architecture = self.analyzer.analyze(repo_path=repo_path, files=files)

        top_files = "\n".join(files[:80])
        routes_text = "\n".join(architecture["api_routes"][:20]) or "No explicit routes detected."
        modules_text = "\n".join(
            [f"- {m['module']}: {m['responsibility']}" for m in architecture["major_modules"][:20]]
        )
        tech_text = ", ".join(architecture["technologies"]) or "Unknown"
        deps_text = "\n".join(architecture["dependency_relationships"][:15])
        prompt = (
            "Summarize this repository architecture in a concise but practical way.\n"
            "Use only the provided structure metadata. Explain actual modules, routes, services, "
            "database layers, and dependency relationships detected in this repository.\n"
            f"Repository ID: {repository_id}\n"
            f"Root Path: {repo_path}\n"
            f"Directories:\n{', '.join(architecture['directories'][:30])}\n"
            f"File List:\n{top_files}\n\n"
            f"Detected API Routes:\n{routes_text}\n"
            f"Detected Major Modules:\n{modules_text}\n"
            f"Detected Technologies:\n{tech_text}\n"
            f"Detected Dependencies:\n{deps_text}\n"
            "\nProvide a high-level architecture overview and request/data flow."
        )
        summary_text = await self.llm_provider.generate(prompt)
        return {"summary": summary_text, "architecture": architecture}
