from pathlib import Path

from git import Repo


def clone_repository(url: str, destination: Path) -> None:
    Repo.clone_from(url, destination)
