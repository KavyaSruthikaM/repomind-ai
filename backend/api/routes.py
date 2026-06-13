from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from schemas import (
    ChatRequest,
    ChatResponse,
    FileContentResponse,
    FileIntelligenceResponse,
    FileNode,
    FileTreeResponse,
    FilesResponse,
    SummaryResponse,
    UploadRepoRequest,
    UploadResponse,
)
from services.chat_service import ChatService
from services.file_intelligence_service import FileIntelligenceService
from services.file_tree_service import FileTreeService
from services.indexing_service import IndexingService
from services.repository_service import RepositoryService
from services.state_service import StateService
from services.summary_service import SummaryService


def build_router(
    repository_service: RepositoryService,
    indexing_service: IndexingService,
    chat_service: ChatService,
    summary_service: SummaryService,
    state_service: StateService,
    file_tree_service: FileTreeService,
    file_intelligence_service: FileIntelligenceService,
) -> APIRouter:
    router = APIRouter()

    @router.post("/upload-repo", response_model=UploadResponse)
    async def upload_repo(payload: UploadRepoRequest) -> UploadResponse:
        try:
            repository_id, repo_path = repository_service.clone_repo(payload.repo_url)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {exc}") from exc

        index_data = indexing_service.index_repository(repository_id, repo_path)
        print(f"DEBUG: Storing repository_id: {repository_id}")
        state_service.set_repo(repository_id, repo_path, index_data["files"])
        print(f"DEBUG: Current StateService IDs: {state_service.get_all_ids()}")
        return UploadResponse(repository_id=repository_id, name=Path(repo_path).name, file_count=len(index_data["files"]))

    @router.post("/upload-zip", response_model=UploadResponse)
    async def upload_zip(file: UploadFile = File(...)) -> UploadResponse:
        if not file.filename or not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only .zip files are supported")

        try:
            repository_id, repo_path = await repository_service.extract_zip(file)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to extract zip: {exc}") from exc

        index_data = indexing_service.index_repository(repository_id, repo_path)
        print(f"DEBUG: Storing repository_id (zip): {repository_id}")
        state_service.set_repo(repository_id, repo_path, index_data["files"])
        print(f"DEBUG: Current StateService IDs: {state_service.get_all_ids()}")
        return UploadResponse(repository_id=repository_id, name=file.filename.replace(".zip", ""), file_count=len(index_data["files"]))

    @router.post("/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest) -> ChatResponse:
        print(f"DEBUG: Requesting repository_id: {payload.repository_id}")
        print(f"DEBUG: All stored repository IDs: {state_service.get_all_ids()}")
        state = state_service.get_repo(payload.repository_id)
        if not state:
            print(f"DEBUG: Repository {payload.repository_id} NOT FOUND in state.")
            raise HTTPException(status_code=404, detail="Repository not found. Upload first.")

        file_context = None
        if payload.file_path:
            try:
                file_context = file_tree_service.get_file_content(
                    Path(state["repo_path"]),
                    payload.file_path,
                )["content"]
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Unable to load file context: {exc}") from exc

        data = await chat_service.answer(
            repository_id=payload.repository_id,
            question=payload.question,
            file_path=payload.file_path,
            file_context=file_context,
        )
        return ChatResponse(answer=data["answer"], references=data["references"])

    @router.get("/summary", response_model=SummaryResponse)
    async def get_summary(repository_id: str) -> SummaryResponse:
        state = state_service.get_repo(repository_id)
        if not state:
            raise HTTPException(status_code=404, detail="Repository not found.")

        if not state.get("summary"):
            summary_payload = await summary_service.summarize(
                repository_id=repository_id,
                repo_path=Path(state["repo_path"]),
                files=state.get("files", []),
            )
            state_service.set_summary(
                repository_id,
                summary_payload["summary"],
                architecture=summary_payload["architecture"],
            )
        repo = state_service.get_repo(repository_id)
        return SummaryResponse(
            repository_id=repository_id,
            summary=repo["summary"],
            architecture=repo.get("architecture", {}),
        )

    @router.get("/files", response_model=FilesResponse)
    async def get_files(repository_id: str) -> FilesResponse:
        state = state_service.get_repo(repository_id)
        if not state:
            raise HTTPException(status_code=404, detail="Repository not found.")
        files = [FileNode(path=f) for f in state.get("files", [])]
        return FilesResponse(repository_id=repository_id, files=files)

    @router.get("/files/tree", response_model=FileTreeResponse)
    async def get_file_tree(repository_id: str) -> FileTreeResponse:
        state = state_service.get_repo(repository_id)
        if not state:
            raise HTTPException(status_code=404, detail="Repository not found.")
        tree = file_tree_service.build_tree(Path(state["repo_path"]))
        return FileTreeResponse(repository_id=repository_id, tree=tree)

    @router.get("/files/content", response_model=FileContentResponse)
    async def get_file_content(repository_id: str, path: str) -> FileContentResponse:
        state = state_service.get_repo(repository_id)
        if not state:
            raise HTTPException(status_code=404, detail="Repository not found.")
        try:
            payload = file_tree_service.get_file_content(Path(state["repo_path"]), path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FileContentResponse(**payload)

    @router.get("/files/intelligence", response_model=FileIntelligenceResponse)
    async def get_file_intelligence(repository_id: str, path: str) -> FileIntelligenceResponse:
        state = state_service.get_repo(repository_id)
        if not state:
            raise HTTPException(status_code=404, detail="Repository not found.")
        try:
            payload = await file_intelligence_service.analyze(
                repository_id=repository_id,
                repo_path=Path(state["repo_path"]),
                rel_path=path,
                indexed_files=state.get("files", []),
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FileIntelligenceResponse(**payload)

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return router
