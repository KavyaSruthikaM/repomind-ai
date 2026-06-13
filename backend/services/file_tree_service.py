from __future__ import annotations

from pathlib import Path

IGNORED_DIRS = {"node_modules", "dist", "build", ".git", "venv", "__pycache__", ".next"}
IGNORED_FILES = {".env"}
IGNORED_PATTERNS = {"secrets", "credentials"}
MAX_PREVIEW_BYTES = 80_000
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".json": "json",
    ".md": "markdown",
    ".css": "css",
    ".html": "html",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".sql": "sql",
    ".sh": "shell",
}


class FileTreeService:
    def build_tree(self, repo_path: Path) -> list[dict]:
        repo_path = repo_path.resolve()
        return self._walk_directory(repo_path, repo_path)

    def get_file_content(self, repo_path: Path, rel_path: str) -> dict:
        target = self._resolve_safe_path(repo_path, rel_path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {rel_path}")

        raw = target.read_bytes()
        truncated = len(raw) > MAX_PREVIEW_BYTES
        preview_bytes = raw[:MAX_PREVIEW_BYTES]
        content = preview_bytes.decode("utf-8", errors="replace")
        line_count = content.count("\n") + (1 if content else 0)

        return {
            "path": rel_path.replace("\\", "/"),
            "name": target.name,
            "language": self._detect_language(target),
            "size_bytes": len(raw),
            "line_count": line_count,
            "content": content,
            "truncated": truncated,
        }

    def _walk_directory(self, repo_path: Path, current: Path) -> list[dict]:
        nodes: list[dict] = []
        entries = sorted(
            [p for p in current.iterdir() if p.name not in IGNORED_DIRS],
            key=lambda p: (p.is_file(), p.name.lower()),
        )

        for entry in entries:
            rel_path = str(entry.relative_to(repo_path)).replace("\\", "/")
            if entry.is_dir():
                children = self._walk_directory(repo_path, entry)
                nodes.append(
                    {
                        "name": entry.name,
                        "path": rel_path,
                        "type": "folder",
                        "children": children,
                    }
                )
                continue

            if self._should_ignore_file(entry):
                continue

            nodes.append(
                {
                    "name": entry.name,
                    "path": rel_path,
                    "type": "file",
                    "language": self._detect_language(entry),
                }
            )
        return nodes

    def _should_ignore_file(self, path: Path) -> bool:
        lower = path.name.lower()
        if path.name in IGNORED_FILES or any(token in lower for token in IGNORED_PATTERNS):
            return True
        return False

    def _detect_language(self, path: Path) -> str | None:
        return LANGUAGE_MAP.get(path.suffix.lower())

    def _resolve_safe_path(self, repo_path: Path, rel_path: str) -> Path:
        repo_path = repo_path.resolve()
        normalized = rel_path.strip().lstrip("/").replace("\\", "/")
        target = (repo_path / normalized).resolve()
        if target != repo_path and repo_path not in target.parents:
            raise ValueError("Invalid file path")
        return target
