from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    anthropic_api_key: str
    serper_api_key: str = ""
    resend_api_key: str = ""
    redis_url: str = "redis://localhost:6379"
    app_env: str = "development"
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"


settings = Settings()
