from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str

    personal_api_token: str
    demo_api_token: str

    airtable_mcp_url: str = "https://mcp.airtable.com/mcp"
    airtable_personal_pat: str
    airtable_demo_pat: str
    airtable_personal_base_name: str
    airtable_demo_base_name: str
    airtable_expenses_table_name: str = "Expenses"

    cors_allowed_origins: str = Field(default="http://localhost:5173")
    api_port: int = 8000
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins(self) -> list[str]:
        values = [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]
        return values or ["http://localhost:5173"]

    def airtable_pat_for_mode(self, mode: str) -> str:
        return self.airtable_personal_pat if mode == "personal" else self.airtable_demo_pat

    def airtable_base_name_for_mode(self, mode: str) -> str:
        if mode == "personal":
            return self.airtable_personal_base_name
        return self.airtable_demo_base_name


settings = Settings()
