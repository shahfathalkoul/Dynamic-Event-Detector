"""Central platform configuration loaded from environment.

All service settings are centralized here so that containers,
CI pipelines, and local dev environments all use the same source
of truth — the environment.
"""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class PlatformSettings(BaseSettings):
    """Root configuration for the News Intelligence Platform."""

    model_config = {"env_prefix": "", "case_sensitive": False, "env_file": ".env"}

    # ── Application ──────────────────────────────────────────────────
    app_name: str = "News Intelligence Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", description="development | staging | production")
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: str = Field(default="http://localhost:3000", description="Comma-separated allowed origins")

    # ── Database ─────────────────────────────────────────────────────
    database_url: str = "sqlite:///data/news_intelligence.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # ── Redis ────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 3600

    # ── Qdrant ───────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_timeout: float = 30.0

    # ── LLM ──────────────────────────────────────────────────────────
    llm_model: str = "gpt-4o-mini"
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000

    # ── Embeddings ───────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str | None = None

    # ── Auth ─────────────────────────────────────────────────────────
    clerk_secret_key: SecretStr | None = None
    clerk_publishable_key: str | None = None
    jwt_secret: SecretStr | None = None
    api_key_header: str = "X-API-Key"

    # ── Observability ────────────────────────────────────────────────
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "news-intelligence-api"
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "news-intelligence"

    # ── Celery ───────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── Rate limiting ────────────────────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
