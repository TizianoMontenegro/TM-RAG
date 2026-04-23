from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    All values can be overridden via a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- FastAPI ---
    app_name: str = "TM Airlines RAG Service"
    app_version: str = "0.1.0"
    debug: bool = False
    allowed_origins: list[str] = ["*"]

    # --- PostgreSQL / pgvector ---
    database_url: str
    pgvector_collection_name: str = "tm_airlines_docs"

    # --- NVIDIA AI Endpoints ---
    nvidia_api_key: str
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_llm_model: str = "meta/llama-3.1-70b-instruct"
    nvidia_embedding_model: str = "nvidia/nv-embedqa-e5-v5"
    nvidia_max_tokens: int = 1024
    nvidia_temperature: float = 0.2

    # --- Logging ---
    log_level: str = "INFO"
    log_format: str = "json"


settings = Settings()
