"""
ブックマーク関連のPydanticスキーマ

リクエスト/レスポンスのバリデーションとシリアライゼーションを定義します。
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BookmarkCreate(BaseModel):
    """ブックマーク作成リクエストスキーマ"""

    rfp_id: str = Field(..., description="RFP ID (UUID)")


class BookmarkResponse(BaseModel):
    """ブックマークレスポンススキーマ"""

    id: str = Field(..., description="ブックマーク ID (UUID)")
    user_id: str = Field(..., description="ユーザー ID (UUID)")
    rfp_id: str = Field(..., description="RFP ID (UUID)")
    created_at: datetime = Field(..., description="作成日時")

    model_config = ConfigDict(from_attributes=True)


class BookmarkWithRFPResponse(BookmarkResponse):
    """RFP情報付きブックマークレスポンススキーマ"""

    rfp: dict = Field(..., description="RFP情報")


class BookmarkListResponse(BaseModel):
    """ブックマーク一覧レスポンススキーマ"""

    total: int = Field(..., description="総件数")
    items: list[BookmarkWithRFPResponse] = Field(..., description="ブックマークアイテム配列")
    page: int = Field(..., description="現在のページ番号")
    page_size: int = Field(..., description="ページサイズ")
