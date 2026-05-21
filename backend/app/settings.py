from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/enrollment.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    funnel_config_path: str = "../config/funnel.yaml"
    mail_driver: str = "log"
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mail_from: str = "customercare@legacyenergy.ca"
    public_app_url: str = "http://localhost:5173"

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def resolved_funnel_config(self) -> Path:
        path = Path(self.funnel_config_path)
        if path.is_absolute():
            return path
        # Relative to backend/ working directory
        return (Path(__file__).resolve().parent.parent / path).resolve()


settings = Settings()
