"""
pytestの共通フィクスチャとテストユーティリティ

テスト実行時に自動的に読み込まれます。
"""
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock
from dotenv import load_dotenv

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み（RLSテスト用に実際の環境変数が必要）
load_dotenv(project_root / ".env")

import pytest
from fastapi.testclient import TestClient
from supabase import Client

# 環境変数設定（テスト用のダミー値）
# ただし、実際のSupabase環境変数がある場合はそれを優先
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
if not os.getenv("SUPABASE_ANON_KEY"):
    os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
if not os.getenv("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test-openai-key"

from main import app
from database import get_supabase_client
from middleware.auth import get_current_user_id


@pytest.fixture
def test_user_id() -> str:
    """テスト用のユーザーID"""
    return "test-user-123"


@pytest.fixture
def mock_supabase_client() -> Generator[MagicMock, None, None]:
    """
    Supabaseクライアントのモック

    各テストで具体的なレスポンスを設定できます。

    Examples:
        >>> def test_example(mock_supabase_client):
        ...     mock_supabase_client.table().select().execute.return_value.data = [{"id": "1"}]
    """
    mock_client = MagicMock(spec=Client)

    # デフォルトのチェーンメソッドモック
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # executeメソッドのレスポンスモック
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0
    mock_table.select.return_value.execute.return_value = mock_response
    mock_table.insert.return_value.execute.return_value = mock_response
    mock_table.update.return_value.execute.return_value = mock_response
    mock_table.delete.return_value.execute.return_value = mock_response

    yield mock_client


@pytest.fixture
def client(mock_supabase_client: MagicMock, test_user_id: str) -> Generator[TestClient, None, None]:
    """
    FastAPIテストクライアント

    認証とSupabaseクライアントをモックします。
    """
    # 依存性のオーバーライド
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_client
    app.dependency_overrides[get_current_user_id] = lambda: test_user_id

    with TestClient(app) as test_client:
        yield test_client

    # クリーンアップ
    app.dependency_overrides.clear()


@pytest.fixture
def mock_rfp_data() -> dict:
    """テスト用のRFPデータ"""
    return {
        "id": "rfp-test-123",
        "external_id": "ext-rfp-123",
        "title": "テストRFP案件",
        "issuing_org": "テスト組織",
        "description": "これはテスト用のRFP案件です。",
        "budget": 10000000,
        "region": "東京都",
        "deadline": "2025-12-31",
        "url": "https://example.com/rfp/123",
        "external_doc_urls": ["https://example.com/doc1.pdf"],
        "embedding": [0.1] * 1536,  # ダミーのembedding
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "fetched_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_bookmark_data(test_user_id: str) -> dict:
    """テスト用のブックマークデータ"""
    return {
        "id": "bookmark-test-123",
        "user_id": test_user_id,
        "rfp_id": "rfp-test-123",
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_company_data(test_user_id: str) -> dict:
    """テスト用の会社データ"""
    return {
        "id": "company-test-123",
        "user_id": test_user_id,
        "name": "テスト株式会社",
        "description": "テスト用の会社です。",
        "business_types": ["システム開発", "コンサルティング"],
        "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL"],
        "regions": ["東京都", "神奈川県"],
        "budget_min": 5000000,
        "budget_max": 50000000,
        "must_requirements": ["実績あり", "ISO認証"],
        "embedding": [0.2] * 1536,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_match_snapshot_data() -> dict:
    """テスト用のマッチングスナップショットデータ"""
    return {
        "company_id": "company-test-123",
        "rfp_id": "rfp-test-123",
        "match_score": 85,
        "must_requirements_ok": True,
        "budget_match_ok": True,
        "region_match_ok": True,
        "match_factors": {
            "semantic_similarity": 0.85,
            "budget_match": 1.0,
            "region_match": 1.0,
        },
        "summary_points": [
            "予算条件が適合しています",
            "地域条件が適合しています",
            "高いセマンティック類似度があります",
        ],
        "updated_at": "2025-01-01T00:00:00Z",
    }


# ============================================================================
# RLSテスト用フィクスチャのインポート
# ============================================================================
# pytest_pluginsを使用してフィクスチャモジュールを登録
pytest_plugins = [
    "tests.fixtures.rls_fixtures",
]
