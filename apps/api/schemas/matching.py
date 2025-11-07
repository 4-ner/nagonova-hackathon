"""
マッチング結果のスキーマ定義

会社とRFP案件のマッチングスコアと詳細情報を表現します。
"""
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class MatchingFactors(BaseModel):
    """マッチングスコアの要因内訳"""

    skill_match: float = Field(..., ge=0.0, le=1.0, description="スキルマッチ度（0.0-1.0）")
    region_coefficient: float = Field(..., ge=0.0, le=1.0, description="地域係数（0.8 or 1.0）")
    budget_boost: float = Field(..., ge=0.0, le=0.1, description="予算マッチ度加算（0-10%）")
    deadline_boost: float = Field(..., ge=0.0, le=0.05, description="納期加算（0-5%）")


class MatchSnapshotBase(BaseModel):
    """マッチングスナップショットの基本情報"""

    company_id: str = Field(..., description="会社ID")
    rfp_id: str = Field(..., description="RFP案件ID")
    match_score: int = Field(..., ge=0, le=100, description="マッチングスコア（0-100）")
    must_requirements_ok: bool = Field(..., description="必須要件を満たすか")
    budget_match_ok: bool = Field(..., description="予算が適合するか")
    region_match_ok: bool = Field(..., description="地域が適合するか")
    match_factors: MatchingFactors = Field(..., description="マッチング要因の内訳")
    summary_points: list[str] = Field(default_factory=list, description="マッチング理由のサマリー")


class MatchSnapshotResponse(MatchSnapshotBase):
    """マッチングスナップショットのレスポンス（IDとタイムスタンプ付き）"""

    id: str = Field(..., description="マッチングスナップショットID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    model_config = {"from_attributes": True}


class RFPWithMatchingResponse(BaseModel):
    """マッチングスコア付きRFP情報"""

    # RFP基本情報
    id: str = Field(..., description="RFP案件ID")
    external_id: str = Field(..., description="外部ID（KKJ APIのID）")
    title: str = Field(..., description="案件タイトル")
    description: str = Field(..., description="案件詳細")
    organization: str = Field(..., description="発注組織名")
    prefecture: str = Field(..., description="都道府県")
    budget: int | None = Field(None, description="予算（円）")
    deadline: date | None = Field(None, description="応募締切日")
    source_url: str | None = Field(None, description="元の案件URL")

    # マッチング情報
    match_score: int = Field(..., ge=0, le=100, description="マッチングスコア（0-100）")
    must_requirements_ok: bool = Field(..., description="必須要件を満たすか")
    budget_match_ok: bool = Field(..., description="予算が適合するか")
    region_match_ok: bool = Field(..., description="地域が適合するか")
    match_factors: MatchingFactors = Field(..., description="マッチング要因の内訳")
    summary_points: list[str] = Field(default_factory=list, description="マッチング理由のサマリー")
    match_calculated_at: datetime = Field(..., description="マッチングスコア計算日時")

    model_config = {"from_attributes": True}


class MatchingListResponse(BaseModel):
    """マッチング結果一覧のレスポンス"""

    matches: list[RFPWithMatchingResponse] = Field(default_factory=list, description="マッチング結果リスト")
    total: int = Field(..., ge=0, description="総マッチング件数")
    page: int = Field(..., ge=1, description="現在のページ番号")
    page_size: int = Field(..., ge=1, description="ページサイズ")
