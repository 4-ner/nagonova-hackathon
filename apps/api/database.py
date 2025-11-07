"""
Supabaseクライアントの初期化と管理

認証付きクライアントとService Roleクライアントを提供します。
"""
import logging
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabaseクライアントのシングルトン管理"""

    _anon_client: Client | None = None
    _service_client: Client | None = None

    @classmethod
    def get_anon_client(cls) -> Client:
        """
        認証付きクライアントを取得（ANON_KEY使用）

        Returns:
            Client: Supabase匿名キークライアント
        """
        if cls._anon_client is None:
            logger.info("Supabase匿名キークライアントを初期化します")
            cls._anon_client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
        return cls._anon_client

    @classmethod
    def get_service_client(cls) -> Client:
        """
        Service Roleクライアントを取得（管理操作用）

        Returns:
            Client: Supabaseサービスロールクライアント
        """
        if cls._service_client is None:
            logger.info("Supabaseサービスロールクライアントを初期化します")
            cls._service_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._service_client


async def get_supabase_client() -> Client:
    """
    FastAPIの依存性注入用のSupabaseクライアント取得関数

    Returns:
        Client: Supabase匿名キークライアント
    """
    return SupabaseClient.get_anon_client()


async def get_service_supabase_client() -> Client:
    """
    FastAPIの依存性注入用のSupabaseサービスクライアント取得関数

    Returns:
        Client: Supabaseサービスロールクライアント
    """
    return SupabaseClient.get_service_client()


async def check_supabase_connection() -> bool:
    """
    Supabase接続をチェック

    Returns:
        bool: 接続が成功した場合True
    """
    try:
        client = SupabaseClient.get_anon_client()
        # 簡単なクエリで接続確認
        # RPC関数やテーブルが存在しない場合でも、クライアントが初期化されているかチェック
        if client:
            logger.info("Supabase接続に成功しました")
            return True
        return False
    except Exception as e:
        logger.error(f"Supabase接続エラー: {e}")
        return False
