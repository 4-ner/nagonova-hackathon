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
from middleware.auth import CurrentUserId, CurrentAuthToken
from schemas.rfp import (
    RFPResponse,
    RFPListResponse,
    RFPWithMatchingResponse,
    RFPWithMatchingListResponse,
    IngestRequest,
    IngestResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultItem,
    SimilarRFPsResponse,
)
from services.embedding import EmbeddingService
from services.matching_engine import MatchingEngine
from services.proposal_generator import ProposalGenerator
from services.vector_search import VectorSearchService

logger = logging.getLogger(__name__)

router = APIRouter()


def _escape_like_pattern(pattern: str) -> str:
    """
    LIKE検索パターンの特殊文字をエスケープします。

    PostgreSQLのLIKE検索で使用される特殊文字（%, _, \）を
    エスケープして、意図しないワイルドカード検索を防ぎます。

    Args:
        pattern: エスケープ対象の検索パターン

    Returns:
        エスケープ済みの検索パターン

    Examples:
        >>> _escape_like_pattern("test%value")
        'test\\%value'
        >>> _escape_like_pattern("100%達成")
        '100\\%達成'
    """
    return (
        pattern
        .replace("\\", "\\\\")  # バックスラッシュを最初にエスケープ
        .replace("%", "\\%")    # %をエスケープ
        .replace("_", "\\_")    # _をエスケープ
    )


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
            # SQLインジェクション対策：LIKE特殊文字をエスケープ
            escaped_query = _escape_like_pattern(query)
            query_builder = query_builder.or_(
                f"title.ilike.%{escaped_query}%,description.ilike.%{escaped_query}%"
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
            # SQLインジェクション対策：LIKE特殊文字をエスケープ
            escaped_cert = _escape_like_pattern(certification_query)
            query_builder = query_builder.ilike("certification", f"%{escaped_cert}%")

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
    auth_token: CurrentAuthToken,
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
        auth_token: 認証トークン
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
        # トークン付きSupabaseクライアントを取得
        supabase = await get_supabase_client(token=auth_token)

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
                    fetched_at,
                    category,
                    procedure_type,
                    cft_issue_date,
                    tender_deadline,
                    opening_event_date,
                    item_code,
                    lg_code,
                    city_code,
                    certification
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
                # KKJ API新規フィールド
                category=rfp_data.get("category"),
                procedure_type=rfp_data.get("procedure_type"),
                cft_issue_date=rfp_data.get("cft_issue_date"),
                tender_deadline=rfp_data.get("tender_deadline"),
                opening_event_date=rfp_data.get("opening_event_date"),
                item_code=rfp_data.get("item_code"),
                lg_code=rfp_data.get("lg_code"),
                city_code=rfp_data.get("city_code"),
                certification=rfp_data.get("certification"),
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


@router.post(
    "/rfps/semantic-search",
    response_model=SemanticSearchResponse,
    summary="セマンティック検索",
    description="テキストクエリからセマンティック検索を実行し、類似RFPを取得します。",
)
async def semantic_search_rfps(
    search_data: SemanticSearchRequest,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> SemanticSearchResponse:
    """
    セマンティック検索

    テキストクエリから埋め込みベクトルを生成し、類似度の高いRFPを検索します。
    `include_match_factors=True`の場合は、会社プロフィールを取得して拡張マッチングスコアを計算します。

    Args:
        search_data: セマンティック検索リクエストデータ
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント

    Returns:
        SemanticSearchResponse: セマンティック検索結果

    Raises:
        HTTPException: 検索エラー
    """
    try:
        logger.info(
            f"セマンティック検索開始: user_id={user_id}, query_length={len(search_data.query)}, "
            f"threshold={search_data.similarity_threshold}, limit={search_data.result_limit}, "
            f"include_match_factors={search_data.include_match_factors}"
        )

        # EmbeddingServiceとVectorSearchServiceを初期化
        embedding_service = EmbeddingService()
        vector_search_service = VectorSearchService(supabase, embedding_service)

        # セマンティック検索を実行
        try:
            results = await vector_search_service.search_similar_rfps(
                query_text=search_data.query,
                similarity_threshold=search_data.similarity_threshold,
                result_limit=search_data.result_limit,
            )
        except Exception as e:
            logger.error(f"セマンティック検索エラー（キーワード検索へフォールバック）: {e}")
            # セマンティック検索失敗時はキーワード検索にフォールバック
            escaped_query = _escape_like_pattern(search_data.query)
            fallback_response = (
                supabase.table("rfps")
                .select("*")
                .or_(f"title.ilike.%{escaped_query}%,description.ilike.%{escaped_query}%")
                .limit(search_data.result_limit)
                .execute()
            )
            # similarity_scoreを付与（キーワード検索の場合は0.5）
            results = [
                {**rfp, "similarity_score": 0.5}
                for rfp in (fallback_response.data or [])
            ]

        # 拡張マッチングスコアの計算が必要な場合
        company = None
        company_embedding = None
        matching_engine = None

        if search_data.include_match_factors:
            # ユーザーの会社情報を取得
            company_response = (
                supabase.table("companies")
                .select("*")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )

            if company_response.data:
                company = company_response.data

                # 会社スキル埋め込みベクトルを取得
                embedding_response = (
                    supabase.table("company_skill_embeddings")
                    .select("embedding")
                    .eq("company_id", company["id"])
                    .order("updated_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if embedding_response.data and len(embedding_response.data) > 0:
                    company_embedding = embedding_response.data[0].get("embedding")

                # MatchingEngineを初期化
                matching_engine = MatchingEngine(supabase, embedding_service)

        # レスポンスアイテムを整形
        items = []
        for rfp_data in results:
            # 基本RFP情報
            item_dict = {
                "id": rfp_data["id"],
                "external_id": rfp_data["external_id"],
                "title": rfp_data["title"],
                "issuing_org": rfp_data["issuing_org"],
                "description": rfp_data["description"],
                "budget": rfp_data.get("budget"),
                "region": rfp_data["region"],
                "deadline": rfp_data["deadline"],
                "url": rfp_data.get("url"),
                "external_doc_urls": rfp_data.get("external_doc_urls", []),
                "has_embedding": rfp_data.get("embedding") is not None,
                "created_at": rfp_data["created_at"],
                "updated_at": rfp_data["updated_at"],
                "fetched_at": rfp_data["fetched_at"],
                "category": rfp_data.get("category"),
                "procedure_type": rfp_data.get("procedure_type"),
                "cft_issue_date": rfp_data.get("cft_issue_date"),
                "tender_deadline": rfp_data.get("tender_deadline"),
                "opening_event_date": rfp_data.get("opening_event_date"),
                "item_code": rfp_data.get("item_code"),
                "lg_code": rfp_data.get("lg_code"),
                "city_code": rfp_data.get("city_code"),
                "certification": rfp_data.get("certification"),
                "similarity_score": rfp_data.get("similarity_score", 0.0),
            }

            # 拡張マッチング情報を計算
            if company and matching_engine:
                try:
                    match_result = await matching_engine.calculate_enhanced_match_score(
                        company=company,
                        rfp=rfp_data,
                        company_embedding=company_embedding,
                    )
                    item_dict["match_score"] = match_result["score"]
                    item_dict["match_factors"] = match_result["factors"]
                    item_dict["summary_points"] = match_result["summary_points"]
                except Exception as e:
                    logger.warning(f"拡張マッチングスコア計算エラー（RFP ID={rfp_data['id']}）: {e}")
                    item_dict["match_score"] = None
                    item_dict["match_factors"] = None
                    item_dict["summary_points"] = []
            else:
                item_dict["match_score"] = None
                item_dict["match_factors"] = None
                item_dict["summary_points"] = []

            items.append(SemanticSearchResultItem(**item_dict))

        logger.info(
            f"セマンティック検索完了: user_id={user_id}, total={len(items)}, "
            f"query={search_data.query}"
        )

        return SemanticSearchResponse(
            total=len(items),
            items=items,
            query=search_data.query,
            similarity_threshold=search_data.similarity_threshold,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"セマンティック検索エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="セマンティック検索に失敗しました",
        )


@router.get(
    "/rfps/{rfp_id}/find-similar",
    response_model=SimilarRFPsResponse,
    summary="類似RFP検索",
    description="指定されたRFPと類似する案件を検索します。",
)
async def find_similar_rfps(
    rfp_id: str,
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    limit: int = Query(10, ge=1, le=50, description="返却する最大件数"),
) -> SimilarRFPsResponse:
    """
    類似RFP検索

    指定されたRFP IDと埋め込みベクトルが類似するRFPを検索します。

    Args:
        rfp_id: 基準となるRFP ID
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        limit: 返却する最大件数（デフォルト: 10、最大: 50）

    Returns:
        SimilarRFPsResponse: 類似RFP検索結果

    Raises:
        HTTPException: RFPが存在しない、検索エラー
    """
    try:
        logger.info(
            f"類似RFP検索開始: user_id={user_id}, rfp_id={rfp_id}, limit={limit}"
        )

        # EmbeddingServiceとVectorSearchServiceを初期化
        embedding_service = EmbeddingService()
        vector_search_service = VectorSearchService(supabase, embedding_service)

        # 類似RFP検索を実行
        try:
            results = await vector_search_service.find_similar_to_rfp(
                rfp_id=rfp_id,
                result_limit=limit,
            )
        except ValueError as e:
            # RFP IDが見つからない場合
            logger.info(f"類似RFP検索エラー: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

        # レスポンスアイテムを整形
        items = []
        for rfp_data in results:
            item_dict = {
                "id": rfp_data["id"],
                "external_id": rfp_data["external_id"],
                "title": rfp_data["title"],
                "issuing_org": rfp_data["issuing_org"],
                "description": rfp_data["description"],
                "budget": rfp_data.get("budget"),
                "region": rfp_data["region"],
                "deadline": rfp_data["deadline"],
                "url": rfp_data.get("url"),
                "external_doc_urls": rfp_data.get("external_doc_urls", []),
                "has_embedding": rfp_data.get("embedding") is not None,
                "created_at": rfp_data["created_at"],
                "updated_at": rfp_data["updated_at"],
                "fetched_at": rfp_data["fetched_at"],
                "category": rfp_data.get("category"),
                "procedure_type": rfp_data.get("procedure_type"),
                "cft_issue_date": rfp_data.get("cft_issue_date"),
                "tender_deadline": rfp_data.get("tender_deadline"),
                "opening_event_date": rfp_data.get("opening_event_date"),
                "item_code": rfp_data.get("item_code"),
                "lg_code": rfp_data.get("lg_code"),
                "city_code": rfp_data.get("city_code"),
                "certification": rfp_data.get("certification"),
                "similarity_score": rfp_data.get("similarity_score", 0.0),
                "match_score": None,
                "match_factors": None,
                "summary_points": [],
            }

            items.append(SemanticSearchResultItem(**item_dict))

        logger.info(
            f"類似RFP検索完了: user_id={user_id}, rfp_id={rfp_id}, total={len(items)}"
        )

        return SimilarRFPsResponse(
            rfp_id=rfp_id,
            similar_rfps=items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"類似RFP検索エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="類似RFP検索に失敗しました",
        )


@router.get(
    "/rfps/with-enhanced-matching",
    response_model=RFPWithMatchingListResponse,
    summary="拡張マッチングスコア付きRFP一覧を取得",
    description="セマンティック検索を含む拡張マッチングスコア付きでRFP一覧を取得します。",
)
async def get_rfps_with_enhanced_matching(
    user_id: CurrentUserId,
    supabase: Annotated[Client, Depends(get_supabase_client)],
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    min_score: int | None = Query(None, ge=0, le=100, description="最小マッチングスコア"),
) -> RFPWithMatchingListResponse:
    """
    拡張マッチングスコア付きRFP一覧取得

    ログインユーザーの会社情報に基づき、セマンティックマッチングを含む
    拡張スコアを計算してRFP一覧を返します。

    Args:
        user_id: 認証ユーザーID
        supabase: Supabaseクライアント
        page: ページ番号（デフォルト: 1）
        page_size: ページサイズ（デフォルト: 20、最大: 100）
        min_score: 最小マッチングスコア（オプション）

    Returns:
        RFPWithMatchingListResponse: 拡張マッチングスコア付きRFP一覧

    Raises:
        HTTPException: 会社情報が見つからない、取得エラー
    """
    try:
        logger.info(
            f"拡張マッチングスコア付きRFP一覧取得開始: user_id={user_id}, "
            f"page={page}, page_size={page_size}, min_score={min_score}"
        )

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

        # 会社スキル埋め込みベクトルを取得
        embedding_response = (
            supabase.table("company_skill_embeddings")
            .select("embedding")
            .eq("company_id", company["id"])
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )

        company_embedding = None
        if embedding_response.data and len(embedding_response.data) > 0:
            company_embedding = embedding_response.data[0].get("embedding")

        # EmbeddingServiceとMatchingEngineを初期化
        embedding_service = EmbeddingService()
        matching_engine = MatchingEngine(supabase, embedding_service)

        # オフセット計算
        offset = (page - 1) * page_size

        # RFP一覧を取得（埋め込みベクトルが存在するもののみ）
        query_builder = (
            supabase.table("rfps")
            .select("*", count="exact")
            .is_("embedding", "not.null")
            .order("fetched_at", desc=True)
            .range(offset, offset + page_size - 1)
        )

        rfp_response = query_builder.execute()

        # 各RFPの拡張マッチングスコアを計算
        items = []
        for rfp in rfp_response.data or []:
            try:
                # 拡張マッチングスコアを計算
                match_result = await matching_engine.calculate_enhanced_match_score(
                    company=company,
                    rfp=rfp,
                    company_embedding=company_embedding,
                )

                # min_scoreフィルタ
                if min_score is not None and match_result["score"] < min_score:
                    continue

                # RFPWithMatchingResponseを作成
                item = RFPWithMatchingResponse(
                    # RFP基本情報
                    id=rfp["id"],
                    external_id=rfp["external_id"],
                    title=rfp["title"],
                    issuing_org=rfp["issuing_org"],
                    description=rfp["description"],
                    budget=rfp.get("budget"),
                    region=rfp["region"],
                    deadline=rfp["deadline"],
                    url=rfp.get("url"),
                    external_doc_urls=rfp.get("external_doc_urls", []),
                    has_embedding=True,
                    created_at=rfp["created_at"],
                    updated_at=rfp["updated_at"],
                    fetched_at=rfp["fetched_at"],
                    category=rfp.get("category"),
                    procedure_type=rfp.get("procedure_type"),
                    cft_issue_date=rfp.get("cft_issue_date"),
                    tender_deadline=rfp.get("tender_deadline"),
                    opening_event_date=rfp.get("opening_event_date"),
                    item_code=rfp.get("item_code"),
                    lg_code=rfp.get("lg_code"),
                    city_code=rfp.get("city_code"),
                    certification=rfp.get("certification"),
                    # マッチング情報
                    match_score=match_result["score"],
                    must_requirements_ok=match_result["must_ok"],
                    budget_match_ok=match_result["budget_ok"],
                    region_match_ok=match_result["region_ok"],
                    match_factors=match_result["factors"],
                    summary_points=match_result["summary_points"],
                    match_calculated_at=datetime.now(),
                )

                items.append(item)

            except Exception as e:
                logger.warning(f"拡張マッチングスコア計算エラー（RFP ID={rfp['id']}）: {e}")
                continue

        # スコア降順でソート
        items.sort(key=lambda x: x.match_score if x.match_score is not None else 0, reverse=True)

        # ページサイズに合わせてトリミング
        items = items[:page_size]

        total = len(items)

        logger.info(
            f"拡張マッチングスコア付きRFP一覧を取得しました: user_id={user_id}, "
            f"total={total}, page={page}, page_size={page_size}, min_score={min_score}"
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
        logger.exception(f"拡張マッチングスコア付きRFP一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="拡張マッチングスコア付きRFP一覧の取得に失敗しました",
        )
