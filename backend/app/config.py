from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "multiagent"
    app_mode: str = "google"  # mock or google
    database_url: str = "sqlite:///./smileflow.db"
    timezone: str = "Africa/Casablanca"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    openai_api_key: str | None = None

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    llm_timeout_seconds: int = 8

    xai_api_key: str = ""
    grok_base_url: str = "https://api.x.ai/v1"
    grok_model: str = "grok-4.3"
    llm_timeout_seconds: int = 30


    google_credentials_file: str = "./credentials/google_credentials.json"
    google_calendar_token_file: str = "./credentials/token_calendar.json"
    google_gmail_token_file: str = "./credentials/token_gmail.json"
    google_calendar_id: str = "primary"

    email_provider: str = "gmail_api"  # gmail_api, smtp, or mock
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str | None = None

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.backend_cors_origins.split(',') if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
