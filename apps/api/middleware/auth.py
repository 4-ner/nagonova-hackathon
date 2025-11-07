"""
Supabase JWT認証ミドルウェア

Authorization: Bearer <token> からトークンを取得し、Supabase JWTを検証します。
"""
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from database import get_supabase_client

logger = logging.getLogger(__name__)

# Bearer トークンスキーム
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> str:
    """
    認証トークンからユーザーIDを取得

    Args:
        credentials: Bearer トークン
        supabase: Supabaseクライアント

    Returns:
        str: ユーザーID (UUID)

    Raises:
        HTTPException: トークンが無効な場合
    """
    token = credentials.credentials

    try:
        # Supabase JWTトークンを検証
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            logger.warning("無効なトークンが提供されました")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効な認証トークンです",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = response.user.id
        logger.debug(f"認証成功: user_id={user_id}")

        return user_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"認証エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 依存性注入用の型エイリアス
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
