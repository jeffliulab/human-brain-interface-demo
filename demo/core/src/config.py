from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LLM_PROVIDER: str = "deepseek"
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL_FAST: str = "deepseek-chat"
    LLM_MODEL_QUALITY: str = "deepseek-chat"
    RAND_SEED: str = "demo-2026-04-20"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def api_key(self) -> str:
        return self.DEEPSEEK_API_KEY or self.OPENAI_API_KEY

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
