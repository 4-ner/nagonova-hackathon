"""
RFP管理APIルーター

RFPの参照操作と管理者用のRFP取得トリガーを提供します。
"""
import logging
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
from supabase import Client

from database import get_supabase_client
from middleware.auth import CurrentUserId
from schemas.rfp import (
    RFPResponse,
    RFPListResponse,
    RFPWithMatchingResponse,
    RFPWithMatchingListResponse,
    IngestRequest,
    IngestResponse,
)
from services.proposal_generator import ProposalGenerator

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
    category: str | None = Query(None, description="案件カテゴリでフィルタ"),
    procedure_type: str | None = Query(None, description="入札手続きの種類でフィルタ"),
    item_code: str | None = Query(None, description="品目分類コードでフィルタ"),
    lg_code: str | None = Query(None, description="地方自治体コード（都道府県）でフィルタ"),
    city_code: str | None = Query(None, description="市区町村コードでフィルタ"),
    certification_query: str | None = Query(None, description="参加資格情報での全文検索"),
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
        category: 案件カテゴリでフィルタ（オプション）
        procedure_type: 入札手続きの種類でフィルタ（オプション）
        item_code: 品目分類コードでフィルタ（オプション）
        lg_code: 地方自治体コード（都道府県）でフィルタ（オプション）
        city_code: 市区町村コードでフィルタ（オプション）
        certification_query: 参加資格情報での全文検索（オプション）

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

        # カテゴリフィルタ
        if category:
            query_builder = query_builder.eq("category", category)

        # 入札手続きの種類フィルタ
        if procedure_type:
            query_builder = query_builder.eq("procedure_type", procedure_type)

        # 品目分類コードフィルタ
        if item_code:
            query_builder = query_builder.eq("item_code", item_code)

        # 地方自治体コード（都道府県）フィルタ
        if lg_code:
            query_builder = query_builder.eq("lg_code", lg_code)

        # 市区町村コードフィルタ
        if city_code:
            query_builder = query_builder.eq("city_code", city_code)

        # 参加資格情報での全文検索フィルタ
        if certification_query:
            # PostgreSQLのILIKEを使用して部分一致検索
            query_builder = query_builder.ilike("certification", f"%{certification_query}%")

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
            f"RFP一覧を取得しました: user_id={user_id}, total={total}, page={page}, page_size={page_size}, "
            f"region={region}, query={query}, category={category}, procedure_type={procedure_type}, "
            f"item_code={item_code}, lg_code={lg_code}, city_code={city_code}, certification_query={certification_query}"
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
    "/rfps/with-matching",
    response_model=RFPWithMatchingListResponse,
    summary="マッチングスコア付きRFP一覧を取得",
    description="認証されたユーザーのマッチングスコア付きでRFP一覧を取得します。",
)
async def get_rfps_with_matching(
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    min_score: int | None = Query(None, ge=0, le=100, description="最小マッチングスコア"),
    must_requirements_only: bool = Query(False, description="必須要件を満たす案件のみ表示"),
    deadline_days: int | None = Query(None, ge=1, description="指定日数以内に締切がある案件のみ表示（7, 14, 30など）"),
    budget_min: int | None = Query(None, ge=0, description="予算の最小値（円）"),
    budget_max: int | None = Query(None, ge=0, description="予算の最大値（円）"),
) -> RFPWithMatchingListResponse:
    """
    マッチングスコア付きRFP一覧取得

    ログインユーザーの会社情報に基づいたマッチングスコア付きでRFP一覧を取得します。

    Args:
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        page: ページ番号（デフォルト: 1）
        page_size: ページサイズ（デフォルト: 20、最大: 100）
        min_score: 最小マッチングスコア（オプション）
        must_requirements_only: 必須要件を満たす案件のみ表示（デフォルト: False）
        deadline_days: 指定日数以内に締切がある案件のみ表示（オプション、例: 7, 14, 30）
        budget_min: 予算の最小値（円）（オプション）
        budget_max: 予算の最大値（円）（オプション）

    Returns:
        RFPWithMatchingListResponse: マッチングスコア付きRFP一覧

    Raises:
        HTTPException: 会社情報が見つからない、取得エラー
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

        # オフセット計算
        offset = (page - 1) * page_size

        # マッチングスナップショットとRFP情報を結合して取得
        query_builder = (
            supabase.table("match_snapshots")
            .select(
                """
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
                    issuing_org,
                    description,
                    budget,
                    region,
                    deadline,
                    url,
                    external_doc_urls,
                    has_embedding,
                    created_at,
                    updated_at,
                    fetched_at
                )
            """,
                count="exact",
            )
            .eq("company_id", company_id)
        )

        # フィルタリング条件を適用
        if min_score is not None:
            query_builder = query_builder.gte("match_score", min_score)

        if must_requirements_only:
            query_builder = query_builder.eq("must_requirements_ok", True)

        # 締切日フィルタ（指定日数以内に締切がある案件のみ）
        if deadline_days is not None:
            # Pythonで日付を計算してフィルタリング
            today = date.today()
            deadline_date = today + timedelta(days=deadline_days)

            query_builder = query_builder.gte("rfps.deadline", str(today))
            query_builder = query_builder.lte("rfps.deadline", str(deadline_date))

        # 予算最小値フィルタ（NULLは除外）
        if budget_min is not None:
            query_builder = query_builder.gte("rfps.budget", budget_min)

        # 予算最大値フィルタ（NULLは除外）
        if budget_max is not None:
            query_builder = query_builder.lte("rfps.budget", budget_max)

        # スコア降順でソート
        query_builder = query_builder.order("match_score", desc=True)

        # ページネーション
        query_builder = query_builder.range(offset, offset + page_size - 1)

        # クエリ実行
        response = query_builder.execute()

        # レスポンスの整形
        items = []
        for record in response.data:
            rfp_data = record.get("rfps")
            if not rfp_data:
                logger.warning(f"RFP data not found for match_snapshot with company_id={company_id}")
                continue

            # RFP情報とマッチング情報を結合
            item = RFPWithMatchingResponse(
                # RFP基本情報
                id=rfp_data["id"],
                external_id=rfp_data["external_id"],
                title=rfp_data["title"],
                issuing_org=rfp_data["issuing_org"],
                description=rfp_data["description"],
                budget=rfp_data.get("budget"),
                region=rfp_data["region"],
                deadline=rfp_data["deadline"],
                url=rfp_data.get("url"),
                external_doc_urls=rfp_data.get("external_doc_urls", []),
                has_embedding=rfp_data.get("embedding") is not None,
                created_at=rfp_data["created_at"],
                updated_at=rfp_data["updated_at"],
                fetched_at=rfp_data["fetched_at"],
                # マッチング情報
                match_score=record["match_score"],
                must_requirements_ok=record["must_requirements_ok"],
                budget_match_ok=record["budget_match_ok"],
                region_match_ok=record["region_match_ok"],
                match_factors=record["match_factors"],
                summary_points=record.get("summary_points", []),
                match_calculated_at=record["updated_at"],
            )
            items.append(item)

        total = response.count if response.count is not None else 0

        logger.info(
            f"マッチングスコア付きRFP一覧を取得しました: user_id={user_id}, company_id={company_id}, "
            f"total={total}, page={page}, page_size={page_size}, "
            f"min_score={min_score}, must_requirements_only={must_requirements_only}, "
            f"deadline_days={deadline_days}, budget_min={budget_min}, budget_max={budget_max}"
        )

        return RFPWithMatchingListResponse(
            total=total,
            items=items,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"マッチングスコア付きRFP一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="マッチングスコア付きRFP一覧の取得に失敗しました",
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


@router.get(
    "/rfps/{rfp_id}/proposal/draft",
    response_class=PlainTextResponse,
    summary="提案書ドラフトを生成",
    description="指定されたRFPに対する提案書ドラフトをMarkdown形式で生成します。",
)
async def generate_proposal_draft(
    rfp_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> str:
    """
    提案書ドラフト生成

    認証ユーザーの会社情報とRFP情報を元に、提案書のドラフトを
    Markdown形式で生成します。マッチング情報が存在する場合は、
    マッチングスコアとサマリーポイントも含めます。

    Args:
        rfp_id: RFP UUID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        str: 提案書ドラフトのMarkdown文字列

    Raises:
        HTTPException: 会社情報が未登録、RFPが存在しない、生成エラー
    """
    try:
        # ユーザーの会社情報を取得
        company_response = (
            supabase.table("companies")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        if not company_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会社情報が見つかりません。先にプロフィールを登録してください。",
            )

        company = company_response.data

        # RFP情報を取得
        rfp_response = (
            supabase.table("rfps")
            .select("*")
            .eq("id", rfp_id)
            .maybe_single()
            .execute()
        )

        if not rfp_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFPが見つかりません",
            )

        rfp = rfp_response.data

        # マッチング情報を取得（オプション）
        match_score = None
        summary_points = None

        match_response = (
            supabase.table("match_snapshots")
            .select("match_score, summary_points")
            .eq("company_id", company["id"])
            .eq("rfp_id", rfp_id)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )

        if match_response.data and len(match_response.data) > 0:
            match_data = match_response.data[0]
            match_score = match_data.get("match_score")
            summary_points = match_data.get("summary_points", [])

        # ProposalGeneratorを初期化して提案書を生成
        generator = ProposalGenerator()
        proposal_markdown = generator.generate_proposal_draft(
            rfp=rfp,
            company=company,
            match_score=match_score,
            summary_points=summary_points,
        )

        logger.info(
            f"提案書ドラフトを生成しました: user_id={user_id}, rfp_id={rfp_id}, "
            f"length={len(proposal_markdown)}"
        )

        return proposal_markdown

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"提案書ドラフト生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提案書ドラフトの生成に失敗しました",
        )
