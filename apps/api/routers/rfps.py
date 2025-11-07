"""
RFP管理APIルーター

RFPの参照操作と管理者用のRFP取得トリガーを提供します。
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from supabase import Client

from database import get_supabase_client
from middleware.auth import CurrentUserId
from schemas.rfp import RFPResponse, RFPListResponse, IngestRequest, IngestResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/rfps",
    response_model=RFPListResponse,
    summary="RFP一覧を取得",
    description="認証されたユーザーがRFP一覧を取得します。ページネーション、フィルタリングに対応しています。",
)
async def get_rfps(
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    region: str | None = Query(None, description="都道府県コードフィルター"),
    query: str | None = Query(None, description="タイトル・説明文での検索"),
) -> RFPListResponse:
    """
    RFP一覧取得

    Args:
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        page: ページ番号（デフォルト: 1）
        page_size: ページサイズ（デフォルト: 20、最大: 100）
        region: 都道府県コードフィルター（オプション）
        query: タイトル・説明文での検索（オプション）

    Returns:
        RFPListResponse: RFP一覧

    Raises:
        HTTPException: 取得エラー
    """
    try:
        # オフセット計算
        offset = (page - 1) * page_size

        # ベースクエリ（embeddingが存在するRFPのみ）
        query_builder = supabase.table("rfps").select("*", count="exact").is_("embedding", "not.null")

        # 地域フィルタ
        if region:
            query_builder = query_builder.eq("region", region)

        # テキスト検索フィルタ（タイトルまたは説明文）
        if query:
            # PostgreSQLのILIKEを使用して部分一致検索
            query_builder = query_builder.or_(
                f"title.ilike.%{query}%,description.ilike.%{query}%"
            )

        # ページネーション
        query_builder = query_builder.range(offset, offset + page_size - 1).order("fetched_at", desc=True)

        # クエリ実行
        response = query_builder.execute()

        # RFPデータを整形（has_embeddingフィールドを追加）
        items = []
        for rfp in response.data:
            rfp_data = {**rfp, "has_embedding": True}  # embeddingフィルタ済みなので常にTrue
            items.append(RFPResponse(**rfp_data))

        total = response.count if response.count is not None else 0

        logger.info(
            f"RFP一覧を取得しました: user_id={user_id}, total={total}, page={page}, page_size={page_size}"
        )

        return RFPListResponse(
            total=total,
            items=items,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RFP一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RFP一覧の取得に失敗しました",
        )


@router.get(
    "/rfps/{rfp_id}",
    response_model=RFPResponse,
    summary="RFP詳細を取得",
    description="認証されたユーザーが指定されたRFPの詳細情報を取得します。",
)
async def get_rfp(
    rfp_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> RFPResponse:
    """
    RFP詳細取得

    Args:
        rfp_id: RFP UUID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        RFPResponse: RFP詳細情報

    Raises:
        HTTPException: RFPが存在しない場合や取得エラー
    """
    try:
        response = supabase.table("rfps").select("*").eq("id", rfp_id).execute()

        if not response.data:
            logger.info(f"RFPが見つかりません: rfp_id={rfp_id}, user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFPが見つかりません",
            )

        rfp = response.data[0]
        # has_embeddingフィールドを追加
        rfp_data = {**rfp, "has_embedding": rfp.get("embedding") is not None}

        logger.debug(f"RFP詳細を取得しました: rfp_id={rfp_id}, user_id={user_id}")

        return RFPResponse(**rfp_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RFP詳細取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RFP詳細の取得に失敗しました",
        )


@router.post(
    "/admin/ingest/kkj",
    response_model=IngestResponse,
    summary="管理者用RFP取得トリガー",
    description="管理者がKKJ APIからRFPを取得するバッチ処理をトリガーします。",
)
async def ingest_rfps_from_kkj(
    ingest_data: IngestRequest,
    background_tasks: BackgroundTasks,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> IngestResponse:
    """
    管理者用RFP取得トリガー

    Args:
        ingest_data: RFP取得リクエストデータ
        background_tasks: FastAPIバックグラウンドタスク
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        IngestResponse: 処理開始レスポンス

    Raises:
        HTTPException: 処理エラー
    """
    try:
        # TODO: 管理者権限チェック（現在は省略）

        # バックグラウンドタスクとして実行
        # TODO: 実際のKKJ APIクライアント呼び出しまたはバッチスクリプト実行
        # background_tasks.add_task(run_kkj_batch, ingest_data)

        logger.info(
            f"RFP取得処理を開始しました: user_id={user_id}, "
            f"prefectures={ingest_data.prefectures}, count={ingest_data.count}"
        )

        return IngestResponse(
            status="started",
            message=f"RFP取得処理を開始しました（都道府県: {', '.join(ingest_data.prefectures)}, 件数: {ingest_data.count}）",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RFP取得処理エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RFP取得処理の開始に失敗しました",
        )
