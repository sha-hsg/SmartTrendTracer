"""
Central configuration for SmartTrendTracer.

Single place where environment variables are read (arch rule: no os.getenv
outside this module). Import the `settings` singleton:

    from app.config import settings
    settings.marker_service_url

API keys live in ~/.env (loaded by start_stt.sh, and by load_dotenv below for
direct runs). LiteLLM additionally reads the provider keys from the process
environment on its own; this module does not change that.
"""
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    # --- Server -----------------------------------------------------------
    api_host: str = "127.0.0.1"          # local only: the API has no authentication
    backend_port: int = Field(default=8088, validation_alias=AliasChoices("BACKEND_PORT", "API_PORT"))
    cors_origins_raw: str = Field(default="", validation_alias="CORS_ORIGINS")

    # --- MongoDB (app reads MONGODB_URI, standalone scripts historically
    #     MONGODB_URL — both are honored) ---------------------------------
    mongodb_uri: str = Field(default="mongodb://localhost:27017/",
                             validation_alias=AliasChoices("MONGODB_URI", "MONGODB_URL"))
    mongodb_db: str = "smarttrendtracer"
    mongodb_replica_set: Optional[str] = None
    mongodb_app_name: Optional[str] = None
    mongodb_options: str = ""
    mongodb_slow_query_ms: float = 100

    # --- External services -------------------------------------------------
    marker_service_url: str = "http://localhost:8002"
    mineru_service_url: str = "http://localhost:8003"
    grobid_service_url: str = "https://kermitt2-grobid.hf.space"

    # --- Database backup (scheduler job "backup": mongodump, weekly) ----------
    backup_dir: str = Field(default=str(Path.home() / "Backups" / "SmartTrendTracer"),
                            validation_alias="STT_BACKUP_DIR")
    backup_keep: int = 8

    # --- LLM provider keys (status display / embedding clients) -------------
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None

    # --- Twitter / Reddit ---------------------------------------------------
    twitter_bearer_token: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "SmartTrendTracer:v1.0 (by /u/smarttrendtracer)"

    # --- Tweet collector (mode-dependent defaults resolved below) -----------
    basic_account_mode: bool = True
    collection_interval_seconds: Optional[int] = None
    credits_backoff_seconds: int = 3600
    batch_size: Optional[int] = None
    intra_batch_delay_seconds: Optional[float] = None
    inter_batch_delay_seconds: Optional[float] = None
    initial_backoff_seconds: Optional[float] = None
    max_backoff_seconds: float = 900
    per_page_max_results: int = 100
    max_pages_per_account: Optional[int] = None
    max_retry_attempts: int = 3
    use_tiered_priority: bool = True
    use_search_fallback: bool = True

    # --- Book worker --------------------------------------------------------
    book_worker_idle_seconds: float = 5

    @property
    def google_or_gemini_api_key(self) -> Optional[str]:
        return self.google_api_key or self.gemini_api_key

    @property
    def cors_origins(self) -> List[str]:
        if self.cors_origins_raw:
            return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]
        return ["http://localhost:3470", "http://localhost:3000",
                "http://localhost:3001", "http://localhost:3002"]

    @property
    def backend_base_url(self) -> str:
        """Base URL the PDF services use to call back into this backend."""
        return f"http://localhost:{self.backend_port}"

    def collector_value(self, name: str):
        """Tweet-collector setting with its Basic/Pro-mode dependent default."""
        defaults = {
            # name: (basic, pro)
            "collection_interval_seconds": (900, 1800),
            "batch_size": (12, 3),
            "intra_batch_delay_seconds": (2.0, 5.0),
            "inter_batch_delay_seconds": (30.0, 60.0),
            "initial_backoff_seconds": (900.0, 60.0),
            "max_pages_per_account": (1, 5),
        }
        value = getattr(self, name)
        if value is not None:
            return value
        basic, pro = defaults[name]
        return basic if self.basic_account_mode else pro


settings = Settings()



# Backwards-compatible aliases
API_HOST = settings.api_host
API_PORT = settings.backend_port
TWITTER_BEARER_TOKEN = settings.twitter_bearer_token
