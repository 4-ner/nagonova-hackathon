"""
ドキュメント関連のPydanticスキーマ

会社ドキュメントのリクエスト/レスポンスのバリデーションとシリアライゼーションを定義します。
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


# ドキュメント種別の型定義
DocumentKind = Literal["url", "pdf", "word", "ppt", "image", "text"]


class DocumentBase(BaseModel):
    """ドキュメント基本スキーマ"""

    title: str = Field(..., min_length=1, max_length=255, description="ドキュメントタイトル")
    description: str | None = Field(None, max_length=1000, description="ドキュメント説明")
    kind: DocumentKind = Field(..., description="ドキュメント種別")


class DocumentCreateUrl(DocumentBase):
    """URL型ドキュメント作成リクエスト"""

    url: HttpUrl = Field(..., description="ドキュメントURL")


class DocumentCreateFile(DocumentBase):
    """ファイル型ドキュメント作成リクエスト"""

    storage_path: str = Field(..., description="Supabase Storageパス")
    size_bytes: int = Field(..., ge=0, description="ファイルサイズ（バイト）")


class DocumentUpdate(BaseModel):
    """ドキュメント更新リクエスト"""

    title: str | None = Field(None, min_length=1, max_length=255, description="ドキュメントタイトル")
    description: str | None = Field(None, max_length=1000, description="ドキュメント説明")


class DocumentResponse(DocumentBase):
    """ドキュメントレスポンススキーマ"""

    id: str = Field(..., description="ドキュメントID (UUID)")
    company_id: str = Field(..., description="会社ID (UUID)")
    url: str | None = Field(None, description="ドキュメントURL（URL型の場合）")
    storage_path: str | None = Field(None, description="Storageパス（ファイル型の場合）")
    size_bytes: int | None = Field(None, description="ファイルサイズ（バイト）")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """ドキュメント一覧レスポンススキーマ"""

    total: int = Field(..., description="総件数")
    items: list[DocumentResponse] = Field(..., description="ドキュメントアイテム配列")
    page: int = Field(..., description="現在のページ番号")
    page_size: int = Field(..., description="ページサイズ")


class UploadUrlRequest(BaseModel):
    """アップロードURL生成リクエスト"""

    filename: str = Field(..., description="ファイル名")
    file_size: int = Field(..., ge=1, description="ファイルサイズ（バイト）")
    kind: DocumentKind | None = Field(None, description="ドキュメント種別（ファイルタイプ検証用）")


class UploadUrlResponse(BaseModel):
    """アップロードURL生成レスポンス"""

    upload_url: str = Field(..., description="署名付きアップロードURL")
    storage_path: str = Field(..., description="Storageパス")
    expires_in: int = Field(..., description="有効期限（秒）")


class DownloadUrlResponse(BaseModel):
    """ダウンロードURL生成レスポンス"""

    download_url: str = Field(..., description="署名付きダウンロードURL")
    expires_in: int = Field(..., description="有効期限（秒）")
