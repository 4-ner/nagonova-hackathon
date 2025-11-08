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

    # KKJ API新規フィールド（2025-11-08追加）
    category: str | None = Field(None, description="案件カテゴリ")
    procedure_type: str | None = Field(None, description="入札手続きの種類")
    cft_issue_date: datetime | None = Field(None, description="仕様書発行日")
    tender_deadline: datetime | None = Field(None, description="入札締切日時")
    opening_event_date: datetime | None = Field(None, description="開札日時")
    item_code: str | None = Field(None, description="品目分類コード")
    lg_code: str | None = Field(None, description="地方自治体コード")
    city_code: str | None = Field(None, description="市区町村コード")
    certification: str | None = Field(None, description="参加資格情報")


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


class RFPWithMatchingResponse(RFPResponse):
    """マッチングスコア付きRFPレスポンススキーマ"""

    match_score: int | None = Field(None, ge=0, le=100, description="マッチングスコア（0-100）")
    must_requirements_ok: bool | None = Field(None, description="必須要件を満たすか")
    budget_match_ok: bool | None = Field(None, description="予算が適合するか")
    region_match_ok: bool | None = Field(None, description="地域が適合するか")
    match_factors: dict | None = Field(None, description="マッチング要因の内訳")
    summary_points: list[str] = Field(default_factory=list, description="マッチング理由のサマリー")
    match_calculated_at: datetime | None = Field(None, description="マッチングスコア計算日時")


class RFPWithMatchingListResponse(BaseModel):
    """マッチングスコア付きRFP一覧レスポンススキーマ"""

    total: int = Field(..., description="総件数")
    items: list[RFPWithMatchingResponse] = Field(..., description="RFPアイテム配列")
    page: int = Field(..., description="現在のページ番号")
    page_size: int = Field(..., description="ページサイズ")


class IngestResponse(BaseModel):
    """RFP取得レスポンススキーマ（管理者用）"""

    status: str = Field(..., description="処理ステータス")
    message: str = Field(..., description="処理メッセージ")
