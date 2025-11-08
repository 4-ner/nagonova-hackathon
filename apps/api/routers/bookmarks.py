"""
ブックマーク管理APIルーター

RFPのブックマーク機能（追加・削除・一覧取得）を提供します。
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from database import get_supabase_client
from middleware.auth import CurrentUserId
from schemas.bookmark import (
    BookmarkCreate,
    BookmarkResponse,
    BookmarkWithRFPResponse,
    BookmarkListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/bookmarks",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ブックマークを作成",
    description="指定されたRFPをブックマークします。既にブックマーク済みの場合は既存のブックマークを返却します（冪等性）。",
)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> BookmarkResponse:
    """
    ブックマーク作成

    Args:
        bookmark_data: ブックマーク作成データ
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        BookmarkResponse: 作成されたブックマーク

    Raises:
        HTTPException: RFPが見つからない、または作成エラー
    """
    try:
        # RFPの存在確認
        rfp_response = (
            supabase.table("rfps")
            .select("id")
            .eq("id", bookmark_data.rfp_id)
            .execute()
        )

        if not rfp_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたRFPが見つかりません",
            )

        # 既存のブックマークを確認（冪等性のため）
        existing_bookmark = (
            supabase.table("bookmarks")
            .select("*")
            .eq("user_id", user_id)
            .eq("rfp_id", bookmark_data.rfp_id)
            .execute()
        )

        # 既にブックマーク済みの場合は既存のものを返却
        if existing_bookmark.data:
            logger.info(
                f"既存のブックマークを返却しました: user_id={user_id}, rfp_id={bookmark_data.rfp_id}"
            )
            return BookmarkResponse(**existing_bookmark.data[0])

        # ブックマーク作成
        insert_data = {
            "user_id": user_id,
            "rfp_id": bookmark_data.rfp_id,
        }

        response = supabase.table("bookmarks").insert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ブックマークの作成に失敗しました",
            )

        logger.info(
            f"ブックマークを作成しました: user_id={user_id}, rfp_id={bookmark_data.rfp_id}, "
            f"bookmark_id={response.data[0]['id']}"
        )

        return BookmarkResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ブックマーク作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ブックマークの作成に失敗しました",
        )


@router.delete(
    "/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ブックマークを削除",
    description="指定されたブックマークを削除します。自分のブックマークのみ削除可能です。",
)
async def delete_bookmark(
    bookmark_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> None:
    """
    ブックマーク削除

    Args:
        bookmark_id: ブックマークID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Raises:
        HTTPException: ブックマークが見つからない、または削除エラー
    """
    try:
        # ブックマークの存在確認と所有権チェック
        bookmark_response = (
            supabase.table("bookmarks")
            .select("id")
            .eq("id", bookmark_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not bookmark_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ブックマークが見つかりません",
            )

        # ブックマーク削除
        delete_response = (
            supabase.table("bookmarks")
            .delete()
            .eq("id", bookmark_id)
            .eq("user_id", user_id)
            .execute()
        )

        logger.info(f"ブックマークを削除しました: bookmark_id={bookmark_id}, user_id={user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ブックマーク削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ブックマークの削除に失敗しました",
        )


@router.get(
    "/bookmarks",
    response_model=BookmarkListResponse,
    summary="ブックマーク一覧を取得",
    description="認証されたユーザーのブックマークしたRFP一覧を取得します。RFP情報を含みます。",
)
async def get_bookmarks(
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
) -> BookmarkListResponse:
    """
    ブックマーク一覧取得

    Args:
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        page: ページ番号（デフォルト: 1）
        page_size: ページサイズ（デフォルト: 20、最大: 100）

    Returns:
        BookmarkListResponse: ブックマーク一覧（RFP情報を含む）

    Raises:
        HTTPException: 取得エラー
    """
    try:
        # オフセット計算
        offset = (page - 1) * page_size

        # ブックマーク一覧とRFP情報を結合して取得
        query_builder = (
            supabase.table("bookmarks")
            .select(
                """
                id,
                user_id,
                rfp_id,
                created_at,
                rfps:rfp_id (
                    id,
                    external_id,
                    title,
                    issuing_org,
                    description,
                    budget,
                    region,
                    deadline,
                    url,
                    external_doc_urls,
                    embedding,
                    created_at,
                    updated_at,
                    fetched_at
                )
            """,
                count="exact",
            )
            .eq("user_id", user_id)
        )

        # 作成日時の降順でソート（最近ブックマークしたものが上）
        query_builder = query_builder.order("created_at", desc=True)

        # ページネーション
        query_builder = query_builder.range(offset, offset + page_size - 1)

        # クエリ実行
        response = query_builder.execute()

        # レスポンスの整形
        items = []
        for record in response.data:
            rfp_data = record.get("rfps")
            if not rfp_data:
                logger.warning(
                    f"RFP data not found for bookmark_id={record.get('id')}, "
                    f"rfp_id={record.get('rfp_id')}"
                )
                continue

            # has_embeddingフィールドを追加
            rfp_data["has_embedding"] = rfp_data.get("embedding") is not None

            # ブックマーク情報とRFP情報を結合
            item = BookmarkWithRFPResponse(
                id=record["id"],
                user_id=record["user_id"],
                rfp_id=record["rfp_id"],
                created_at=record["created_at"],
                rfp=rfp_data,
            )
            items.append(item)

        total = response.count if response.count is not None else 0

        logger.info(
            f"ブックマーク一覧を取得しました: user_id={user_id}, total={total}, "
            f"page={page}, page_size={page_size}"
        )

        return BookmarkListResponse(
            total=total,
            items=items,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"ブックマーク一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ブックマーク一覧の取得に失敗しました",
        )


@router.delete(
    "/bookmarks/rfp/{rfp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ブックマークを削除（RFP ID指定）",
    description="指定されたRFP IDのブックマークを削除します。自分のブックマークのみ削除可能です。",
)
async def delete_bookmark_by_rfp(
    rfp_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> None:
    """
    ブックマーク削除（RFP ID指定）

    Args:
        rfp_id: RFP ID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Raises:
        HTTPException: ブックマークが見つからない、または削除エラー
    """
    try:
        # ブックマークの存在確認と所有権チェック
        bookmark_response = (
            supabase.table("bookmarks")
            .select("id")
            .eq("rfp_id", rfp_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not bookmark_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ブックマークが見つかりません",
            )

        # ブックマーク削除
        delete_response = (
            supabase.table("bookmarks")
            .delete()
            .eq("rfp_id", rfp_id)
            .eq("user_id", user_id)
            .execute()
        )

        logger.info(f"ブックマークを削除しました: rfp_id={rfp_id}, user_id={user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ブックマーク削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ブックマークの削除に失敗しました",
        )


@router.get(
    "/bookmarks/check/{rfp_id}",
    summary="ブックマーク済みかチェック",
    description="指定されたRFPがブックマーク済みかどうかをチェックします。",
)
async def check_bookmark(
    rfp_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> dict:
    """
    ブックマーク済みかチェック

    Args:
        rfp_id: RFP ID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        dict: {"is_bookmarked": bool, "bookmark_id": str | null}

    Raises:
        HTTPException: 取得エラー
    """
    try:
        bookmark_response = (
            supabase.table("bookmarks")
            .select("id")
            .eq("rfp_id", rfp_id)
            .eq("user_id", user_id)
            .execute()
        )

        is_bookmarked = len(bookmark_response.data) > 0
        bookmark_id = bookmark_response.data[0]["id"] if is_bookmarked else None

        return {
            "is_bookmarked": is_bookmarked,
            "bookmark_id": bookmark_id,
        }

    except Exception as e:
        logger.error(f"ブックマークチェックエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ブックマークチェックに失敗しました",
        )
