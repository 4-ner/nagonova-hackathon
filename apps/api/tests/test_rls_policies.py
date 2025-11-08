"""
Row Level Security (RLS) ポリシー動作確認テスト

実際のSupabaseデータベースに接続し、RLSポリシーが正しく機能していることを確認します。

実行方法:
    pytest tests/test_rls_policies.py -v -m rls

環境変数の設定が必要:
    - SUPABASE_URL: SupabaseプロジェクトURL
    - SUPABASE_ANON_KEY: Supabase匿名キー
    - SUPABASE_SERVICE_KEY: Supabaseサービスキー
"""
import pytest
from supabase import Client
from typing import Dict, Any

from tests.fixtures.rls_fixtures import (
    RlsTestUser,
    supabase_anon_client,
    supabase_service_client,
    authenticated_client_1,
    authenticated_client_2,
    test_user_1,
    test_user_2,
    company_user_1,
    company_user_2,
    rfp_data,
    company_document_user_1,
    bookmark_user_1,
    match_snapshot_user_1,
    company_skill_embedding_user_1,
)


# ============================================================================
# 1. companiesテーブル - RLSポリシーテスト
# ============================================================================

@pytest.mark.rls
class TestCompaniesRLS:
    """companiesテーブルのRLSポリシーテスト"""

    def test_user_can_read_own_company(
        self,
        authenticated_client_1: Client,
        company_user_1: Dict[str, Any],
        test_user_1: RlsTestUser,
    ):
        """ユーザーは自分の会社を参照できる"""
        response = authenticated_client_1.table("companies").select("*").eq("user_id", test_user_1.user_id).execute()

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == company_user_1["id"]
        assert response.data[0]["name"] == "テスト株式会社1"

    def test_user_cannot_read_other_company(
        self,
        authenticated_client_1: Client,
        company_user_2: Dict[str, Any],
        test_user_2: RlsTestUser,
    ):
        """ユーザーは他人の会社を参照できない"""
        response = authenticated_client_1.table("companies").select("*").eq("user_id", test_user_2.user_id).execute()

        # RLSによりフィルタリングされ、結果は空になる
        assert response.data is not None
        assert len(response.data) == 0

    def test_user_can_update_own_company(
        self,
        authenticated_client_1: Client,
        company_user_1: Dict[str, Any],
    ):
        """ユーザーは自分の会社を更新できる"""
        updated_name = "更新されたテスト株式会社1"

        response = (
            authenticated_client_1.table("companies")
            .update({"name": updated_name})
            .eq("id", company_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["name"] == updated_name

    def test_user_cannot_update_other_company(
        self,
        authenticated_client_1: Client,
        company_user_2: Dict[str, Any],
    ):
        """ユーザーは他人の会社を更新できない"""
        # RLSポリシーにより更新が拒否される（または影響行数が0）
        response = (
            authenticated_client_1.table("companies")
            .update({"name": "不正な更新"})
            .eq("id", company_user_2["id"])
            .execute()
        )

        # 更新されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0

    def test_user_can_create_company(
        self,
        authenticated_client_1: Client,
        test_user_1: RlsTestUser,
        supabase_service_client: Client,
    ):
        """ユーザーは自分の会社を作成できる"""
        # まず既存の会社を削除（UNIQUE制約対策）
        supabase_service_client.table("companies").delete().eq("user_id", test_user_1.user_id).execute()

        new_company_data = {
            "user_id": test_user_1.user_id,
            "name": "新規作成会社",
            "description": "新しく作成された会社です",
            "regions": ["東京都"],
            "budget_min": 1000000,
            "budget_max": 10000000,
            "skills": ["Python"],
            "ng_keywords": [],
        }

        response = authenticated_client_1.table("companies").insert(new_company_data).execute()

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["name"] == "新規作成会社"
        assert response.data[0]["user_id"] == test_user_1.user_id

    def test_unauthenticated_user_cannot_read_companies(
        self,
        supabase_anon_client: Client,
        company_user_1: Dict[str, Any],
    ):
        """未認証ユーザーは会社を参照できない"""
        # ログアウトして未認証状態にする
        supabase_anon_client.auth.sign_out()

        response = supabase_anon_client.table("companies").select("*").execute()

        # 未認証の場合、RLSにより結果が空になる
        assert response.data is not None
        assert len(response.data) == 0


# ============================================================================
# 2. company_documentsテーブル - RLSポリシーテスト
# ============================================================================

@pytest.mark.rls
class TestCompanyDocumentsRLS:
    """company_documentsテーブルのRLSポリシーテスト"""

    def test_user_can_read_own_company_documents(
        self,
        authenticated_client_1: Client,
        company_document_user_1: Dict[str, Any],
        company_user_1: Dict[str, Any],
    ):
        """同一会社のユーザーはドキュメントを参照できる"""
        response = (
            authenticated_client_1.table("company_documents")
            .select("*")
            .eq("company_id", company_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == company_document_user_1["id"]
        assert response.data[0]["title"] == "実績資料1"

    def test_user_cannot_read_other_company_documents(
        self,
        authenticated_client_1: Client,
        authenticated_client_2: Client,
        company_user_2: Dict[str, Any],
    ):
        """他社のユーザーはドキュメントを参照できない"""
        # ユーザー2のドキュメントを作成
        document_data = {
            "company_id": company_user_2["id"],
            "title": "ユーザー2の資料",
            "kind": "pdf",
            "storage_path": "test/user2/document.pdf",
            "size_bytes": 2048000,
        }
        doc_response = authenticated_client_2.table("company_documents").insert(document_data).execute()
        document_id = doc_response.data[0]["id"]

        # ユーザー1でユーザー2のドキュメントを参照しようとする
        response = (
            authenticated_client_1.table("company_documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )

        # RLSにより結果が空になる
        assert response.data is not None
        assert len(response.data) == 0

    def test_user_can_create_document(
        self,
        authenticated_client_1: Client,
        company_user_1: Dict[str, Any],
    ):
        """同一会社のユーザーはドキュメントを作成できる"""
        new_document_data = {
            "company_id": company_user_1["id"],
            "title": "新規ドキュメント",
            "kind": "url",
            "url": "https://example.com/newdoc",
            "tags": ["新規"],
        }

        response = authenticated_client_1.table("company_documents").insert(new_document_data).execute()

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["title"] == "新規ドキュメント"
        assert response.data[0]["company_id"] == company_user_1["id"]

    def test_user_can_delete_own_company_document(
        self,
        authenticated_client_1: Client,
        company_document_user_1: Dict[str, Any],
    ):
        """同一会社のユーザーはドキュメントを削除できる"""
        response = (
            authenticated_client_1.table("company_documents")
            .delete()
            .eq("id", company_document_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == company_document_user_1["id"]

        # 削除確認
        verify_response = (
            authenticated_client_1.table("company_documents")
            .select("*")
            .eq("id", company_document_user_1["id"])
            .execute()
        )
        assert len(verify_response.data) == 0

    def test_user_cannot_delete_other_company_document(
        self,
        authenticated_client_1: Client,
        authenticated_client_2: Client,
        company_user_2: Dict[str, Any],
    ):
        """他社のユーザーはドキュメントを削除できない"""
        # ユーザー2のドキュメントを作成
        document_data = {
            "company_id": company_user_2["id"],
            "title": "ユーザー2の削除対象資料",
            "kind": "text",
            "storage_path": "test/user2/delete_test.txt",
            "size_bytes": 1024,
        }
        doc_response = authenticated_client_2.table("company_documents").insert(document_data).execute()
        document_id = doc_response.data[0]["id"]

        # ユーザー1でユーザー2のドキュメントを削除しようとする
        response = (
            authenticated_client_1.table("company_documents")
            .delete()
            .eq("id", document_id)
            .execute()
        )

        # 削除されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0


# ============================================================================
# 3. rfpsテーブル - RLSポリシーテスト
# ============================================================================

@pytest.mark.rls
class TestRfpsRLS:
    """rfpsテーブルのRLSポリシーテスト"""

    def test_authenticated_user_can_read_rfps(
        self,
        authenticated_client_1: Client,
        rfp_data: Dict[str, Any],
    ):
        """認証済みユーザーはRFPを参照できる"""
        response = authenticated_client_1.table("rfps").select("*").eq("id", rfp_data["id"]).execute()

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == rfp_data["id"]
        assert response.data[0]["title"] == "テストRFP案件"

    def test_unauthenticated_user_cannot_read_rfps(
        self,
        supabase_anon_client: Client,
        rfp_data: Dict[str, Any],
    ):
        """未認証ユーザーはRFPを参照できない"""
        # ログアウトして未認証状態にする
        supabase_anon_client.auth.sign_out()

        response = supabase_anon_client.table("rfps").select("*").execute()

        # 未認証の場合、RLSにより結果が空になる
        assert response.data is not None
        assert len(response.data) == 0

    def test_user_cannot_create_rfp(
        self,
        authenticated_client_1: Client,
    ):
        """一般ユーザーはRFPを作成できない"""
        import uuid
        from datetime import datetime, timedelta

        new_rfp_data = {
            "external_id": f"unauthorized-rfp-{uuid.uuid4()}",
            "title": "不正なRFP",
            "issuing_org": "不正な組織",
            "description": "一般ユーザーが作成しようとしたRFP",
            "budget": 5000000,
            "region": "東京都",
            "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "embedding": [0.1] * 1536,
        }

        # RLSポリシーにより作成が拒否される
        with pytest.raises(Exception):
            authenticated_client_1.table("rfps").insert(new_rfp_data).execute()

    def test_user_cannot_update_rfp(
        self,
        authenticated_client_1: Client,
        rfp_data: Dict[str, Any],
    ):
        """一般ユーザーはRFPを更新できない"""
        # RLSポリシーにより更新が拒否される
        response = (
            authenticated_client_1.table("rfps")
            .update({"title": "不正な更新"})
            .eq("id", rfp_data["id"])
            .execute()
        )

        # 更新されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0

    def test_user_cannot_delete_rfp(
        self,
        authenticated_client_1: Client,
        rfp_data: Dict[str, Any],
    ):
        """一般ユーザーはRFPを削除できない"""
        # RLSポリシーにより削除が拒否される
        response = authenticated_client_1.table("rfps").delete().eq("id", rfp_data["id"]).execute()

        # 削除されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0

    def test_service_role_can_manage_rfps(
        self,
        supabase_service_client: Client,
        rfp_data: Dict[str, Any],
    ):
        """Service RoleはRFPを管理できる（作成・更新・削除）"""
        # 更新テスト
        updated_title = "Service Roleで更新されたRFP"
        response = (
            supabase_service_client.table("rfps")
            .update({"title": updated_title})
            .eq("id", rfp_data["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["title"] == updated_title


# ============================================================================
# 4. bookmarksテーブル - RLSポリシーテスト
# ============================================================================

@pytest.mark.rls
class TestBookmarksRLS:
    """bookmarksテーブルのRLSポリシーテスト"""

    def test_user_can_read_own_bookmarks(
        self,
        authenticated_client_1: Client,
        bookmark_user_1: Dict[str, Any],
        test_user_1: RlsTestUser,
    ):
        """ユーザーは自分のブックマークを参照できる"""
        response = (
            authenticated_client_1.table("bookmarks")
            .select("*")
            .eq("user_id", test_user_1.user_id)
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == bookmark_user_1["id"]
        assert response.data[0]["user_id"] == test_user_1.user_id

    def test_user_cannot_read_other_bookmarks(
        self,
        authenticated_client_1: Client,
        authenticated_client_2: Client,
        test_user_2: RlsTestUser,
        rfp_data: Dict[str, Any],
    ):
        """ユーザーは他人のブックマークを参照できない"""
        # ユーザー2のブックマークを作成
        bookmark_data = {
            "user_id": test_user_2.user_id,
            "rfp_id": rfp_data["id"],
        }
        bookmark_response = authenticated_client_2.table("bookmarks").insert(bookmark_data).execute()
        bookmark_id = bookmark_response.data[0]["id"]

        # ユーザー1でユーザー2のブックマークを参照しようとする
        response = authenticated_client_1.table("bookmarks").select("*").eq("id", bookmark_id).execute()

        # RLSにより結果が空になる
        assert response.data is not None
        assert len(response.data) == 0

    def test_user_can_create_bookmark(
        self,
        authenticated_client_1: Client,
        test_user_1: RlsTestUser,
        rfp_data: Dict[str, Any],
        supabase_service_client: Client,
    ):
        """ユーザーはブックマークを作成できる"""
        # 既存のブックマークを削除（UNIQUE制約対策）
        supabase_service_client.table("bookmarks").delete().eq("user_id", test_user_1.user_id).eq("rfp_id", rfp_data["id"]).execute()

        new_bookmark_data = {
            "user_id": test_user_1.user_id,
            "rfp_id": rfp_data["id"],
        }

        response = authenticated_client_1.table("bookmarks").insert(new_bookmark_data).execute()

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["user_id"] == test_user_1.user_id
        assert response.data[0]["rfp_id"] == rfp_data["id"]

    def test_user_can_delete_own_bookmark(
        self,
        authenticated_client_1: Client,
        bookmark_user_1: Dict[str, Any],
    ):
        """ユーザーは自分のブックマークを削除できる"""
        response = (
            authenticated_client_1.table("bookmarks")
            .delete()
            .eq("id", bookmark_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == bookmark_user_1["id"]

        # 削除確認
        verify_response = (
            authenticated_client_1.table("bookmarks")
            .select("*")
            .eq("id", bookmark_user_1["id"])
            .execute()
        )
        assert len(verify_response.data) == 0

    def test_user_cannot_delete_other_bookmark(
        self,
        authenticated_client_1: Client,
        authenticated_client_2: Client,
        test_user_2: RlsTestUser,
        rfp_data: Dict[str, Any],
    ):
        """ユーザーは他人のブックマークを削除できない"""
        # ユーザー2のブックマークを作成
        bookmark_data = {
            "user_id": test_user_2.user_id,
            "rfp_id": rfp_data["id"],
        }
        bookmark_response = authenticated_client_2.table("bookmarks").insert(bookmark_data).execute()
        bookmark_id = bookmark_response.data[0]["id"]

        # ユーザー1でユーザー2のブックマークを削除しようとする
        response = authenticated_client_1.table("bookmarks").delete().eq("id", bookmark_id).execute()

        # 削除されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0


# ============================================================================
# 5. match_snapshotsテーブル - RLSポリシーテスト
# ============================================================================

@pytest.mark.rls
class TestMatchSnapshotsRLS:
    """match_snapshotsテーブルのRLSポリシーテスト"""

    def test_user_can_read_own_match_snapshots(
        self,
        authenticated_client_1: Client,
        match_snapshot_user_1: Dict[str, Any],
        test_user_1: RlsTestUser,
    ):
        """ユーザーは自分のマッチングスナップショットを参照できる"""
        response = (
            authenticated_client_1.table("match_snapshots")
            .select("*")
            .eq("user_id", test_user_1.user_id)
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == match_snapshot_user_1["id"]
        assert response.data[0]["score"] == 85

    def test_user_cannot_read_other_match_snapshots(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
        test_user_2: RlsTestUser,
        rfp_data: Dict[str, Any],
    ):
        """ユーザーは他人のマッチングスナップショットを参照できない"""
        # ユーザー2のマッチングスナップショットを作成（Service Role）
        snapshot_data = {
            "user_id": test_user_2.user_id,
            "rfp_id": rfp_data["id"],
            "score": 70,
            "must_ok": True,
            "budget_ok": True,
            "region_ok": False,
            "factors": {
                "skill": 0.7,
                "must": 1.0,
                "budget": 1.0,
                "deadline": 0.8,
                "region": 0.5,
            },
            "summary_points": ["予算適合"],
        }
        snapshot_response = supabase_service_client.table("match_snapshots").insert(snapshot_data).execute()
        snapshot_id = snapshot_response.data[0]["id"]

        # ユーザー1でユーザー2のスナップショットを参照しようとする
        response = authenticated_client_1.table("match_snapshots").select("*").eq("id", snapshot_id).execute()

        # RLSにより結果が空になる
        assert response.data is not None
        assert len(response.data) == 0

        # クリーンアップ
        supabase_service_client.table("match_snapshots").delete().eq("id", snapshot_id).execute()

    def test_user_cannot_create_match_snapshot(
        self,
        authenticated_client_1: Client,
        test_user_1: RlsTestUser,
        rfp_data: Dict[str, Any],
    ):
        """一般ユーザーはマッチングスナップショットを作成できない"""
        snapshot_data = {
            "user_id": test_user_1.user_id,
            "rfp_id": rfp_data["id"],
            "score": 90,
            "must_ok": True,
            "budget_ok": True,
            "region_ok": True,
            "factors": {
                "skill": 0.9,
                "must": 1.0,
                "budget": 1.0,
                "deadline": 0.9,
                "region": 1.0,
            },
            "summary_points": ["完全一致"],
        }

        # RLSポリシーにより作成が拒否される
        with pytest.raises(Exception):
            authenticated_client_1.table("match_snapshots").insert(snapshot_data).execute()

    def test_user_cannot_delete_match_snapshot(
        self,
        authenticated_client_1: Client,
        match_snapshot_user_1: Dict[str, Any],
    ):
        """一般ユーザーはマッチングスナップショットを削除できない"""
        # RLSポリシーにより削除が拒否される
        response = (
            authenticated_client_1.table("match_snapshots")
            .delete()
            .eq("id", match_snapshot_user_1["id"])
            .execute()
        )

        # 削除されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0

    def test_service_role_can_manage_match_snapshots(
        self,
        supabase_service_client: Client,
        match_snapshot_user_1: Dict[str, Any],
    ):
        """Service Roleはマッチングスナップショットを管理できる"""
        # 更新テスト
        updated_score = 95

        response = (
            supabase_service_client.table("match_snapshots")
            .update({"score": updated_score})
            .eq("id", match_snapshot_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["score"] == updated_score


# ============================================================================
# 6. company_skill_embeddingsテーブル - RLSポリシーテスト
# ============================================================================

@pytest.mark.rls
class TestCompanySkillEmbeddingsRLS:
    """company_skill_embeddingsテーブルのRLSポリシーテスト"""

    def test_user_can_read_own_company_embeddings(
        self,
        authenticated_client_1: Client,
        company_skill_embedding_user_1: Dict[str, Any],
        company_user_1: Dict[str, Any],
    ):
        """ユーザーは自分の会社のスキル埋め込みを参照できる"""
        response = (
            authenticated_client_1.table("company_skill_embeddings")
            .select("*")
            .eq("company_id", company_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["id"] == company_skill_embedding_user_1["id"]
        assert response.data[0]["skill_text"] == "Python, FastAPI, PostgreSQLを使用したシステム開発の実績があります。"

    def test_user_cannot_read_other_company_embeddings(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
        company_user_2: Dict[str, Any],
    ):
        """ユーザーは他の会社のスキル埋め込みを参照できない"""
        # ユーザー2の会社スキル埋め込みを作成（Service Role）
        embedding_data = {
            "company_id": company_user_2["id"],
            "skill_text": "Java, Spring, MySQLの開発実績",
            "embedding": [0.3] * 1536,
        }
        embedding_response = supabase_service_client.table("company_skill_embeddings").insert(embedding_data).execute()
        embedding_id = embedding_response.data[0]["id"]

        # ユーザー1でユーザー2の埋め込みを参照しようとする
        response = authenticated_client_1.table("company_skill_embeddings").select("*").eq("id", embedding_id).execute()

        # RLSにより結果が空になる
        assert response.data is not None
        assert len(response.data) == 0

        # クリーンアップ
        supabase_service_client.table("company_skill_embeddings").delete().eq("id", embedding_id).execute()

    def test_user_cannot_create_embedding(
        self,
        authenticated_client_1: Client,
        company_user_1: Dict[str, Any],
    ):
        """一般ユーザーはスキル埋め込みを作成できない"""
        embedding_data = {
            "company_id": company_user_1["id"],
            "skill_text": "不正な埋め込み",
            "embedding": [0.5] * 1536,
        }

        # RLSポリシーにより作成が拒否される
        with pytest.raises(Exception):
            authenticated_client_1.table("company_skill_embeddings").insert(embedding_data).execute()

    def test_user_cannot_update_embedding(
        self,
        authenticated_client_1: Client,
        company_skill_embedding_user_1: Dict[str, Any],
    ):
        """一般ユーザーはスキル埋め込みを更新できない"""
        # RLSポリシーにより更新が拒否される
        response = (
            authenticated_client_1.table("company_skill_embeddings")
            .update({"skill_text": "不正な更新"})
            .eq("id", company_skill_embedding_user_1["id"])
            .execute()
        )

        # 更新されたレコードがないことを確認
        assert response.data is not None
        assert len(response.data) == 0

    def test_service_role_can_manage_embeddings(
        self,
        supabase_service_client: Client,
        company_skill_embedding_user_1: Dict[str, Any],
    ):
        """Service Roleはスキル埋め込みを管理できる"""
        # 更新テスト
        updated_text = "Service Roleで更新されたスキル説明"

        response = (
            supabase_service_client.table("company_skill_embeddings")
            .update({"skill_text": updated_text})
            .eq("id", company_skill_embedding_user_1["id"])
            .execute()
        )

        assert response.data is not None
        assert len(response.data) == 1
        assert response.data[0]["skill_text"] == updated_text
