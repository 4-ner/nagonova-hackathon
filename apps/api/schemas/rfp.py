"""
RFP関連のPydanticスキーマ

リクエスト/レスポンスのバリデーションとシリアライゼーションを定義します。
"""
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class RFPBase(BaseModel):
    """RFP基本スキーマ"""

    title: str = Field(..., min_length=1, description="RFPタイトル")
    issuing_org: str = Field(..., min_length=1, description="発行組織名")
    description: str = Field(..., description="RFP説明文")
    budget: int | None = Field(None, ge=0, description="予算（円）")
    region: str = Field(..., description="都道府県コード")
    deadline: date = Field(..., description="応募締切日")
    url: str | None = Field(None, description="RFP URL")
    external_doc_urls: list[str] = Field(default_factory=list, description="外部ドキュメントURL配列")


class RFPResponse(RFPBase):
    """RFPレスポンススキーマ"""

    id: str = Field(..., description="RFP ID (UUID)")
    external_id: str = Field(..., description="外部システムのID")
    has_embedding: bool = Field(..., description="埋め込みベクトルが存在するか")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    fetched_at: datetime = Field(..., description="取得日時")

    model_config = ConfigDict(from_attributes=True)


class RFPListResponse(BaseModel):
    """RFP一覧レスポンススキーマ"""

    total: int = Field(..., description="総件数")
    items: list[RFPResponse] = Field(..., description="RFPアイテム配列")
    page: int = Field(..., description="現在のページ番号")
    page_size: int = Field(..., description="ページサイズ")


class IngestRequest(BaseModel):
    """RFP取得リクエストスキーマ（管理者用）"""

    prefectures: list[str] = Field(default=["13", "27"], description="都道府県コード配列")
    count: int = Field(default=100, ge=1, le=1000, description="取得件数")
    query: str = Field(default="*", description="検索クエリ")
    ng_keywords: list[str] = Field(default=["保守", "運用"], description="NGキーワード配列")


class IngestResponse(BaseModel):
    """RFP取得レスポンススキーマ（管理者用）"""

    status: str = Field(..., description="処理ステータス")
    message: str = Field(..., description="処理メッセージ")
