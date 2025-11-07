"""
環境変数と設定を管理するモジュール

Pydantic Settingsを使用して環境変数を型安全に管理します。
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Supabase設定
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # アプリケーション設定
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS設定（文字列またはリストを受け入れる）
    cors_origins: str | list[str] = "http://localhost:3000"

    # OpenAI API設定
    openai_api_key: str

    # KKJ API設定
    kkj_api_url: str = "http://www.kkj.go.jp/api/"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """カンマ区切り文字列をリストに変換"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",  # カレントディレクトリ（apps/api）の.envを読む
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# グローバル設定インスタンス
settings = Settings()
