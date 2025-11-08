"""
ブックマークAPIのテストケース

ブックマークの作成、削除、一覧取得をテストします。
"""
import pytest
from unittest.mock import MagicMock
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestCreateBookmark:
    """ブックマーク作成APIのテストクラス"""

    def test_ブックマーク作成_正常系(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_rfp_data: dict,
        mock_bookmark_data: dict,
    ):
        """ブックマークが正常に作成されることを確認"""
        # RFP存在確認のモック
        rfp_response = MagicMock()
        rfp_response.data = [{"id": mock_rfp_data["id"]}]

        # 既存ブックマークチェックのモック（存在しない）
        existing_bookmark_response = MagicMock()
        existing_bookmark_response.data = []

        # ブックマーク作成のモック
        create_response = MagicMock()
        create_response.data = [mock_bookmark_data]

        # モックの設定（詳細なチェーンメソッドの設定）
        mock_table = mock_supabase_client.table.return_value

        # RFP存在確認のチェーン
        rfp_select = MagicMock()
        rfp_eq = MagicMock()
        rfp_eq.execute.return_value = rfp_response
        rfp_select.eq.return_value = rfp_eq

        # 既存ブックマークチェックのチェーン
        bookmark_select = MagicMock()
        bookmark_eq1 = MagicMock()
        bookmark_eq2 = MagicMock()
        bookmark_eq2.execute.return_value = existing_bookmark_response
        bookmark_eq1.eq.return_value = bookmark_eq2
        bookmark_select.eq.return_value = bookmark_eq1

        # selectメソッドの呼び出しごとに適切なモックを返す
        mock_table.select.side_effect = [rfp_select, bookmark_select]

        # insertのチェーン
        mock_insert = MagicMock()
        mock_insert.execute.return_value = create_response
        mock_table.insert.return_value = mock_insert

        # APIリクエスト
        response = client.post(
            "/api/bookmarks",
            json={"rfp_id": mock_rfp_data["id"]},
        )

        # レスポンス検証
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == mock_bookmark_data["id"]
        assert data["rfp_id"] == mock_bookmark_data["rfp_id"]
        assert data["user_id"] == mock_bookmark_data["user_id"]

    def test_ブックマーク作成_RFPが存在しない(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
    ):
        """存在しないRFPに対してブックマーク作成時に404エラーが返されることを確認"""
        # RFP存在確認のモック（存在しない）
        rfp_response = MagicMock()
        rfp_response.data = []

        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = rfp_response

        # APIリクエスト
        response = client.post(
            "/api/bookmarks",
            json={"rfp_id": "non-existent-rfp-id"},
        )

        # レスポンス検証
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "指定されたRFPが見つかりません" in response.json()["detail"]

    def test_ブックマーク作成_既に存在する場合は既存のものを返却_冪等性(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_rfp_data: dict,
        mock_bookmark_data: dict,
    ):
        """既にブックマーク済みの場合、既存のブックマークを返却することを確認（冪等性）"""
        # RFP存在確認のモック
        rfp_response = MagicMock()
        rfp_response.data = [{"id": mock_rfp_data["id"]}]

        # 既存ブックマークチェックのモック（存在する）
        existing_bookmark_response = MagicMock()
        existing_bookmark_response.data = [mock_bookmark_data]

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.side_effect = [
            rfp_response,  # RFP存在確認
            existing_bookmark_response,  # 既存ブックマークチェック
        ]

        # APIリクエスト
        response = client.post(
            "/api/bookmarks",
            json={"rfp_id": mock_rfp_data["id"]},
        )

        # レスポンス検証
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == mock_bookmark_data["id"]
        assert data["rfp_id"] == mock_bookmark_data["rfp_id"]

        # insertが呼ばれていないことを確認（既存のものを返却）
        mock_table.insert.assert_not_called()


@pytest.mark.unit
class TestDeleteBookmark:
    """ブックマーク削除APIのテストクラス"""

    def test_ブックマーク削除_正常系(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_bookmark_data: dict,
    ):
        """ブックマークが正常に削除されることを確認"""
        # ブックマーク存在確認のモック
        bookmark_response = MagicMock()
        bookmark_response.data = [{"id": mock_bookmark_data["id"]}]

        # 削除レスポンスのモック
        delete_response = MagicMock()
        delete_response.data = []

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            bookmark_response
        )
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            delete_response
        )

        # APIリクエスト
        response = client.delete(f"/api/bookmarks/{mock_bookmark_data['id']}")

        # レスポンス検証
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_ブックマーク削除_存在しない(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
    ):
        """存在しないブックマークの削除時に404エラーが返されることを確認"""
        # ブックマーク存在確認のモック（存在しない）
        bookmark_response = MagicMock()
        bookmark_response.data = []

        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            bookmark_response
        )

        # APIリクエスト
        response = client.delete("/api/bookmarks/non-existent-bookmark-id")

        # レスポンス検証
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "ブックマークが見つかりません" in response.json()["detail"]

    def test_ブックマーク削除_他のユーザーのブックマークは削除できない(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
    ):
        """他のユーザーのブックマークは削除できないことを確認"""
        # ブックマーク存在確認のモック（他のユーザーのもの = 検索結果に含まれない）
        bookmark_response = MagicMock()
        bookmark_response.data = []

        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            bookmark_response
        )

        # APIリクエスト
        response = client.delete("/api/bookmarks/other-user-bookmark-id")

        # レスポンス検証
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "ブックマークが見つかりません" in response.json()["detail"]


@pytest.mark.unit
class TestGetBookmarks:
    """ブックマーク一覧取得APIのテストクラス"""

    def test_ブックマーク一覧取得_正常系(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_bookmark_data: dict,
        mock_rfp_data: dict,
    ):
        """ブックマーク一覧が正常に取得できることを確認"""
        # ブックマーク一覧のモックデータ（RFP情報を含む）
        bookmark_with_rfp = {
            **mock_bookmark_data,
            "rfps": {
                **mock_rfp_data,
                "has_embedding": True,
            },
        }

        # モックレスポンス
        list_response = MagicMock()
        list_response.data = [bookmark_with_rfp]
        list_response.count = 1

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = (
            list_response
        )

        # APIリクエスト
        response = client.get("/api/bookmarks?page=1&page_size=20")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == mock_bookmark_data["id"]
        assert data["items"][0]["rfp"]["id"] == mock_rfp_data["id"]

    def test_ブックマーク一覧取得_空リスト(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
    ):
        """ブックマークが存在しない場合、空リストが返されることを確認"""
        # モックレスポンス（空）
        list_response = MagicMock()
        list_response.data = []
        list_response.count = 0

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = (
            list_response
        )

        # APIリクエスト
        response = client.get("/api/bookmarks")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_ブックマーク一覧取得_ページネーション(
        self,
        client: TestClient,
        mock_supabase_client: MagicMock,
        mock_bookmark_data: dict,
        mock_rfp_data: dict,
    ):
        """ページネーションパラメータが正しく適用されることを確認"""
        # モックデータ
        bookmark_with_rfp = {
            **mock_bookmark_data,
            "rfps": {**mock_rfp_data, "has_embedding": True},
        }

        list_response = MagicMock()
        list_response.data = [bookmark_with_rfp]
        list_response.count = 50  # 合計50件

        # モックの設定
        mock_table = mock_supabase_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_order = mock_eq.order.return_value
        mock_range = mock_order.range
        mock_range.return_value.execute.return_value = list_response

        # APIリクエスト（2ページ目、10件ずつ）
        response = client.get("/api/bookmarks?page=2&page_size=10")

        # レスポンス検証
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total"] == 50

        # rangeメソッドが正しいオフセットで呼ばれたことを確認
        # page=2, page_size=10 → offset=10, range(10, 19)
        mock_range.assert_called_once_with(10, 19)
