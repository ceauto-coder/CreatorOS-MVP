from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    supabase_url: str
    supabase_service_role_key: str
    creatoros_model: str = "gpt-5.6-luna"
    creatoros_memory_extractor_model: str = "gpt-5.6-luna"
    creatoros_embedding_model: str = "text-embedding-3-small"
    creatoros_memory_top_k: int = 6
    creatoros_memory_min_score: float = 0.35
    creatoros_debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
