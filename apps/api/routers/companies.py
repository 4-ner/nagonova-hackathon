"""
会社プロフィール管理APIルーター

会社情報のCRUD操作を提供します。
"""
import logging
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from database import get_supabase_client
from middleware.auth import CurrentUserId, CurrentAuthToken
from schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/companies",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="会社プロフィールを作成",
    description="認証されたユーザーの会社プロフィールを作成します。1ユーザーにつき1会社のみ作成可能です。",
)
async def create_company(
    company_data: CompanyCreate,
    user_id: CurrentUserId,
    auth_token: CurrentAuthToken,
) -> CompanyResponse:
    """
    会社プロフィール作成

    Args:
        company_data: 会社作成データ
        user_id: 認証ユーザーID
        auth_token: 認証トークン

    Returns:
        CompanyResponse: 作成された会社情報

    Raises:
        HTTPException: 既に会社が存在する場合や作成エラー
    """
    try:
        # トークン付きSupabaseクライアントを取得
        supabase = await get_supabase_client(token=auth_token)

        # 既存の会社があるかチェック
        existing = supabase.table("companies").select("id").eq("user_id", user_id).execute()

        if existing.data:
            logger.warning(f"ユーザー {user_id} は既に会社を登録しています")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="既に会社プロフィールが存在します",
            )

        # 会社データを作成
        insert_data = {
            "user_id": user_id,
            **company_data.model_dump(),
        }

        response = supabase.table("companies").insert(insert_data).execute()

        if not response.data:
            logger.error(f"会社作成に失敗しました: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="会社プロフィールの作成に失敗しました",
            )

        created_company = response.data[0]
        logger.info(f"会社を作成しました: id={created_company['id']}, user_id={user_id}")

        return CompanyResponse(**created_company)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"会社作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会社プロフィールの作成に失敗しました",
        )


@router.get(
    "/companies/me",
    response_model=CompanyResponse,
    summary="自分の会社情報を取得",
    description="認証されたユーザーの会社プロフィールを取得します。",
)
async def get_my_company(
    user_id: CurrentUserId,
    auth_token: CurrentAuthToken,
) -> CompanyResponse:
    """
    自分の会社情報取得

    Args:
        user_id: 認証ユーザーID
        auth_token: 認証トークン

    Returns:
        CompanyResponse: 会社情報

    Raises:
        HTTPException: 会社が存在しない場合や取得エラー
    """
    try:
        # トークン付きSupabaseクライアントを取得
        supabase = await get_supabase_client(token=auth_token)
        response = supabase.table("companies").select("*").eq("user_id", user_id).execute()

        if not response.data:
            logger.info(f"会社が見つかりません: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会社プロフィールが見つかりません",
            )

        company = response.data[0]
        logger.debug(f"会社情報を取得しました: id={company['id']}, user_id={user_id}")

        return CompanyResponse(**company)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"会社情報取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会社情報の取得に失敗しました",
        )


@router.put(
    "/companies/me",
    response_model=CompanyResponse,
    summary="会社情報を更新",
    description="認証されたユーザーの会社プロフィールを更新します。部分更新に対応しています。",
)
async def update_my_company(
    company_data: CompanyUpdate,
    user_id: CurrentUserId,
    auth_token: CurrentAuthToken,
) -> CompanyResponse:
    """
    会社情報更新

    Args:
        company_data: 会社更新データ
        user_id: 認証ユーザーID
        auth_token: 認証トークン

    Returns:
        CompanyResponse: 更新された会社情報

    Raises:
        HTTPException: 会社が存在しない場合や更新エラー
    """
    try:
        # トークン付きSupabaseクライアントを取得
        supabase = await get_supabase_client(token=auth_token)

        # 会社が存在するかチェック
        existing = supabase.table("companies").select("id").eq("user_id", user_id).execute()

        if not existing.data:
            logger.info(f"会社が見つかりません: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会社プロフィールが見つかりません",
            )

        # 更新データを準備（Noneでないフィールドのみ）
        update_data = company_data.model_dump(exclude_unset=True)

        if not update_data:
            logger.warning(f"更新データがありません: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新するデータがありません",
            )

        # updated_atを設定
        update_data["updated_at"] = datetime.now().isoformat()

        # 更新実行
        response = (
            supabase.table("companies")
            .update(update_data)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            logger.error(f"会社更新に失敗しました: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="会社プロフィールの更新に失敗しました",
            )

        updated_company = response.data[0]
        logger.info(f"会社を更新しました: id={updated_company['id']}, user_id={user_id}")

        return CompanyResponse(**updated_company)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"会社更新エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会社プロフィールの更新に失敗しました",
        )


@router.delete(
    "/companies/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="会社情報を削除",
    description="認証されたユーザーの会社プロフィールを削除します。",
)
async def delete_my_company(
    user_id: CurrentUserId,
    auth_token: CurrentAuthToken,
) -> None:
    """
    会社情報削除

    Args:
        user_id: 認証ユーザーID
        auth_token: 認証トークン

    Raises:
        HTTPException: 会社が存在しない場合や削除エラー
    """
    try:
        # トークン付きSupabaseクライアントを取得
        supabase = await get_supabase_client(token=auth_token)

        # 会社が存在するかチェック
        existing = supabase.table("companies").select("id").eq("user_id", user_id).execute()

        if not existing.data:
            logger.info(f"会社が見つかりません: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会社プロフィールが見つかりません",
            )

        company_id = existing.data[0]["id"]

        # 削除実行
        supabase.table("companies").delete().eq("user_id", user_id).execute()

        logger.info(f"会社を削除しました: id={company_id}, user_id={user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"会社削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会社プロフィールの削除に失敗しました",
        )
