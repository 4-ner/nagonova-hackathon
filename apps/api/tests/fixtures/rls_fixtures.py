"""
RLSポリシーテスト用フィクスチャ

実際のSupabaseデータベースに接続してテストを行います。
"""
import os
import uuid
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta

import pytest
from supabase import create_client, Client
from supabase_auth.types import AuthResponse


class RlsTestUser:
    """
    RLSテストユーザー情報を保持するクラス

    Note: クラス名を'TestUser'から'RlsTestUser'に変更しました。
    Pytestは'Test'で始まるクラスをテストクラスとして認識しようとするため、
    警告を回避するためにクラス名を変更しています。
    """

    def __init__(self, email: str, password: str, user_id: Optional[str] = None, access_token: Optional[str] = None):
        self.email = email
        self.password = password
        self.user_id = user_id
        self.access_token = access_token


@pytest.fixture(scope="session")
def supabase_url() -> str:
    """Supabase URL"""
    url = os.getenv("SUPABASE_URL")
    if not url:
        pytest.skip("SUPABASE_URL環境変数が設定されていません")
    return url


@pytest.fixture(scope="session")
def supabase_anon_key() -> str:
    """Supabase Anon Key"""
    key = os.getenv("SUPABASE_ANON_KEY")
    if not key:
        pytest.skip("SUPABASE_ANON_KEY環境変数が設定されていません")
    return key


@pytest.fixture(scope="session")
def supabase_service_key() -> str:
    """Supabase Service Key"""
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not key:
        pytest.skip("SUPABASE_SERVICE_KEY環境変数が設定されていません")
    return key


@pytest.fixture(scope="function")
def supabase_anon_client(supabase_url: str, supabase_anon_key: str) -> Generator[Client, None, None]:
    """
    Supabase匿名クライアント（RLS適用）

    一般ユーザーとして動作し、RLSポリシーが適用されます。
    """
    client = create_client(supabase_url, supabase_anon_key)
    yield client


@pytest.fixture(scope="function")
def supabase_service_client(supabase_url: str, supabase_service_key: str) -> Generator[Client, None, None]:
    """
    Supabase Service Roleクライアント（RLS無視）

    Service Roleとして動作し、RLSポリシーを無視してすべてのデータにアクセスできます。
    テストデータのセットアップとクリーンアップに使用します。
    """
    client = create_client(supabase_url, supabase_service_key)
    yield client


@pytest.fixture(scope="function")
def test_user_1(supabase_anon_client: Client, supabase_service_client: Client) -> Generator[RlsTestUser, None, None]:
    """
    テストユーザー1

    各テストで使用する主要なテストユーザー。
    テスト実行後に自動的に削除されます。
    """
    # ユニークなメールアドレスを生成（Gmailのエイリアス機能を使用）
    unique_id = str(uuid.uuid4())[:8]
    email = f"rfp-radar-test+user1-{unique_id}@gmail.com"
    password = "test-password-123!Aa"

    user = None
    # Service Roleクライアントで直接ユーザーを作成（メール確認をスキップ）
    try:
        response = supabase_service_client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True  # メール確認済みとしてユーザーを作成
        })

        if not response.user:
            pytest.fail("テストユーザー1の作成に失敗しました")

        user = RlsTestUser(
            email=email,
            password=password,
            user_id=response.user.id,
            access_token=None  # 後でログインして取得
        )

        yield user

    finally:
        # クリーンアップ: Service Roleでユーザーを削除
        if user and user.user_id:
            try:
                # 関連データを削除（カスケード削除が効かない場合に備えて）
                supabase_service_client.table("companies").delete().eq("user_id", user.user_id).execute()
                supabase_service_client.table("bookmarks").delete().eq("user_id", user.user_id).execute()
                supabase_service_client.table("match_snapshots").delete().eq("user_id", user.user_id).execute()

                # ユーザーを削除（Supabase Admin APIを使用）
                supabase_service_client.auth.admin.delete_user(user.user_id)
            except Exception as e:
                print(f"テストユーザー1のクリーンアップに失敗: {e}")


@pytest.fixture(scope="function")
def test_user_2(supabase_anon_client: Client, supabase_service_client: Client) -> Generator[RlsTestUser, None, None]:
    """
    テストユーザー2

    権限テストで「他のユーザー」として使用。
    テスト実行後に自動的に削除されます。
    """
    # ユニークなメールアドレスを生成（Gmailのエイリアス機能を使用）
    unique_id = str(uuid.uuid4())[:8]
    email = f"rfp-radar-test+user2-{unique_id}@gmail.com"
    password = "test-password-456!Aa"

    user = None
    # Service Roleクライアントで直接ユーザーを作成（メール確認をスキップ）
    try:
        response = supabase_service_client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True  # メール確認済みとしてユーザーを作成
        })

        if not response.user:
            pytest.fail("テストユーザー2の作成に失敗しました")

        user = RlsTestUser(
            email=email,
            password=password,
            user_id=response.user.id,
            access_token=None  # 後でログインして取得
        )

        yield user

    finally:
        # クリーンアップ: Service Roleでユーザーを削除
        if user and user.user_id:
            try:
                # 関連データを削除
                supabase_service_client.table("companies").delete().eq("user_id", user.user_id).execute()
                supabase_service_client.table("bookmarks").delete().eq("user_id", user.user_id).execute()
                supabase_service_client.table("match_snapshots").delete().eq("user_id", user.user_id).execute()

                # ユーザーを削除
                supabase_service_client.auth.admin.delete_user(user.user_id)
            except Exception as e:
                print(f"テストユーザー2のクリーンアップに失敗: {e}")


@pytest.fixture(scope="function")
def authenticated_client_1(supabase_url: str, supabase_anon_key: str, test_user_1: RlsTestUser) -> Generator[Client, None, None]:
    """
    テストユーザー1で認証済みのSupabaseクライアント

    RLSポリシーがtest_user_1の権限で適用されます。
    """
    client = create_client(supabase_url, supabase_anon_key)

    # ログイン
    client.auth.sign_in_with_password({
        "email": test_user_1.email,
        "password": test_user_1.password,
    })

    yield client

    # ログアウト
    try:
        client.auth.sign_out()
    except Exception:
        pass


@pytest.fixture(scope="function")
def authenticated_client_2(supabase_url: str, supabase_anon_key: str, test_user_2: RlsTestUser) -> Generator[Client, None, None]:
    """
    テストユーザー2で認証済みのSupabaseクライアント

    RLSポリシーがtest_user_2の権限で適用されます。
    """
    client = create_client(supabase_url, supabase_anon_key)

    # ログイン
    client.auth.sign_in_with_password({
        "email": test_user_2.email,
        "password": test_user_2.password,
    })

    yield client

    # ログアウト
    try:
        client.auth.sign_out()
    except Exception:
        pass


# ===========================
# テストデータ生成フィクスチャ
# ===========================

@pytest.fixture(scope="function")
def company_user_1(authenticated_client_1: Client, test_user_1: RlsTestUser) -> Generator[Dict[str, Any], None, None]:
    """
    テストユーザー1の会社データを作成

    テスト実行後に自動的に削除されます（CASCADE）。
    """
    company_data = {
        "user_id": test_user_1.user_id,
        "name": "テスト株式会社1",
        "description": "テストユーザー1の会社です",
        "regions": ["東京都", "神奈川県"],
        "budget_min": 5000000,
        "budget_max": 50000000,
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "ng_keywords": ["NG1", "NG2"],
    }

    response = authenticated_client_1.table("companies").insert(company_data).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("テストユーザー1の会社データの作成に失敗しました")

    company = response.data[0]
    yield company

    # クリーンアップはユーザー削除時にCASCADEで自動削除されるため不要


@pytest.fixture(scope="function")
def company_user_2(authenticated_client_2: Client, test_user_2: RlsTestUser) -> Generator[Dict[str, Any], None, None]:
    """
    テストユーザー2の会社データを作成

    テスト実行後に自動的に削除されます（CASCADE）。
    """
    company_data = {
        "user_id": test_user_2.user_id,
        "name": "テスト株式会社2",
        "description": "テストユーザー2の会社です",
        "regions": ["大阪府"],
        "budget_min": 3000000,
        "budget_max": 30000000,
        "skills": ["Java", "Spring", "MySQL"],
        "ng_keywords": [],
    }

    response = authenticated_client_2.table("companies").insert(company_data).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("テストユーザー2の会社データの作成に失敗しました")

    company = response.data[0]
    yield company

    # クリーンアップはユーザー削除時にCASCADEで自動削除されるため不要


@pytest.fixture(scope="function")
def rfp_data(supabase_service_client: Client) -> Generator[Dict[str, Any], None, None]:
    """
    RFP案件データを作成（Service Roleで作成）

    テスト実行後に自動的に削除されます。
    """
    rfp = {
        "external_id": f"test-rfp-{uuid.uuid4()}",
        "title": "テストRFP案件",
        "issuing_org": "テスト省庁",
        "description": "これはRLSテスト用のRFP案件です。",
        "budget": 10000000,
        "region": "東京都",
        "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "url": "https://example.com/rfp/test",
        "external_doc_urls": ["https://example.com/doc1.pdf"],
        "embedding": [0.1] * 1536,
    }

    response = supabase_service_client.table("rfps").insert(rfp).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("RFPデータの作成に失敗しました")

    rfp_record = response.data[0]
    yield rfp_record

    # クリーンアップ
    try:
        supabase_service_client.table("rfps").delete().eq("id", rfp_record["id"]).execute()
    except Exception as e:
        print(f"RFPデータのクリーンアップに失敗: {e}")


@pytest.fixture(scope="function")
def company_document_user_1(authenticated_client_1: Client, company_user_1: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    テストユーザー1の会社ドキュメントデータを作成

    テスト実行後に自動的に削除されます（CASCADE）。
    """
    document_data = {
        "company_id": company_user_1["id"],
        "title": "実績資料1",
        "kind": "pdf",
        "storage_path": "test/user1/document1.pdf",
        "size_bytes": 1024000,
        "tags": ["実績", "品質"],
        "description": "テスト用の実績資料です",
    }

    response = authenticated_client_1.table("company_documents").insert(document_data).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("テストユーザー1の会社ドキュメントの作成に失敗しました")

    document = response.data[0]
    yield document

    # クリーンアップはユーザー削除時にCASCADEで自動削除されるため不要


@pytest.fixture(scope="function")
def bookmark_user_1(authenticated_client_1: Client, test_user_1: RlsTestUser, rfp_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    テストユーザー1のブックマークデータを作成

    テスト実行後に自動的に削除されます（CASCADE）。
    """
    bookmark_data = {
        "user_id": test_user_1.user_id,
        "rfp_id": rfp_data["id"],
    }

    response = authenticated_client_1.table("bookmarks").insert(bookmark_data).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("テストユーザー1のブックマークの作成に失敗しました")

    bookmark = response.data[0]
    yield bookmark

    # クリーンアップはユーザー削除時にCASCADEで自動削除されるため不要


@pytest.fixture(scope="function")
def match_snapshot_user_1(supabase_service_client: Client, test_user_1: RlsTestUser, rfp_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    テストユーザー1のマッチングスナップショットデータを作成（Service Roleで作成）

    テスト実行後に自動的に削除されます。
    """
    snapshot_data = {
        "user_id": test_user_1.user_id,
        "rfp_id": rfp_data["id"],
        "score": 85,
        "must_ok": True,
        "budget_ok": True,
        "region_ok": True,
        "factors": {
            "skill": 0.8,
            "must": 1.0,
            "budget": 1.0,
            "deadline": 0.9,
            "region": 1.0,
        },
        "summary_points": ["予算適合", "地域適合", "高いスキルマッチ"],
    }

    response = supabase_service_client.table("match_snapshots").insert(snapshot_data).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("テストユーザー1のマッチングスナップショットの作成に失敗しました")

    snapshot = response.data[0]
    yield snapshot

    # クリーンアップ
    try:
        supabase_service_client.table("match_snapshots").delete().eq("id", snapshot["id"]).execute()
    except Exception as e:
        print(f"マッチングスナップショットのクリーンアップに失敗: {e}")


@pytest.fixture(scope="function")
def company_skill_embedding_user_1(supabase_service_client: Client, company_user_1: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    テストユーザー1の会社スキル埋め込みデータを作成（Service Roleで作成）

    テスト実行後に自動的に削除されます。
    """
    embedding_data = {
        "company_id": company_user_1["id"],
        "skill_text": "Python, FastAPI, PostgreSQLを使用したシステム開発の実績があります。",
        "embedding": [0.2] * 1536,
    }

    response = supabase_service_client.table("company_skill_embeddings").insert(embedding_data).execute()

    if not response.data or len(response.data) == 0:
        pytest.fail("テストユーザー1の会社スキル埋め込みの作成に失敗しました")

    embedding = response.data[0]
    yield embedding

    # クリーンアップ
    try:
        supabase_service_client.table("company_skill_embeddings").delete().eq("id", embedding["id"]).execute()
    except Exception as e:
        print(f"会社スキル埋め込みのクリーンアップに失敗: {e}")
