"""
Configuration management for the multi-agent market research system.
Loads environment variables and provides centralized configuration access.
"""

import os
import json
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Gemini Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-pro"
    # LangSmith Configuration
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "market-research-agent"
    langchain_tracing_v2: bool = True
    langchain_endpoint: str = "https://api.smith.langchain.com"
    
    # Application Configuration
    app_env: str = "development"
    log_level: str = "INFO"
    
    # Frontend Configuration
    frontend_url: str = "http://localhost:5173"
    
    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Storage Directories
    reports_dir: str = "./data/reports"
    research_notes_dir: str = "./data/research_notes"
    
    # Vector Store Configuration
    vector_store_type: str = "chromadb"
    vector_store_path: str = "./data/vector_store"
    
    # API Configuration
    max_tokens_per_request: int = 100000
    request_timeout: int = 300
    
    model_config = SettingsConfigDict(
        # Allow `.env` either at repo root (next to `src/`) or inside `src/backend/`.
        # This avoids startup failures when running from different working directories.
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.reports_dir,
            self.research_notes_dir,
            self.vector_store_path,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# #region agent log
def _agent_debug_log(hypothesis_id: str, location: str, message: str, data: dict):
    """Write a single NDJSON debug log line (no secrets)."""
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": os.getenv("AGENT_RUN_ID", "repro-1"),
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(__import__("time").time() * 1000),
        }
        log_path = "/Users/vikaskundalpady/Hackathons/WestBay/codebase/agentic-hackathon-westbay/.cursor/debug.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        # Never break app startup because of debug logging.
        pass


_agent_debug_log(
    "H1",
    "src/backend/config.py:pre-settings",
    "Config module import: checking env/.env presence",
    {
        "cwd": os.getcwd(),
        "env_file_relative": ".env",
        "env_file_exists_cwd": Path(".env").exists(),
        "env_file_backend_path": str(BACKEND_DIR / ".env"),
        "env_file_backend_exists": (BACKEND_DIR / ".env").exists(),
        "env_file_repo_root_path": str(REPO_ROOT / ".env"),
        "env_file_repo_root_exists": (REPO_ROOT / ".env").exists(),
        "has_env_GEMINI_API_KEY": os.getenv("GEMINI_API_KEY") is not None,
        "has_env_gemini_api_key": os.getenv("gemini_api_key") is not None,
    },
)
# #endregion

# Global settings instance
try:
    settings = Settings()
    # #region agent log
    _agent_debug_log(
        "H2",
        "src/backend/config.py:settings-ok",
        "Settings instantiated successfully",
        {
            "app_env": getattr(settings, "app_env", None),
            "gemini_api_key_present": bool(getattr(settings, "gemini_api_key", "")),
        },
    )
    # #endregion
except ValidationError as e:
    # #region agent log
    _agent_debug_log(
        "H3",
        "src/backend/config.py:settings-validation-error",
        "Settings validation failed",
        {
            "error_count": len(getattr(e, "errors", lambda: [])()),
            "missing_fields": [
                err.get("loc", [None])[0]
                for err in getattr(e, "errors", lambda: [])()
                if err.get("type") == "missing"
            ],
        },
    )
    # #endregion
    raise

# Create necessary directories on module import
settings.create_directories()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_prompts_dir() -> Path:
    """Get the prompts directory path."""
    return get_project_root() / "prompts"

