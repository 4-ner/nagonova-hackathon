"""
RFP管理APIのテストケース

RFP一覧取得とマッチングスコア付きRFP取得をテストします。
"""
import pytest
from unittest.mock import MagicMock
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestGetRFPsWithMatching:
    """マッチングスコア付きRFP一覧取得APIのテストクラス"""

    def test_マッチングスコア付きRFP取得_正常系(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        mock_match_snapshot_data: dict,
    ):
        """マッチングスコア付きRFP一覧が正常に取得できることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショットのモックデータ
        match_with_rfp = {
            **mock_match_snapshot_data,
            "rfps": {
                **mock_rfp_data,
                "embedding": [0.1] * 1536,  # has_embeddingの判定用
            },
        }

        # マッチングスナップショット一覧のモック
        match_response = MagicMock()
        match_response.data = [match_with_rfp]
        match_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value

        # 会社情報取得のモック
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        # マッチングスナップショット取得のモック
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = (
            match_response
        )

        # APIリクエスト
        response = client.get("/api/rfps/with-matching?page=1&page_size=20")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) == 1

        # RFP情報の検証
        item = data["items"][0]
        assert item["id"] == mock_rfp_data["id"]
        assert item["title"] == mock_rfp_data["title"]

        # マッチング情報の検証
        assert item["match_score"] == mock_match_snapshot_data["match_score"]
        assert item["must_requirements_ok"] == mock_match_snapshot_data["must_requirements_ok"]
        assert item["budget_match_ok"] == mock_match_snapshot_data["budget_match_ok"]
        assert item["region_match_ok"] == mock_match_snapshot_data["region_match_ok"]

    def test_マッチングスコア付きRFP取得_会社情報が存在しない(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
    ):
        """会社情報が存在しない場合、404エラーが返されることを確認"""
        # 会社情報のモック（存在しない）
        company_response = MagicMock()
        company_response.data = None

        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        # APIリクエスト
        response = client.get("/api/rfps/with-matching")

        # レスポンス検証
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "会社情報が見つかりません" in response.json()["detail"]

    def test_マッチングスコア付きRFP取得_最小スコアフィルタ(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        mock_match_snapshot_data: dict,
    ):
        """最小スコアフィルタが適用されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショットのモック
        match_with_rfp = {
            **mock_match_snapshot_data,
            "rfps": {**mock_rfp_data, "embedding": [0.1] * 1536},
        }
        match_response = MagicMock()
        match_response.data = [match_with_rfp]
        match_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_gte = mock_eq.gte.return_value
        mock_order = mock_gte.order.return_value
        mock_range = mock_order.range
        mock_range.return_value.execute.return_value = match_response

        # APIリクエスト（最小スコア80以上）
        response = client.get("/api/rfps/with-matching?min_score=80")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1

        # gteメソッドが正しく呼ばれたことを確認
        mock_eq.gte.assert_called_once_with("match_score", 80)

    def test_マッチングスコア付きRFP取得_必須要件フィルタ(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        mock_match_snapshot_data: dict,
    ):
        """必須要件フィルタが適用されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショットのモック
        match_with_rfp = {
            **mock_match_snapshot_data,
            "rfps": {**mock_rfp_data, "embedding": [0.1] * 1536},
        }
        match_response = MagicMock()
        match_response.data = [match_with_rfp]
        match_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        mock_select = mock_table.select.return_value
        mock_eq1 = mock_select.eq.return_value
        mock_eq2 = mock_eq1.eq.return_value
        mock_order = mock_eq2.order.return_value
        mock_range = mock_order.range
        mock_range.return_value.execute.return_value = match_response

        # APIリクエスト（必須要件を満たす案件のみ）
        response = client.get("/api/rfps/with-matching?must_requirements_only=true")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1

        # 必須要件フィルタが適用されたことを確認（2回目のeq呼び出し）
        assert mock_eq1.eq.call_count >= 1

    def test_マッチングスコア付きRFP取得_締切日フィルタ(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        mock_match_snapshot_data: dict,
    ):
        """締切日フィルタ（指定日数以内）が適用されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショットのモック
        match_with_rfp = {
            **mock_match_snapshot_data,
            "rfps": {**mock_rfp_data, "embedding": [0.1] * 1536},
        }
        match_response = MagicMock()
        match_response.data = [match_with_rfp]
        match_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_gte = mock_eq.gte.return_value
        mock_lte = mock_gte.lte.return_value
        mock_order = mock_lte.order.return_value
        mock_range = mock_order.range
        mock_range.return_value.execute.return_value = match_response

        # APIリクエスト（7日以内に締切）
        response = client.get("/api/rfps/with-matching?deadline_days=7")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1

        # 締切日フィルタが適用されたことを確認
        assert mock_eq.gte.call_count >= 1
        assert mock_gte.lte.call_count >= 1

    def test_マッチングスコア付きRFP取得_予算フィルタ(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        mock_match_snapshot_data: dict,
    ):
        """予算フィルタ（最小値・最大値）が適用されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショットのモック
        match_with_rfp = {
            **mock_match_snapshot_data,
            "rfps": {**mock_rfp_data, "embedding": [0.1] * 1536},
        }
        match_response = MagicMock()
        match_response.data = [match_with_rfp]
        match_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_gte = mock_eq.gte.return_value
        mock_lte = mock_gte.lte.return_value
        mock_order = mock_lte.order.return_value
        mock_range = mock_order.range
        mock_range.return_value.execute.return_value = match_response

        # APIリクエスト（予算500万円〜1000万円）
        response = client.get("/api/rfps/with-matching?budget_min=5000000&budget_max=10000000")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1

        # 予算フィルタが適用されたことを確認
        assert mock_eq.gte.call_count >= 1
        assert mock_gte.lte.call_count >= 1

    def test_マッチングスコア付きRFP取得_複数フィルタ組み合わせ(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        mock_match_snapshot_data: dict,
    ):
        """複数のフィルタを組み合わせた場合に正しく動作することを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショットのモック
        match_with_rfp = {
            **mock_match_snapshot_data,
            "rfps": {**mock_rfp_data, "embedding": [0.1] * 1536},
        }
        match_response = MagicMock()
        match_response.data = [match_with_rfp]
        match_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        # 複雑なチェーンのモック
        mock_select = mock_table.select.return_value
        mock_eq1 = mock_select.eq.return_value
        mock_gte1 = mock_eq1.gte.return_value
        mock_eq2 = mock_gte1.eq.return_value
        mock_order = mock_eq2.order.return_value
        mock_range = mock_order.range
        mock_range.return_value.execute.return_value = match_response

        # APIリクエスト（複数フィルタ組み合わせ）
        response = client.get(
            "/api/rfps/with-matching?min_score=70&must_requirements_only=true"
        )

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1

    def test_マッチングスコア付きRFP取得_空リスト(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
    ):
        """マッチング結果が存在しない場合、空リストが返されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = {"id": mock_company_data["id"]}

        # マッチングスナップショット一覧のモック（空）
        match_response = MagicMock()
        match_response.data = []
        match_response.count = 0

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = (
            match_response
        )

        # APIリクエスト
        response = client.get("/api/rfps/with-matching")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


@pytest.mark.unit
class TestGenerateProposalDraft:
    """提案書ドラフト生成APIのテストクラス"""

    def test_提案書ドラフト生成_正常系_基本情報のみ(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
    ):
        """基本情報のみで提案書ドラフトが正常に生成されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_data = {
            **mock_company_data,
            "skills": ["Python", "FastAPI", "React", "TypeScript"],
        }
        company_response.data = company_data

        # RFP情報のモック
        rfp_response = MagicMock()
        rfp_response.data = mock_rfp_data

        # マッチング情報のモック（存在しない）
        match_response = MagicMock()
        match_response.data = []

        # モックの設定
        mock_table = mock_supabase_client.table.return_value

        # 会社情報、RFP情報、マッチング情報の順に返す
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = [
            company_response,  # 会社情報
            rfp_response,  # RFP情報
        ]

        # マッチング情報のモック
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
            match_response
        )

        # APIリクエスト
        response = client.get(f"/api/rfps/{mock_rfp_data['id']}/proposal/draft")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # 生成された提案書のチェック
        draft = response.text
        assert len(draft) > 0

        # RFP情報が含まれていることを確認
        assert mock_rfp_data["title"] in draft
        assert mock_rfp_data["issuing_org"] in draft

        # 会社情報が含まれていることを確認
        assert company_data["name"] in draft

    def test_提案書ドラフト生成_正常系_マッチング情報あり(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
        test_user_id: str,
    ):
        """マッチング情報ありで提案書ドラフトが正常に生成されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_data = {
            **mock_company_data,
            "skills": ["Python", "FastAPI", "React"],
        }
        company_response.data = company_data

        # RFP情報のモック
        rfp_response = MagicMock()
        rfp_response.data = mock_rfp_data

        # マッチング情報のモック（存在する）
        match_data = {
            "score": 85,
            "summary_points": [
                "予算条件が適合しています",
                "地域条件が適合しています",
            ],
        }
        match_response = MagicMock()
        match_response.data = [match_data]

        # モックの設定
        mock_table = mock_supabase_client.table.return_value

        # 会社情報、RFP情報の順に返す
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = [
            company_response,  # 会社情報
            rfp_response,  # RFP情報
        ]

        # マッチング情報のモック
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
            match_response
        )

        # APIリクエスト
        response = client.get(f"/api/rfps/{mock_rfp_data['id']}/proposal/draft")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK

        # 生成された提案書のチェック
        draft = response.text
        assert len(draft) > 0

        # マッチング情報が含まれていることを確認
        assert "85点" in draft
        for point in match_data["summary_points"]:
            assert point in draft

    def test_提案書ドラフト生成_異常系_会社情報が存在しない(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_rfp_data: dict,
    ):
        """会社情報が存在しない場合、404エラーが返されることを確認"""
        # 会社情報のモック（存在しない）
        company_response = MagicMock()
        company_response.data = None

        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            company_response
        )

        # APIリクエスト
        response = client.get(f"/api/rfps/{mock_rfp_data['id']}/proposal/draft")

        # レスポンス検証
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        # エラーレスポンスの形式を確認
        if "detail" in response_data:
            assert "会社情報が見つかりません" in response_data["detail"]
        else:
            assert "会社情報が見つかりません" in str(response_data)

    def test_提案書ドラフト生成_異常系_RFPが存在しない(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
    ):
        """RFPが存在しない場合、404エラーが返されることを確認"""
        # 会社情報のモック
        company_response = MagicMock()
        company_response.data = mock_company_data

        # RFP情報のモック（存在しない）
        rfp_response = MagicMock()
        rfp_response.data = None

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = [
            company_response,  # 会社情報
            rfp_response,  # RFP情報（存在しない）
        ]

        # APIリクエスト
        response = client.get("/api/rfps/non-existent-rfp-id/proposal/draft")

        # レスポンス検証
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        # エラーレスポンスの形式を確認
        if "detail" in response_data:
            assert "RFPが見つかりません" in response_data["detail"]
        else:
            assert "RFPが見つかりません" in str(response_data)

    def test_提案書ドラフト生成_正常系_予算がNone(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
    ):
        """予算がNoneの場合でも正常に生成されることを確認"""
        # RFPデータの予算をNoneに
        rfp_data_no_budget = {**mock_rfp_data, "budget": None}

        # 会社情報のモック
        company_response = MagicMock()
        company_data = {
            **mock_company_data,
            "skills": ["Python", "FastAPI"],
        }
        company_response.data = company_data

        # RFP情報のモック
        rfp_response = MagicMock()
        rfp_response.data = rfp_data_no_budget

        # マッチング情報のモック（存在しない）
        match_response = MagicMock()
        match_response.data = []

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = [
            company_response,  # 会社情報
            rfp_response,  # RFP情報
        ]
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
            match_response
        )

        # APIリクエスト
        response = client.get(f"/api/rfps/{rfp_data_no_budget['id']}/proposal/draft")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK

        # 生成された提案書のチェック
        draft = response.text
        assert len(draft) > 0
        assert "未定" in draft  # 予算が「未定」と表示されることを確認

    def test_提案書ドラフト生成_正常系_外部ドキュメントURLなし(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_company_data: dict,
        mock_rfp_data: dict,
    ):
        """外部ドキュメントURLがない場合でも正常に生成されることを確認"""
        # RFPデータの外部ドキュメントURLを空に
        rfp_data_no_docs = {**mock_rfp_data, "external_doc_urls": []}

        # 会社情報のモック
        company_response = MagicMock()
        company_data = {
            **mock_company_data,
            "skills": ["Python"],
        }
        company_response.data = company_data

        # RFP情報のモック
        rfp_response = MagicMock()
        rfp_response.data = rfp_data_no_docs

        # マッチング情報のモック（存在しない）
        match_response = MagicMock()
        match_response.data = []

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = [
            company_response,  # 会社情報
            rfp_response,  # RFP情報
        ]
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
            match_response
        )

        # APIリクエスト
        response = client.get(f"/api/rfps/{rfp_data_no_docs['id']}/proposal/draft")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK

        # 生成された提案書のチェック
        draft = response.text
        assert len(draft) > 0
        assert "外部資料なし" in draft
