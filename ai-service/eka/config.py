"""
EKA Configuration — Pydantic Settings v2
Reads from environment variables and .env file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ROOT_DIR / ".env", _BASE_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: Literal["auto", "groq", "ollama", "offline"] = Field(
        default="auto", alias="LLM_PROVIDER"
    )
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY", repr=False)
    groq_model: str = Field(
        default="llama-3.3-70b-versatile", alias="GROQ_MODEL"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(
        default="llama3.2", alias="OLLAMA_MODEL"
    )
    llm_timeout: float = Field(default=20.0, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")

    # ── Embeddings ────────────────────────────────────────────────────────────
    embeddings: Literal["hashing", "fastembed"] = Field(
        default="hashing", alias="EMBEDDINGS"
    )

    # ── Thresholds ────────────────────────────────────────────────────────────
    t_match: float = Field(default=0.85, alias="T_MATCH")
    t_partial: float = Field(default=0.60, alias="T_PARTIAL")

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token: str = Field(default="", alias="GITHUB_TOKEN", repr=False)
    # Comma-separated: acme=owner/repo,globex=owner/repo2
    github_repos: str = Field(default="", alias="GITHUB_REPOS")

    # ── Slack ─────────────────────────────────────────────────────────────────
    slack_webhook_url: str = Field(default="", alias="SLACK_WEBHOOK_URL", repr=False)

    # ── Security ──────────────────────────────────────────────────────────────
    webhook_secret: str = Field(default="changeme-webhook", alias="WEBHOOK_SECRET", repr=False)
    jwt_secret: str = Field(default="changeme-dev-only", alias="JWT_SECRET", repr=False)

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///./eka.db", alias="DATABASE_URL"
    )

    # ── Environment ───────────────────────────────────────────────────────────
    env: Literal["dev", "staging", "prod"] = Field(default="dev", alias="ENV")

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8001, alias="CHROMA_PORT")

    # ── Derived helpers ───────────────────────────────────────────────────────
    @field_validator("t_match", "t_partial", mode="before")
    @classmethod
    def _clamp_threshold(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    def get_github_repos(self) -> dict[str, str]:
        """Parse GITHUB_REPOS env string into {tenant: owner/repo}."""
        result: dict[str, str] = {}
        for entry in self.github_repos.split(","):
            entry = entry.strip()
            if "=" in entry:
                tenant, repo = entry.split("=", 1)
                result[tenant.strip()] = repo.strip()
        return result

    def chroma_url(self) -> str:
        return f"http://{self.chroma_host}:{self.chroma_port}"


# Singleton — import this everywhere
settings = Settings()

def get_settings() -> Settings:
    return settings
