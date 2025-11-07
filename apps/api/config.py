"""
環境変数と設定を管理するモジュール

Pydantic Settingsを使用して環境変数を型安全に管理します。
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# プロジェクトルートディレクトリを取得（apps/api から2階層上）
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


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

    # CORS設定
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# グローバル設定インスタンス
settings = Settings()
