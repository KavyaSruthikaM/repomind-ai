import json
from pathlib import Path
from typing import Any


class StateService:
    def __init__(self, state_path: Path | str | None = None) -> None:
        self._state: dict[str, dict[str, Any]] = {}
        self.state_path = Path(state_path) if state_path else None
        self._load()

    def _load(self) -> None:
        if self.state_path and self.state_path.exists():
            try:
                with open(self.state_path, "r") as f:
                    self._state = json.load(f)
            except Exception:
                self._state = {}

    def _save(self) -> None:
        if self.state_path:
            try:
                with open(self.state_path, "w") as f:
                    json.dump(self._state, f, indent=4)
            except Exception:
                pass

    def set_repo(
        self,
        repository_id: str,
        repo_path: Path,
        files: list[str],
        summary: str | None = None,
        architecture: dict[str, Any] | None = None,
    ) -> None:
        self._state[repository_id] = {
            "repo_path": str(repo_path),
            "files": files,
            "summary": summary or "",
            "architecture": architecture or {},
        }
        self._save()

    def get_repo(self, repository_id: str) -> dict[str, Any] | None:
        return self._state.get(repository_id)

    def get_all_ids(self) -> list[str]:
        return list(self._state.keys())

    def set_summary(self, repository_id: str, summary: str, architecture: dict[str, Any] | None = None) -> None:
        if repository_id in self._state:
            self._state[repository_id]["summary"] = summary
            if architecture is not None:
                self._state[repository_id]["architecture"] = architecture
            self._save()
