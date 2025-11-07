"""
Supabase Storageサービス

ファイルのアップロード/ダウンロード用の署名付きURL生成、ファイル削除を提供します。
"""
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Tuple

from supabase import Client

logger = logging.getLogger(__name__)

# Storage設定
BUCKET_NAME = "company-documents"
UPLOAD_URL_EXPIRES_IN = 300  # 5分（秒）
DOWNLOAD_URL_EXPIRES_IN = 3600  # 1時間（秒）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class StorageService:
    """Supabase Storage操作サービス"""

    # 許可されるMIME Type
    ALLOWED_MIME_TYPES = {
        'pdf': ['application/pdf'],
        'word': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
        ],
        'ppt': [
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint',
        ],
        'image': ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'],
        'text': ['text/plain'],
    }

    def __init__(self, supabase_client: Client):
        """
        初期化

        Args:
            supabase_client: Supabaseクライアント
        """
        self.supabase = supabase_client

    def sanitize_filename(self, filename: str) -> str:
        """
        ファイル名をサニタイズ

        Args:
            filename: 元のファイル名

        Returns:
            str: サニタイズされたファイル名

        Raises:
            ValueError: 無効なファイル名の場合
        """
        # パスからファイル名のみ抽出
        safe_name = Path(filename).name

        # 危険な文字を除去（英数字、スペース、ハイフン、アンダースコア、ドットのみ許可）
        safe_name = re.sub(r'[^\w\s.-]', '', safe_name)

        # 連続するドットを単一に（..攻撃防止）
        safe_name = re.sub(r'\.+', '.', safe_name)

        # 先頭・末尾の空白とドットを削除
        safe_name = safe_name.strip('. ')

        # ファイル名長を制限（拡張子を考慮）
        max_length = 255
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:max_length - len(ext)] + ext

        # 空文字列チェック
        if not safe_name or safe_name == '.':
            raise ValueError("無効なファイル名です")

        return safe_name

    def validate_file_type(self, kind: str, filename: str) -> None:
        """
        ファイルタイプの検証

        Args:
            kind: ドキュメント種別
            filename: ファイル名

        Raises:
            ValueError: 許可されていないファイルタイプの場合
        """
        # 拡張子からMIME Typeを推測
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)

        if not mime_type:
            raise ValueError(f"ファイルタイプを判定できません: {filename}")

        allowed_types = self.ALLOWED_MIME_TYPES.get(kind, [])

        if mime_type not in allowed_types:
            raise ValueError(
                f"許可されていないファイルタイプです: {mime_type} (種別: {kind})"
            )

    def generate_storage_path(self, user_id: str, filename: str) -> str:
        """
        Storageパスを生成

        パス形式: {user_id}/{document_id}/{filename}

        Args:
            user_id: ユーザーID
            filename: ファイル名

        Returns:
            str: Storageパス
        """
        # ドキュメントIDを生成
        document_id = str(uuid.uuid4())

        # ファイル名をサニタイズ
        safe_filename = self.sanitize_filename(filename)

        # パスを生成
        storage_path = f"{user_id}/{document_id}/{safe_filename}"

        logger.debug(f"Storage path generated: {storage_path}")

        return storage_path

    def create_signed_upload_url(
        self, user_id: str, filename: str, file_size: int, kind: str = None
    ) -> Tuple[str, str]:
        """
        署名付きアップロードURLを生成

        Args:
            user_id: ユーザーID
            filename: ファイル名
            file_size: ファイルサイズ（バイト）
            kind: ドキュメント種別（オプション）

        Returns:
            Tuple[str, str]: (署名付きURL, Storageパス)

        Raises:
            ValueError: ファイルサイズが制限を超える場合、またはファイルタイプが無効な場合
            Exception: URL生成エラー
        """
        # ファイルサイズチェック
        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"ファイルサイズが制限を超えています（最大: {MAX_FILE_SIZE / 1024 / 1024}MB）"
            )

        # ファイルタイプ検証（kindが提供されている場合）
        if kind and kind != 'url':
            self.validate_file_type(kind, filename)

        # Storageパス生成
        storage_path = self.generate_storage_path(user_id, filename)

        try:
            # 署名付きアップロードURL生成
            response = self.supabase.storage.from_(BUCKET_NAME).create_signed_upload_url(
                storage_path
            )

            if not response or "signedURL" not in response:
                raise Exception("署名付きURLの生成に失敗しました")

            signed_url = response["signedURL"]

            logger.info(
                f"Signed upload URL created: user_id={user_id}, path={storage_path}"
            )

            return signed_url, storage_path

        except Exception as e:
            logger.error(f"署名付きアップロードURL生成エラー: {e}")
            raise

    def create_signed_download_url(self, storage_path: str) -> str:
        """
        署名付きダウンロードURLを生成

        Args:
            storage_path: Storageパス

        Returns:
            str: 署名付きダウンロードURL

        Raises:
            Exception: URL生成エラー
        """
        try:
            # 署名付きダウンロードURL生成
            response = self.supabase.storage.from_(BUCKET_NAME).create_signed_url(
                storage_path, DOWNLOAD_URL_EXPIRES_IN
            )

            if not response or "signedURL" not in response:
                raise Exception("署名付きURLの生成に失敗しました")

            signed_url = response["signedURL"]

            logger.debug(f"Signed download URL created: path={storage_path}")

            return signed_url

        except Exception as e:
            logger.error(f"署名付きダウンロードURL生成エラー: {e}")
            raise

    def delete_file(self, storage_path: str) -> None:
        """
        ファイルを削除

        Args:
            storage_path: Storageパス

        Raises:
            Exception: ファイル削除エラー
        """
        try:
            # ファイル削除
            response = self.supabase.storage.from_(BUCKET_NAME).remove([storage_path])

            logger.info(f"File deleted: path={storage_path}")

        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            raise

    def get_public_url(self, storage_path: str) -> str:
        """
        公開URLを取得（バケットがpublicの場合のみ）

        現在のバケット設定ではprivateなため、この関数は使用されません。
        将来的にpublicバケットを使用する場合に備えて実装しています。

        Args:
            storage_path: Storageパス

        Returns:
            str: 公開URL
        """
        try:
            response = self.supabase.storage.from_(BUCKET_NAME).get_public_url(
                storage_path
            )

            return response

        except Exception as e:
            logger.error(f"公開URL取得エラー: {e}")
            raise
