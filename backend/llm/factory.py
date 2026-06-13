from config import settings
from llm.base import LLMProvider
from llm.ollama_provider import OllamaProvider

class LLMFactory:
    @staticmethod
    def create_default_provider() -> LLMProvider:
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)
