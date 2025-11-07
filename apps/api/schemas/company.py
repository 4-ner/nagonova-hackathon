"""
会社プロフィール関連のPydanticスキーマ

リクエスト/レスポンスのバリデーションとシリアライゼーションを定義します。
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CompanyBase(BaseModel):
    """会社情報の基本スキーマ"""

    name: str = Field(..., min_length=1, max_length=255, description="会社名")
    description: str | None = Field(None, description="会社の説明")
    regions: list[str] = Field(default_factory=list, description="対応可能な都道府県コード配列")
    budget_min: int | None = Field(None, ge=0, description="最小予算（円）")
    budget_max: int | None = Field(None, ge=0, description="最大予算（円）")
    skills: list[str] = Field(default_factory=list, description="保有スキル配列")
    ng_keywords: list[str] = Field(default_factory=list, description="NGキーワード配列")


class CompanyCreate(CompanyBase):
    """会社作成用スキーマ"""

    pass


class CompanyUpdate(BaseModel):
    """会社更新用スキーマ（すべてのフィールドがOptional）"""

    name: str | None = Field(None, min_length=1, max_length=255, description="会社名")
    description: str | None = Field(None, description="会社の説明")
    regions: list[str] | None = Field(None, description="対応可能な都道府県コード配列")
    budget_min: int | None = Field(None, ge=0, description="最小予算（円）")
    budget_max: int | None = Field(None, ge=0, description="最大予算（円）")
    skills: list[str] | None = Field(None, description="保有スキル配列")
    ng_keywords: list[str] | None = Field(None, description="NGキーワード配列")


class CompanyResponse(CompanyBase):
    """会社情報レスポンス用スキーマ"""

    id: str = Field(..., description="会社ID (UUID)")
    user_id: str = Field(..., description="ユーザーID (UUID)")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    model_config = ConfigDict(from_attributes=True)
