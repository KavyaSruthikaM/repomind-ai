import shutil
import tempfile
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from git import Repo

IGNORED_DIRS = {"node_modules", "dist", "build", ".git", "venv", "__pycache__"}
IGNORED_FILES = {".env"}
IGNORED_PATTERNS = {"secrets", "credentials"}


class RepositoryService:
    def __init__(self, repos_root: Path) -> None:
        self.repos_root = repos_root
        self.repos_root.mkdir(parents=True, exist_ok=True)

    def _sanitize_repo(self, target_path: Path) -> None:
        for path in target_path.rglob("*"):
            if path.is_dir() and path.name in IGNORED_DIRS:
                shutil.rmtree(path, ignore_errors=True)
                continue

            if path.is_file():
                lower = path.name.lower()
                if path.name in IGNORED_FILES or any(token in lower for token in IGNORED_PATTERNS):
                    path.unlink(missing_ok=True)

    def clone_repo(self, repo_url: str) -> tuple[str, Path]:
        repo_id = str(uuid4())
        target_path = self.repos_root / repo_id
        Repo.clone_from(repo_url, target_path)
        self._sanitize_repo(target_path)
        return repo_id, target_path

    async def extract_zip(self, file: UploadFile) -> tuple[str, Path]:
        repo_id = str(uuid4())
        target_path = self.repos_root / repo_id
        target_path.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            content = await file.read()
            tmp.write(content)
            zip_path = Path(tmp.name)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_path)

        zip_path.unlink(missing_ok=True)
        self._sanitize_repo(target_path)
        return repo_id, target_path
