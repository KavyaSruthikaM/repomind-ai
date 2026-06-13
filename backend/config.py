from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    chroma_path: str = "../chroma_db"
    repos_path: str = "../repos"
    state_path: str = "../state.json"
    max_chunk_size: int = 2000


settings = Settings()
