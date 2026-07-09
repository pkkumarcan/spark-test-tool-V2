from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SPARK_"}

    # Gateway
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Postgres
    postgres_url: str = "postgresql://spark:spark@localhost:5432/spark"

    # LLM
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "qwen3:8b"

    # ComfyUI
    comfyui_url: str = "http://localhost:8188"

    # Remote GPU nodes (optional)
    node_b_url: str = ""

    # Security
    api_key: str = ""
    trust_proxy_headers: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3002"]
    max_body_size: int = 10 * 1024 * 1024  # 10MB

    # Observability
    otel_enabled: bool = True
    langfuse_url: str = ""
    langfuse_key: str = ""


settings = Settings()

if not settings.debug and "spark:spark@" in settings.postgres_url:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.warning(
        "SPARK_POSTGRES_URL contains default 'spark:spark' credentials. "
        "Change them before deploying to production."
    )
