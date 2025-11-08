"""
KKJ API拡張フィールドのRLS継続性テスト

rfpsテーブルに追加された9個の新規カラム（category, procedure_type, cft_issue_date,
tender_deadline, opening_event_date, item_code, lg_code, city_code, certification）が
既存のRLSポリシーと互換性を保ちながら機能することを確認します。

注意: このテストを実行する前に、以下のマイグレーションを実行してください：
    supabase db push (apps/apiディレクトリから)
    またはSupabase Dashboardで以下のSQLを実行:
    - migrations/20251108_kkj_api_extended_fields.sql

スキーマキャッシュの更新:
    Supabase APIはスキーマキャッシュを使用しているため、マイグレーション実行後に
    PostgRESTプロセスの再起動やキャッシュの無効化が必要な場合があります。

実行方法:
    pytest tests/test_rls_rfps_extended.py -v -m rls

環境変数の設定が必要:
    - SUPABASE_URL: SupabaseプロジェクトURL
    - SUPABASE_ANON_KEY: Supabase匿名キー
    - SUPABASE_SERVICE_KEY: Supabaseサービスキー
"""
import pytest
from supabase import Client
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from tests.fixtures.rls_fixtures import (
    RlsTestUser,
    supabase_service_client,
    authenticated_client_1,
    test_user_1,
    rfp_data,
)

logger = logging.getLogger(__name__)


def check_extended_fields_available(client: Client) -> bool:
    """
    拡張フィールドがデータベースで利用可能かチェック

    Service Roleクライアントを使用してRFPテーブルの構造を確認し、
    拡張フィールドが存在するかを判定します。

    Args:
        client: Supabaseクライアント（Service Role推奨）

    Returns:
        bool: 拡張フィールドが利用可能な場合True、そうでない場合False
    """
    try:
        # テーブル情報を取得してみる
        response = client.table("rfps").select("category").limit(1).execute()
        return True
    except Exception as e:
        logger.warning(f"Extended fields not available: {e}")
        return False


@pytest.mark.rls
class TestRfpsExtendedFieldsRLS:
    """rfpsテーブル拡張フィールドのRLSポリシーテスト"""

    # ========================================================================
    # テスト1: 認証ユーザーが拡張フィールド付きRFPを参照できる
    # ========================================================================

    def test_authenticated_user_can_read_extended_fields(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
        test_user_1: RlsTestUser,
    ) -> None:
        """
        認証ユーザーが拡張フィールド付きRFPを参照できることを確認する

        Service Roleで拡張フィールド（category, procedure_type, lg_code, city_code等）を
        含むRFPを作成し、認証ユーザーで取得してすべてのフィールドが正しく返されることを検証。

        テスト手順:
            1. Service Roleで拡張フィールド付きRFPを作成
            2. 認証ユーザーで同じRFPを参照
            3. すべての拡張フィールドが正しく取得できることを確認
        """
        import uuid

        try:
            # RFPを作成（拡張フィールド付き）
            rfp = {
                "external_id": f"test-extended-{uuid.uuid4()}",
                "title": "拡張フィールドテスト案件",
                "issuing_org": "テスト省庁",
                "description": "KKJ API拡張フィールドのテスト案件です。",
                "budget": 5000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                # 拡張フィールド
                "category": "建設工事",
                "procedure_type": "一般競争入札",
                "cft_issue_date": datetime.now().isoformat(),
                "tender_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
                "opening_event_date": (datetime.now() + timedelta(days=31)).isoformat(),
                "item_code": "30100100",
                "lg_code": "13",  # 東京都
                "city_code": "100",
                "certification": "建設業許可を要する",
            }

            response = supabase_service_client.table("rfps").insert(rfp).execute()
            assert response.data is not None
            assert len(response.data) == 1
            rfp_id = response.data[0]["id"]

            # 認証ユーザーでRFPを参照
            auth_response = authenticated_client_1.table("rfps").select("*").eq("id", rfp_id).execute()

            assert auth_response.data is not None
            assert len(auth_response.data) == 1
            fetched_rfp = auth_response.data[0]

            # 基本フィールド確認
            assert fetched_rfp["id"] == rfp_id
            assert fetched_rfp["title"] == "拡張フィールドテスト案件"

            # 拡張フィールド確認
            assert fetched_rfp["category"] == "建設工事"
            assert fetched_rfp["procedure_type"] == "一般競争入札"
            assert fetched_rfp["item_code"] == "30100100"
            assert fetched_rfp["lg_code"] == "13"
            assert fetched_rfp["city_code"] == "100"
            assert fetched_rfp["certification"] == "建設業許可を要する"
            assert fetched_rfp["cft_issue_date"] is not None
            assert fetched_rfp["tender_deadline"] is not None
            assert fetched_rfp["opening_event_date"] is not None

        finally:
            # クリーンアップ
            supabase_service_client.table("rfps").delete().eq("external_id", f"test-extended-{rfp_id}").execute()

    # ========================================================================
    # テスト2: 拡張フィールドでのフィルタリングが機能する
    # ========================================================================

    def test_extended_fields_filtering_works(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
    ) -> None:
        """
        拡張フィールド（category, lg_code）でフィルタリングできることを確認する

        複数のRFPを異なるcategory, lg_codeで作成し、認証ユーザーが正しく
        フィルタリングできることを検証。

        テスト手順:
            1. Service Roleで異なるcategoryのRFPを2つ作成
            2. 認証ユーザーで特定のcategoryでフィルタリング
            3. 正しいRFPのみが取得できることを確認
        """
        import uuid

        rfp_ids = []
        try:
            # RFP 1: カテゴリ「建設工事」
            rfp_1 = {
                "external_id": f"test-filter-1-{uuid.uuid4()}",
                "title": "建設工事案件",
                "issuing_org": "省庁A",
                "description": "建設工事の案件",
                "budget": 10000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                "category": "建設工事",
                "lg_code": "13",
            }

            # RFP 2: カテゴリ「製造・供給」
            rfp_2 = {
                "external_id": f"test-filter-2-{uuid.uuid4()}",
                "title": "製造・供給案件",
                "issuing_org": "省庁B",
                "description": "製造・供給の案件",
                "budget": 5000000,
                "region": "大阪府",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.2] * 1536,
                "category": "製造・供給",
                "lg_code": "27",
            }

            # RFPを作成
            response_1 = supabase_service_client.table("rfps").insert(rfp_1).execute()
            response_2 = supabase_service_client.table("rfps").insert(rfp_2).execute()

            assert response_1.data and len(response_1.data) == 1
            assert response_2.data and len(response_2.data) == 1

            rfp_id_1 = response_1.data[0]["id"]
            rfp_id_2 = response_2.data[0]["id"]
            rfp_ids = [rfp_id_1, rfp_id_2]

            # categoryでフィルタリング: 建設工事
            filter_response = (
                authenticated_client_1.table("rfps")
                .select("*")
                .eq("category", "建設工事")
                .execute()
            )

            assert filter_response.data is not None
            # 作成したRFPは少なくとも含まれるはず
            filtered_titles = [r["title"] for r in filter_response.data]
            assert "建設工事案件" in filtered_titles

            # 製造・供給案件は含まれないはず
            assert "製造・供給案件" not in filtered_titles

            # lg_codeでフィルタリング: 大阪府（27）
            lg_filter_response = (
                authenticated_client_1.table("rfps")
                .select("*")
                .eq("lg_code", "27")
                .execute()
            )

            assert lg_filter_response.data is not None
            # 製造・供給案件は含まれるはず
            lg_titles = [r["title"] for r in lg_filter_response.data]
            assert "製造・供給案件" in lg_titles

        finally:
            # クリーンアップ
            for rfp_id in rfp_ids:
                try:
                    supabase_service_client.table("rfps").delete().eq("id", rfp_id).execute()
                except Exception:
                    pass

    # ========================================================================
    # テスト3: 日時フィールドの範囲検索が機能する
    # ========================================================================

    def test_datetime_fields_range_search_works(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
    ) -> None:
        """
        日時フィールド（tender_deadline）の範囲検索が機能することを確認する

        異なるtender_deadlineを持つRFPを複数作成し、認証ユーザーが
        範囲検索（gte, lte）できることを検証。

        テスト手順:
            1. Service Roleで異なるtender_deadlineのRFPを3つ作成
            2. 認証ユーザーで期限範囲を指定してフィルタリング
            3. 正しい範囲のRFPのみが取得できることを確認
        """
        import uuid

        rfp_ids = []
        try:
            now = datetime.now()
            date_1 = now + timedelta(days=10)
            date_2 = now + timedelta(days=20)
            date_3 = now + timedelta(days=30)

            # RFP 1: 10日後が期限
            rfp_1 = {
                "external_id": f"test-date-1-{uuid.uuid4()}",
                "title": "期限10日後",
                "issuing_org": "省庁A",
                "description": "早い期限",
                "budget": 1000000,
                "region": "東京都",
                "deadline": (now + timedelta(days=10)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                "tender_deadline": date_1.isoformat(),
            }

            # RFP 2: 20日後が期限
            rfp_2 = {
                "external_id": f"test-date-2-{uuid.uuid4()}",
                "title": "期限20日後",
                "issuing_org": "省庁B",
                "description": "中間期限",
                "budget": 2000000,
                "region": "大阪府",
                "deadline": (now + timedelta(days=20)).strftime("%Y-%m-%d"),
                "embedding": [0.2] * 1536,
                "tender_deadline": date_2.isoformat(),
            }

            # RFP 3: 30日後が期限
            rfp_3 = {
                "external_id": f"test-date-3-{uuid.uuid4()}",
                "title": "期限30日後",
                "issuing_org": "省庁C",
                "description": "遠い期限",
                "budget": 3000000,
                "region": "福岡県",
                "deadline": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.3] * 1536,
                "tender_deadline": date_3.isoformat(),
            }

            # RFPを作成
            response_1 = supabase_service_client.table("rfps").insert(rfp_1).execute()
            response_2 = supabase_service_client.table("rfps").insert(rfp_2).execute()
            response_3 = supabase_service_client.table("rfps").insert(rfp_3).execute()

            assert all([response_1.data, response_2.data, response_3.data])
            rfp_ids = [r["id"] for r in [response_1.data[0], response_2.data[0], response_3.data[0]]]

            # 範囲検索: 15日後〜25日後
            query_date_start = (now + timedelta(days=15)).isoformat()
            query_date_end = (now + timedelta(days=25)).isoformat()

            range_response = (
                authenticated_client_1.table("rfps")
                .select("*")
                .gte("tender_deadline", query_date_start)
                .lte("tender_deadline", query_date_end)
                .execute()
            )

            assert range_response.data is not None
            range_titles = [r["title"] for r in range_response.data]

            # 期限20日後は含まれるはず
            assert "期限20日後" in range_titles

            # 期限10日後と30日後は含まれないはず
            assert "期限10日後" not in range_titles
            assert "期限30日後" not in range_titles

        finally:
            # クリーンアップ
            for rfp_id in rfp_ids:
                try:
                    supabase_service_client.table("rfps").delete().eq("id", rfp_id).execute()
                except Exception:
                    pass

    # ========================================================================
    # テスト4: NULLフィールドの扱いが正常
    # ========================================================================

    def test_null_extended_fields_handling(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
    ) -> None:
        """
        拡張フィールドがNULLのRFPが正しく処理されることを確認する

        一部の拡張フィールドがNULLのRFPを作成し、認証ユーザーで取得して
        NULLフィールドがNoneとして正しく返されることを検証。

        テスト手順:
            1. Service Roleで拡張フィールドがNULLのRFPを作成
            2. 認証ユーザーで取得
            3. NULLフィールドがNoneとして返されることを確認
        """
        import uuid

        rfp_id = None
        try:
            # 拡張フィールドのいくつかをNULLで作成
            rfp = {
                "external_id": f"test-null-{uuid.uuid4()}",
                "title": "NULLフィールドテスト",
                "issuing_org": "省庁",
                "description": "一部のフィールドがNULLです",
                "budget": 5000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                # 拡張フィールド: 一部のみ設定
                "category": "建設工事",
                "procedure_type": None,  # NULLで作成
                "cft_issue_date": datetime.now().isoformat(),
                "tender_deadline": None,  # NULLで作成
                "opening_event_date": None,  # NULLで作成
                "item_code": None,  # NULLで作成
                "lg_code": "13",
                "city_code": None,  # NULLで作成
                "certification": None,  # NULLで作成
            }

            response = supabase_service_client.table("rfps").insert(rfp).execute()
            assert response.data and len(response.data) == 1
            rfp_id = response.data[0]["id"]

            # 認証ユーザーで取得
            auth_response = authenticated_client_1.table("rfps").select("*").eq("id", rfp_id).execute()

            assert auth_response.data is not None
            assert len(auth_response.data) == 1
            fetched_rfp = auth_response.data[0]

            # NULLフィールドがNoneとして返されることを確認
            assert fetched_rfp["category"] == "建設工事"
            assert fetched_rfp["procedure_type"] is None
            assert fetched_rfp["cft_issue_date"] is not None
            assert fetched_rfp["tender_deadline"] is None
            assert fetched_rfp["opening_event_date"] is None
            assert fetched_rfp["item_code"] is None
            assert fetched_rfp["lg_code"] == "13"
            assert fetched_rfp["city_code"] is None
            assert fetched_rfp["certification"] is None

        finally:
            # クリーンアップ
            if rfp_id:
                try:
                    supabase_service_client.table("rfps").delete().eq("id", rfp_id).execute()
                except Exception:
                    pass

    # ========================================================================
    # テスト5: Service Roleのみが拡張フィールド付きRFPを作成できる
    # ========================================================================

    def test_only_service_role_can_create_rfps_with_extended_fields(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
    ) -> None:
        """
        一般ユーザーはRFPを作成できず、Service Roleのみが作成できることを確認する

        既存のRLSポリシーが拡張フィールドでも引き続き機能していることを検証。

        テスト手順:
            1. 認証ユーザーでRFP作成を試行 → エラー確認
            2. Service RoleでRFP作成 → 成功確認
        """
        import uuid

        rfp_id = None
        try:
            # 一般ユーザーでRFP作成を試行（拡張フィールド付き）
            new_rfp = {
                "external_id": f"unauthorized-{uuid.uuid4()}",
                "title": "不正なRFP",
                "issuing_org": "不正な組織",
                "description": "一般ユーザーが作成しようとしたRFP",
                "budget": 5000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                "category": "建設工事",  # 拡張フィールド
                "lg_code": "13",  # 拡張フィールド
            }

            # RLSポリシーにより作成が拒否される
            with pytest.raises(Exception):
                authenticated_client_1.table("rfps").insert(new_rfp).execute()

            # Service Roleでは作成できる
            service_rfp = {
                "external_id": f"authorized-{uuid.uuid4()}",
                "title": "Service Roleで作成したRFP",
                "issuing_org": "省庁",
                "description": "Service Roleで正しく作成されたRFP",
                "budget": 5000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                "category": "建設工事",
                "lg_code": "13",
            }

            response = supabase_service_client.table("rfps").insert(service_rfp).execute()
            assert response.data is not None
            assert len(response.data) == 1
            assert response.data[0]["category"] == "建設工事"
            assert response.data[0]["lg_code"] == "13"
            rfp_id = response.data[0]["id"]

        finally:
            # クリーンアップ
            if rfp_id:
                try:
                    supabase_service_client.table("rfps").delete().eq("id", rfp_id).execute()
                except Exception:
                    pass

    # ========================================================================
    # テスト6: 複合フィルタリング（複数の拡張フィールド）
    # ========================================================================

    def test_combined_extended_fields_filtering(
        self,
        authenticated_client_1: Client,
        supabase_service_client: Client,
    ) -> None:
        """
        複数の拡張フィールドを組み合わせてフィルタリングできることを確認する

        category と lg_code の両方でフィルタリングし、複合条件検索が
        正しく動作することを検証。

        テスト手順:
            1. 異なるcategory/lg_codeの組み合わせのRFPを複数作成
            2. 認証ユーザーで複合フィルタリング実行
            3. 正しい結果が取得できることを確認
        """
        import uuid

        rfp_ids = []
        try:
            # RFP 1: 建設工事 × 東京都
            rfp_1 = {
                "external_id": f"test-combined-1-{uuid.uuid4()}",
                "title": "東京建設工事",
                "issuing_org": "省庁A",
                "description": "東京の建設工事案件",
                "budget": 10000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.1] * 1536,
                "category": "建設工事",
                "lg_code": "13",
            }

            # RFP 2: 建設工事 × 大阪府
            rfp_2 = {
                "external_id": f"test-combined-2-{uuid.uuid4()}",
                "title": "大阪建設工事",
                "issuing_org": "省庁B",
                "description": "大阪の建設工事案件",
                "budget": 10000000,
                "region": "大阪府",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.2] * 1536,
                "category": "建設工事",
                "lg_code": "27",
            }

            # RFP 3: 製造・供給 × 東京都
            rfp_3 = {
                "external_id": f"test-combined-3-{uuid.uuid4()}",
                "title": "東京製造・供給",
                "issuing_org": "省庁C",
                "description": "東京の製造・供給案件",
                "budget": 5000000,
                "region": "東京都",
                "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "embedding": [0.3] * 1536,
                "category": "製造・供給",
                "lg_code": "13",
            }

            # RFPを作成
            response_1 = supabase_service_client.table("rfps").insert(rfp_1).execute()
            response_2 = supabase_service_client.table("rfps").insert(rfp_2).execute()
            response_3 = supabase_service_client.table("rfps").insert(rfp_3).execute()

            assert all([response_1.data, response_2.data, response_3.data])
            rfp_ids = [r["id"] for r in [response_1.data[0], response_2.data[0], response_3.data[0]]]

            # 複合フィルタリング: 建設工事 AND 東京都
            combined_response = (
                authenticated_client_1.table("rfps")
                .select("*")
                .eq("category", "建設工事")
                .eq("lg_code", "13")
                .execute()
            )

            assert combined_response.data is not None
            combined_titles = [r["title"] for r in combined_response.data]

            # 東京建設工事は含まれるはず
            assert "東京建設工事" in combined_titles

            # 大阪建設工事と東京製造・供給は含まれないはず
            assert "大阪建設工事" not in combined_titles
            assert "東京製造・供給" not in combined_titles

        finally:
            # クリーンアップ
            for rfp_id in rfp_ids:
                try:
                    supabase_service_client.table("rfps").delete().eq("id", rfp_id).execute()
                except Exception:
                    pass

    # ========================================================================
    # テスト7: 既存のRFPに対する拡張フィールド読み取り
    # ========================================================================

    def test_read_existing_rfps_with_extended_fields(
        self,
        authenticated_client_1: Client,
        rfp_data: Dict[str, Any],
    ) -> None:
        """
        既存のRFPデータが正しく読み取れることを確認する

        マイグレーション前に作成されたRFPが、拡張フィールド追加後も
        正しく読み取れることを検証（後方互換性）。

        注意: マイグレーションが実行されている場合、拡張フィールドはNULLとして
        返されます。マイグレーションが実行されていない場合は、拡張フィールドの
        キーそのものが存在しません。

        テスト手順:
            1. 既存のRFP（拡張フィールドなし）を取得
            2. 基本フィールドは正しく読み取れることを確認
            3. 拡張フィールドが存在する場合はNULLで、存在しない場合も許容
        """
        # 既存のRFPを参照
        response = authenticated_client_1.table("rfps").select("*").eq("id", rfp_data["id"]).execute()

        assert response.data is not None
        assert len(response.data) == 1
        fetched_rfp = response.data[0]

        # 基本フィールドは存在するはず
        assert fetched_rfp["id"] == rfp_data["id"]
        assert fetched_rfp["title"] == "テストRFP案件"
        assert fetched_rfp["issuing_org"] == "テスト省庁"
        assert fetched_rfp["budget"] == 10000000

        # 拡張フィールドのチェック
        # マイグレーションが実行されている場合、フィールドが存在しNULLが返される
        # マイグレーションが実行されていない場合、フィールドキーが存在しない
        extended_fields = [
            "category",
            "procedure_type",
            "cft_issue_date",
            "tender_deadline",
            "opening_event_date",
            "item_code",
            "lg_code",
            "city_code",
            "certification",
        ]

        # 拡張フィールドの存在確認
        has_extended_fields = all(field in fetched_rfp for field in extended_fields)

        if has_extended_fields:
            # マイグレーション実行済み: すべての拡張フィールドがNULLであることを確認
            for field in extended_fields:
                assert fetched_rfp[field] is None, f"Field {field} should be None for pre-migration RFP"
        else:
            # マイグレーション未実行: 拡張フィールドが存在しないことは許容
            # テストはスキップせず、基本フィールドの読み取りが正常であることを確認
            pass
