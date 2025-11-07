"""
マッチング機能のAPIエンドポイント

会社とRFP案件のマッチング結果を提供します。
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from database import get_supabase_client
from middleware.auth import CurrentUserId
from schemas.matching import MatchingListResponse, MatchingFactors, RFPWithMatchingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/me/matching",
    response_model=MatchingListResponse,
    summary="自社のマッチング結果取得",
    description="ログインユーザーの会社に対するRFP案件のマッチング結果を取得します。",
)
async def get_my_matching_results(
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    page: Annotated[int, Query(ge=1, description="ページ番号")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="ページサイズ")] = 20,
    min_score: Annotated[int | None, Query(ge=0, le=100, description="最小マッチングスコア")] = None,
    must_requirements_only: Annotated[
        bool, Query(description="必須要件を満たす案件のみ表示")
    ] = False,
    sort_by: Annotated[
        str, Query(description="ソート基準（score: スコア降順, deadline: 締切昇順）")
    ] = "score",
):
    """
    ログインユーザーの会社に対するマッチング結果を取得します。

    Args:
        user_id: 現在のユーザーID（依存性注入）
        supabase: Supabaseクライアント（依存性注入）
        page: ページ番号（1から始まる）
        page_size: 1ページあたりの件数（最大100）
        min_score: 最小マッチングスコア（フィルタリング用）
        must_requirements_only: 必須要件を満たす案件のみ表示するか
        sort_by: ソート基準（score: スコア降順, deadline: 締切昇順）

    Returns:
        MatchingListResponse: マッチング結果一覧

    Raises:
        HTTPException: 会社情報が見つからない、データベースエラー等
    """
    try:
        # ユーザーの会社情報を取得
        company_response = (
            supabase.table("companies")
            .select("id")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        if not company_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会社情報が見つかりません。先にプロフィールを登録してください。",
            )

        company_id = company_response.data["id"]

        # マッチングスナップショットとRFP情報を結合して取得
        query = (
            supabase.table("match_snapshots")
            .select(
                """
                id,
                match_score,
                must_requirements_ok,
                budget_match_ok,
                region_match_ok,
                match_factors,
                summary_points,
                updated_at,
                rfps:rfp_id (
                    id,
                    external_id,
                    title,
                    description,
                    organization,
                    prefecture,
                    budget,
                    deadline,
                    source_url
                )
            """
            )
            .eq("company_id", company_id)
        )

        # フィルタリング条件を適用
        if min_score is not None:
            query = query.gte("match_score", min_score)

        if must_requirements_only:
            query = query.eq("must_requirements_ok", True)

        # ソート順を適用
        if sort_by == "deadline":
            # 締切昇順（NULLは最後）
            query = query.order("rfps.deadline", desc=False, nulls_last=True)
        else:
            # デフォルト: スコア降順
            query = query.order("match_score", desc=True)

        # ページネーション用のオフセット計算
        offset = (page - 1) * page_size

        # 総件数を取得（フィルタリング適用後）
        count_query = (
            supabase.table("match_snapshots")
            .select("id", count="exact")
            .eq("company_id", company_id)
        )

        if min_score is not None:
            count_query = count_query.gte("match_score", min_score)

        if must_requirements_only:
            count_query = count_query.eq("must_requirements_ok", True)

        count_response = count_query.execute()
        total = count_response.count or 0

        # データ取得（ページネーション適用）
        data_response = query.range(offset, offset + page_size - 1).execute()

        # レスポンスの整形
        matches = []
        for record in data_response.data:
            rfp_data = record.get("rfps")
            if not rfp_data:
                logger.warning(f"RFP data not found for match_snapshot: {record['id']}")
                continue

            match_result = RFPWithMatchingResponse(
                # RFP情報
                id=rfp_data["id"],
                external_id=rfp_data["external_id"],
                title=rfp_data["title"],
                description=rfp_data["description"],
                organization=rfp_data["organization"],
                prefecture=rfp_data["prefecture"],
                budget=rfp_data.get("budget"),
                deadline=rfp_data.get("deadline"),
                source_url=rfp_data.get("source_url"),
                # マッチング情報
                match_score=record["match_score"],
                must_requirements_ok=record["must_requirements_ok"],
                budget_match_ok=record["budget_match_ok"],
                region_match_ok=record["region_match_ok"],
                match_factors=MatchingFactors(**record["match_factors"]),
                summary_points=record.get("summary_points", []),
                match_calculated_at=record["updated_at"],
            )
            matches.append(match_result)

        return MatchingListResponse(
            matches=matches,
            total=total,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching matching results for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="マッチング結果の取得中にエラーが発生しました",
        ) from e
