from typing import Any

from pydantic import BaseModel, Field


class UploadRepoRequest(BaseModel):
    repo_url: str


class UploadResponse(BaseModel):
    repository_id: str
    name: str
    file_count: int


class ChatRequest(BaseModel):
    repository_id: str
    question: str = Field(min_length=3)
    file_path: str | None = None


class ChatResponse(BaseModel):
    answer: str
    references: list[dict[str, Any]]


class SummaryResponse(BaseModel):
    repository_id: str
    summary: str
    architecture: dict[str, Any]


class FileNode(BaseModel):
    path: str
    language: str | None = None


class TreeNode(BaseModel):
    name: str
    path: str
    type: str
    language: str | None = None
    children: list["TreeNode"] | None = None


class FileTreeResponse(BaseModel):
    repository_id: str
    tree: list[TreeNode]


class FileContentResponse(BaseModel):
    path: str
    name: str
    language: str | None = None
    size_bytes: int
    line_count: int
    content: str
    truncated: bool


class RelatedModule(BaseModel):
    path: str
    name: str
    reason: str


class FileIntelligenceResponse(BaseModel):
    file: FileContentResponse
    explanation: str
    architectural_role: str
    imports: list[str]
    related_modules: list[RelatedModule]
    references: list[dict[str, Any]]


class FilesResponse(BaseModel):
    repository_id: str
    files: list[FileNode]


TreeNode.model_rebuild()
