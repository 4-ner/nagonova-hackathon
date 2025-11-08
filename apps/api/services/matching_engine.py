"""
マッチングエンジンサービス

会社プロフィールとRFPをマッチングし、スコアを計算します。
"""

import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from supabase import Client

from services.embedding import EmbeddingService

# ロガー設定
logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    マッチングエンジンクラス

    会社プロフィールとRFPのマッチングスコアを計算し、
    マッチング結果のサマリーを生成します。
    """

    def __init__(
        self, supabase_client: Client, embedding_service: EmbeddingService
    ) -> None:
        """
        MatchingEngineを初期化します。

        Args:
            supabase_client: Supabaseクライアント
            embedding_service: 埋め込みサービス

        Raises:
            FileNotFoundError: スキルエイリアス辞書ファイルが見つからない場合
            json.JSONDecodeError: スキルエイリアス辞書のJSON解析に失敗した場合
        """
        self.supabase = supabase_client
        self.embedding_service = embedding_service

        # スキルエイリアス辞書を読み込み
        skill_aliases_path = (
            Path(__file__).parent.parent / "data" / "skill_aliases.json"
        )

        if not skill_aliases_path.exists():
            error_msg = f"スキルエイリアス辞書が見つかりません: {skill_aliases_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(skill_aliases_path, "r", encoding="utf-8") as f:
                self.skill_aliases: dict[str, list[str]] = json.load(f)

            logger.info(
                f"スキルエイリアス辞書読み込み完了: {len(self.skill_aliases)}件"
            )

        except json.JSONDecodeError as e:
            error_msg = f"スキルエイリアス辞書の解析に失敗: {e}"
            logger.error(error_msg)
            raise

        logger.info("MatchingEngine初期化完了")

    def calculate_matching_score(self, company: dict[str, Any], rfp: dict[str, Any]) -> dict[str, Any]:
        """
        会社プロフィールとRFPのマッチングスコアを計算します。

        Args:
            company: 会社プロフィール辞書
                - id: UUID
                - skills: list[str] - 保有スキル配列
                - regions: list[str] - 対応可能な都道府県コード配列
                - budget_min: int | None - 予算下限
                - budget_max: int | None - 予算上限
                - ng_keywords: list[str] - NGキーワード配列
            rfp: RFP辞書
                - id: UUID
                - title: str - タイトル
                - description: str - 説明
                - budget: int | None - 予算
                - region: str - 都道府県コード
                - deadline: date | str - 締切日

        Returns:
            マッチング結果辞書:
                - score: int - 最終スコア (0~100)
                - must_ok: bool - 必須要件を満たしているか
                - budget_ok: bool - 予算条件を満たしているか
                - region_ok: bool - 地域条件を満たしているか
                - factors: dict - スコア計算要素
                    - skill: float - スキルマッチ度 (0.0~1.0)
                    - must: bool - 必須要件判定
                    - budget: float - 予算ブースト (0.0~0.1)
                    - deadline: float - 締切ブースト (0.0~0.05)
                    - region: float - 地域係数 (0.8 or 1.0)
                - summary_points: list[str] - マッチング結果サマリー（3点程度）

        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        # 必須フィールドチェック
        required_company_fields = ["id", "skills", "regions"]
        required_rfp_fields = ["id", "title", "description", "region", "deadline"]

        for field in required_company_fields:
            if field not in company:
                raise ValueError(f"会社プロフィールに必須フィールドがありません: {field}")

        for field in required_rfp_fields:
            if field not in rfp:
                raise ValueError(f"RFPに必須フィールドがありません: {field}")

        logger.info(
            f"マッチング計算開始: company_id={company['id']}, rfp_id={rfp['id']}"
        )

        # RFP全文を作成（タイトル + 説明）
        rfp_text = f"{rfp['title']}\n{rfp['description']}"

        # NGキーワードチェック
        ng_keywords = company.get("ng_keywords", [])
        if ng_keywords:
            for ng_keyword in ng_keywords:
                if ng_keyword and ng_keyword.lower() in rfp_text.lower():
                    logger.info(
                        f"NGキーワードが検出されました: {ng_keyword} - スコア0を返却"
                    )
                    return {
                        "score": 0,
                        "must_ok": False,
                        "budget_ok": False,
                        "region_ok": False,
                        "factors": {
                            "skill": 0.0,
                            "must": False,
                            "budget": 0.0,
                            "deadline": 0.0,
                            "region": 0.0,
                        },
                        "summary_points": [f"NGキーワード「{ng_keyword}」が含まれています"],
                    }

        # 各要素を計算
        skill_match = self._calculate_skill_match(company["skills"], rfp_text)
        must_ok = self._check_must_requirements(rfp_text)
        region_coefficient = self._calculate_region_coefficient(
            company["regions"], rfp["region"]
        )
        budget_boost = self._calculate_budget_boost(
            company.get("budget_min"),
            company.get("budget_max"),
            rfp.get("budget"),
        )

        # 締切日を date オブジェクトに変換
        if isinstance(rfp["deadline"], str):
            deadline_date = datetime.fromisoformat(rfp["deadline"]).date()
        else:
            deadline_date = rfp["deadline"]

        deadline_boost = self._calculate_deadline_boost(deadline_date)

        # ベーススコア計算
        base_score = skill_match * 100

        # 必須要件チェック
        if not must_ok:
            base_score *= 0.5  # 必須要件未達は50%減点

        # 地域係数適用
        base_score *= region_coefficient

        # 予算ブースト適用
        base_score *= 1.0 + budget_boost

        # 締切ブースト適用
        base_score *= 1.0 + deadline_boost

        # 最終スコア（0~100に丸める）
        final_score = min(100, max(0, int(base_score)))

        # 予算条件判定
        budget_ok = True
        if rfp.get("budget") and company.get("budget_min") and company.get("budget_max"):
            budget_ok = (
                company["budget_min"] <= rfp["budget"] <= company["budget_max"]
            )

        # 地域条件判定
        region_ok = rfp["region"] in company["regions"]

        # 要素を辞書にまとめる
        factors = {
            "skill": round(skill_match, 3),
            "must": must_ok,
            "budget": round(budget_boost, 3),
            "deadline": round(deadline_boost, 3),
            "region": round(region_coefficient, 3),
        }

        # サマリーポイント生成
        summary_points = self._generate_summary_points(company, rfp, factors)

        result = {
            "score": final_score,
            "must_ok": must_ok,
            "budget_ok": budget_ok,
            "region_ok": region_ok,
            "factors": factors,
            "summary_points": summary_points,
        }

        logger.info(
            f"マッチング計算完了: score={final_score}, "
            f"skill={skill_match:.2f}, must_ok={must_ok}, "
            f"budget_ok={budget_ok}, region_ok={region_ok}"
        )

        return result

    def _calculate_skill_match(
        self, company_skills: list[str], rfp_text: str
    ) -> float:
        """
        スキル一致度を計算します。

        会社の保有スキルとRFP本文中のスキル出現回数を比較し、
        一致度を0.0~1.0のスコアで返します。

        Args:
            company_skills: 会社の保有スキル配列
            rfp_text: RFP全文（タイトル + 説明）

        Returns:
            スキルマッチ度 (0.0~1.0)
        """
        if not company_skills:
            logger.warning("会社のスキルが空です")
            return 0.0

        rfp_text_lower = rfp_text.lower()
        matched_skills = 0
        total_skills = len(company_skills)

        for skill in company_skills:
            if not skill:
                continue

            # スキルエイリアス展開
            expanded_skills = self._expand_skill_with_aliases(skill)

            # いずれかのエイリアスがRFP本文に含まれているかチェック
            for expanded_skill in expanded_skills:
                if expanded_skill.lower() in rfp_text_lower:
                    matched_skills += 1
                    logger.debug(f"スキルマッチ: {skill} (alias: {expanded_skill})")
                    break  # 1つマッチしたらこのスキルはカウント済み

        match_ratio = matched_skills / total_skills if total_skills > 0 else 0.0

        logger.debug(
            f"スキルマッチ計算: matched={matched_skills}, total={total_skills}, "
            f"ratio={match_ratio:.2f}"
        )

        return match_ratio

    def _check_must_requirements(self, rfp_text: str) -> bool:
        """
        必須要件を判定します。

        RFP本文中に「必須」「必ず」「条件」等のキーワードが含まれているかチェックします。

        Args:
            rfp_text: RFP全文（タイトル + 説明）

        Returns:
            必須要件キーワードが含まれている場合 True、含まれていない場合 False
        """
        must_keywords = [
            "必須",
            "必ず",
            "条件",
            "要件",
            "必要",
            "不可欠",
            "義務",
            "前提",
        ]

        rfp_text_lower = rfp_text.lower()

        for keyword in must_keywords:
            if keyword in rfp_text_lower:
                logger.debug(f"必須要件キーワード検出: {keyword}")
                return True

        logger.debug("必須要件キーワードなし")
        return True  # 必須要件が明記されていない場合は True（条件を満たしているとみなす）

    def _calculate_region_coefficient(
        self, company_regions: list[str], rfp_region: str
    ) -> float:
        """
        地域係数を計算します。

        会社の対応可能地域とRFPの地域が一致するかチェックし、係数を返します。

        Args:
            company_regions: 会社の対応可能な都道府県コード配列
            rfp_region: RFPの都道府県コード

        Returns:
            地域係数 (一致: 1.0, 不一致: 0.8)
        """
        if rfp_region in company_regions:
            logger.debug(f"地域一致: {rfp_region}")
            return 1.0

        logger.debug(f"地域不一致: rfp={rfp_region}, company={company_regions}")
        return 0.8

    def _calculate_budget_boost(
        self,
        company_budget_min: int | None,
        company_budget_max: int | None,
        rfp_budget: int | None,
    ) -> float:
        """
        予算ブーストを計算します。

        会社の予算範囲とRFPの予算を比較し、ブースト値を返します。

        Args:
            company_budget_min: 会社の予算下限（円）
            company_budget_max: 会社の予算上限（円）
            rfp_budget: RFPの予算（円）

        Returns:
            予算ブースト (範囲内: +0.1, 近い: +0.05, それ以外: 0.0)
        """
        # 予算情報が不足している場合はブーストなし
        if (
            rfp_budget is None
            or company_budget_min is None
            or company_budget_max is None
        ):
            logger.debug("予算情報不足: ブーストなし")
            return 0.0

        # 予算範囲内
        if company_budget_min <= rfp_budget <= company_budget_max:
            logger.debug(
                f"予算範囲内: rfp={rfp_budget}, "
                f"company=[{company_budget_min}, {company_budget_max}] -> +10%"
            )
            return 0.1

        # 予算範囲外だが近い（±20%以内）
        tolerance = 0.2
        if (
            company_budget_min * (1 - tolerance)
            <= rfp_budget
            <= company_budget_max * (1 + tolerance)
        ):
            logger.debug(
                f"予算範囲近傍: rfp={rfp_budget}, "
                f"company=[{company_budget_min}, {company_budget_max}] -> +5%"
            )
            return 0.05

        logger.debug(
            f"予算範囲外: rfp={rfp_budget}, "
            f"company=[{company_budget_min}, {company_budget_max}] -> 0%"
        )
        return 0.0

    def _calculate_deadline_boost(self, rfp_deadline: date) -> float:
        """
        締切ブーストを計算します。

        RFPの締切までの日数に応じてブースト値を返します。

        Args:
            rfp_deadline: RFPの締切日

        Returns:
            締切ブースト (1週間以内: +0.05, 1ヶ月以内: +0.03, それ以降: 0.0)
        """
        today = date.today()
        days_until_deadline = (rfp_deadline - today).days

        if days_until_deadline < 0:
            logger.debug(f"締切超過: {days_until_deadline}日前 -> 0%")
            return 0.0

        if days_until_deadline <= 7:
            logger.debug(f"締切1週間以内: {days_until_deadline}日 -> +5%")
            return 0.05

        if days_until_deadline <= 30:
            logger.debug(f"締切1ヶ月以内: {days_until_deadline}日 -> +3%")
            return 0.03

        logger.debug(f"締切1ヶ月以降: {days_until_deadline}日 -> 0%")
        return 0.0

    def _generate_summary_points(
        self, company: dict[str, Any], rfp: dict[str, Any], factors: dict[str, Any]
    ) -> list[str]:
        """
        マッチング結果のサマリーポイントを生成します。

        Args:
            company: 会社プロフィール辞書
            rfp: RFP辞書
            factors: スコア計算要素辞書

        Returns:
            サマリーポイントのリスト（最大3点）
        """
        summary_points: list[str] = []

        # スキルマッチ度
        skill_match_percent = int(factors["skill"] * 100)
        if skill_match_percent >= 80:
            summary_points.append(f"スキルマッチ度 {skill_match_percent}% (高)")
        elif skill_match_percent >= 50:
            summary_points.append(f"スキルマッチ度 {skill_match_percent}% (中)")
        else:
            summary_points.append(f"スキルマッチ度 {skill_match_percent}% (低)")

        # 予算条件
        if rfp.get("budget") and company.get("budget_min") and company.get("budget_max"):
            if company["budget_min"] <= rfp["budget"] <= company["budget_max"]:
                summary_points.append("予算範囲内")
            else:
                summary_points.append("予算範囲外")

        # 地域条件
        if rfp["region"] in company["regions"]:
            summary_points.append("対応可能地域")
        else:
            summary_points.append("対応不可地域")

        # 締切情報
        if isinstance(rfp["deadline"], str):
            deadline_date = datetime.fromisoformat(rfp["deadline"]).date()
        else:
            deadline_date = rfp["deadline"]

        days_until_deadline = (deadline_date - date.today()).days

        if days_until_deadline < 0:
            summary_points.append("締切超過")
        elif days_until_deadline <= 7:
            summary_points.append(f"締切まで{days_until_deadline}日（緊急）")
        elif days_until_deadline <= 30:
            summary_points.append(f"締切まで{days_until_deadline}日")

        # 最大3点に制限
        return summary_points[:3]

    def _expand_skill_with_aliases(self, skill: str) -> list[str]:
        """
        スキルエイリアスを展開します。

        スキルエイリアス辞書を使用して、スキル名とそのエイリアスをリストで返します。

        Args:
            skill: スキル名

        Returns:
            スキル名とエイリアスのリスト
        """
        # スキル自身を含める
        expanded = [skill]

        # 辞書のキーとして一致するか確認
        if skill in self.skill_aliases:
            expanded.extend(self.skill_aliases[skill])
            logger.debug(f"エイリアス展開(キー): {skill} -> {expanded}")
            return expanded

        # 辞書の値として一致するか確認
        for key, aliases in self.skill_aliases.items():
            if skill in aliases:
                expanded.append(key)
                expanded.extend([a for a in aliases if a != skill])
                logger.debug(f"エイリアス展開(値): {skill} -> {expanded}")
                return expanded

        # 大文字小文字を無視して検索
        skill_lower = skill.lower()
        for key, aliases in self.skill_aliases.items():
            if key.lower() == skill_lower:
                expanded.extend(self.skill_aliases[key])
                logger.debug(f"エイリアス展開(大小無視): {skill} -> {expanded}")
                return expanded

            if any(alias.lower() == skill_lower for alias in aliases):
                expanded.append(key)
                expanded.extend([a for a in aliases if a.lower() != skill_lower])
                logger.debug(f"エイリアス展開(大小無視): {skill} -> {expanded}")
                return expanded

        # エイリアスが見つからない場合はスキル自身のみ
        logger.debug(f"エイリアスなし: {skill}")
        return expanded

    async def calculate_enhanced_match_score(
        self,
        company: dict[str, Any],
        rfp: dict[str, Any],
        company_embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        セマンティックマッチングを含む拡張スコア計算を行います。

        スコア内訳:
        - semantic_skill_match (40%): 会社スキルとRFP説明の意味的類似度
        - keyword_skill_match (30%): キーワードベースのスキルマッチ
        - budget_match (10%): 予算適合度
        - region_match (10%): 地域適合度
        - deadline_bonus (10%): 納期ボーナス

        Args:
            company: 会社プロフィール辞書
                - id: UUID
                - skills: list[str] - 保有スキル配列
                - regions: list[str] - 対応可能な都道府県コード配列
                - budget_min: int | None - 予算下限
                - budget_max: int | None - 予算上限
                - ng_keywords: list[str] - NGキーワード配列
            rfp: RFP辞書
                - id: UUID
                - title: str - タイトル
                - description: str - 説明
                - embedding: list[float] | None - RFP埋め込みベクトル
                - budget: int | None - 予算
                - region: str - 都道府県コード
                - deadline: date | str - 締切日
            company_embedding: 会社スキル埋め込みベクトル（オプション）

        Returns:
            マッチング結果辞書:
                - score: int - 最終スコア (0~100)
                - must_ok: bool - 必須要件を満たしているか
                - budget_ok: bool - 予算条件を満たしているか
                - region_ok: bool - 地域条件を満たしているか
                - factors: dict - スコア計算要素
                    - semantic_skill_match: float - セマンティックスキルマッチ度 (0.0~1.0)
                    - keyword_skill_match: float - キーワードスキルマッチ度 (0.0~1.0)
                    - must: bool - 必須要件判定
                    - budget: float - 予算ブースト (0.0~0.1)
                    - deadline: float - 締切ブースト (0.0~0.05)
                    - region: float - 地域係数 (0.8 or 1.0)
                - summary_points: list[str] - マッチング結果サマリー

        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        # 必須フィールドチェック（既存のcalculate_matching_scoreと同じ）
        required_company_fields = ["id", "skills", "regions"]
        required_rfp_fields = ["id", "title", "description", "region", "deadline"]

        for field in required_company_fields:
            if field not in company:
                raise ValueError(f"会社プロフィールに必須フィールドがありません: {field}")

        for field in required_rfp_fields:
            if field not in rfp:
                raise ValueError(f"RFPに必須フィールドがありません: {field}")

        logger.info(
            f"拡張マッチング計算開始: company_id={company['id']}, rfp_id={rfp['id']}"
        )

        # RFP全文を作成（タイトル + 説明）
        rfp_text = f"{rfp['title']}\n{rfp['description']}"

        # NGキーワードチェック（既存ロジックを再利用）
        ng_keywords = company.get("ng_keywords", [])
        if ng_keywords:
            for ng_keyword in ng_keywords:
                if ng_keyword and ng_keyword.lower() in rfp_text.lower():
                    logger.info(
                        f"NGキーワードが検出されました: {ng_keyword} - スコア0を返却"
                    )
                    return {
                        "score": 0,
                        "must_ok": False,
                        "budget_ok": False,
                        "region_ok": False,
                        "factors": {
                            "semantic_skill_match": 0.0,
                            "keyword_skill_match": 0.0,
                            "must": False,
                            "budget": 0.0,
                            "deadline": 0.0,
                            "region": 0.0,
                        },
                        "summary_points": [f"NGキーワード「{ng_keyword}」が含まれています"],
                    }

        # 1. セマンティックスキルマッチ度計算（40%）
        semantic_skill_match = 0.0
        if company_embedding and rfp.get("embedding"):
            try:
                # コサイン類似度を計算
                semantic_skill_match = self._calculate_cosine_similarity(
                    company_embedding, rfp["embedding"]
                )
                logger.debug(
                    f"セマンティックスキルマッチ: {semantic_skill_match:.3f}"
                )
            except Exception as e:
                logger.warning(f"セマンティックスキルマッチ計算エラー: {e}")
                semantic_skill_match = 0.0

        # 2. キーワードスキルマッチ度計算（30%）- 既存ロジックを再利用
        keyword_skill_match = self._calculate_skill_match(company["skills"], rfp_text)

        # 3. 必須要件チェック
        must_ok = self._check_must_requirements(rfp_text)

        # 4. 地域係数
        region_coefficient = self._calculate_region_coefficient(
            company["regions"], rfp["region"]
        )

        # 5. 予算ブースト
        budget_boost = self._calculate_budget_boost(
            company.get("budget_min"),
            company.get("budget_max"),
            rfp.get("budget"),
        )

        # 6. 締切ブースト
        if isinstance(rfp["deadline"], str):
            deadline_date = datetime.fromisoformat(rfp["deadline"]).date()
        else:
            deadline_date = rfp["deadline"]

        deadline_boost = self._calculate_deadline_boost(deadline_date)

        # ベーススコア計算（セマンティック40% + キーワード30% = 70%）
        base_score = (semantic_skill_match * 40) + (keyword_skill_match * 30)

        # 必須要件チェック
        if not must_ok:
            base_score *= 0.5  # 必須要件未達は50%減点

        # 地域係数適用（10%）
        base_score += region_coefficient * 10

        # 予算ブースト適用（10%）
        base_score += budget_boost * 100

        # 締切ブースト適用（10%）
        base_score += deadline_boost * 100

        # 最終スコア（0~100に丸める）
        final_score = min(100, max(0, int(base_score)))

        # 予算条件判定
        budget_ok = True
        if rfp.get("budget") and company.get("budget_min") and company.get("budget_max"):
            budget_ok = (
                company["budget_min"] <= rfp["budget"] <= company["budget_max"]
            )

        # 地域条件判定
        region_ok = rfp["region"] in company["regions"]

        # 要素を辞書にまとめる
        factors = {
            "semantic_skill_match": round(semantic_skill_match, 3),
            "keyword_skill_match": round(keyword_skill_match, 3),
            "must": must_ok,
            "budget": round(budget_boost, 3),
            "deadline": round(deadline_boost, 3),
            "region": round(region_coefficient, 3),
        }

        # サマリーポイント生成（拡張版）
        summary_points = self._generate_enhanced_summary_points(
            company, rfp, factors
        )

        result = {
            "score": final_score,
            "must_ok": must_ok,
            "budget_ok": budget_ok,
            "region_ok": region_ok,
            "factors": factors,
            "summary_points": summary_points,
        }

        logger.info(
            f"拡張マッチング計算完了: score={final_score}, "
            f"semantic={semantic_skill_match:.2f}, keyword={keyword_skill_match:.2f}, "
            f"must_ok={must_ok}, budget_ok={budget_ok}, region_ok={region_ok}"
        )

        return result

    def _calculate_cosine_similarity(
        self, vec1: list[float], vec2: list[float]
    ) -> float:
        """
        2つのベクトルのコサイン類似度を計算します。

        Args:
            vec1: ベクトル1
            vec2: ベクトル2

        Returns:
            コサイン類似度（0.0~1.0）

        Raises:
            ValueError: ベクトルの次元が一致しない場合
        """
        if len(vec1) != len(vec2):
            raise ValueError(
                f"ベクトルの次元が一致しません: {len(vec1)} != {len(vec2)}"
            )

        # 内積を計算
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # ノルムを計算
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        # ゼロ除算を防ぐ
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        # コサイン類似度
        similarity = dot_product / (norm1 * norm2)

        # 0.0~1.0の範囲にクリップ（浮動小数点誤差対策）
        return max(0.0, min(1.0, similarity))

    def _generate_enhanced_summary_points(
        self, company: dict[str, Any], rfp: dict[str, Any], factors: dict[str, Any]
    ) -> list[str]:
        """
        拡張マッチング結果のサマリーポイントを生成します。

        Args:
            company: 会社プロフィール辞書
            rfp: RFP辞書
            factors: スコア計算要素辞書

        Returns:
            サマリーポイントのリスト（最大3点）
        """
        summary_points: list[str] = []

        # セマンティックスキルマッチ度
        semantic_match_percent = int(factors["semantic_skill_match"] * 100)
        keyword_match_percent = int(factors["keyword_skill_match"] * 100)

        if semantic_match_percent >= 80:
            summary_points.append(
                f"AI分析スキルマッチ度 {semantic_match_percent}% (高)"
            )
        elif semantic_match_percent >= 50:
            summary_points.append(
                f"AI分析スキルマッチ度 {semantic_match_percent}% (中)"
            )
        elif keyword_match_percent >= 50:
            summary_points.append(
                f"キーワードスキルマッチ度 {keyword_match_percent}% (中)"
            )
        else:
            summary_points.append("スキルマッチ度 低")

        # 予算条件
        if rfp.get("budget") and company.get("budget_min") and company.get("budget_max"):
            if company["budget_min"] <= rfp["budget"] <= company["budget_max"]:
                summary_points.append("予算範囲内")
            else:
                summary_points.append("予算範囲外")

        # 地域条件
        if rfp["region"] in company["regions"]:
            summary_points.append("対応可能地域")
        else:
            summary_points.append("対応不可地域")

        # 締切情報
        if isinstance(rfp["deadline"], str):
            deadline_date = datetime.fromisoformat(rfp["deadline"]).date()
        else:
            deadline_date = rfp["deadline"]

        days_until_deadline = (deadline_date - date.today()).days

        if days_until_deadline < 0:
            summary_points.append("締切超過")
        elif days_until_deadline <= 7:
            summary_points.append(f"締切まで{days_until_deadline}日（緊急）")
        elif days_until_deadline <= 30:
            summary_points.append(f"締切まで{days_until_deadline}日")

        # 最大3点に制限
        return summary_points[:3]
