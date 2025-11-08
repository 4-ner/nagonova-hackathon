"""
提案書生成サービス

RFP情報と会社情報を元に、提案書のドラフトをMarkdown形式で生成します。
"""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    select_autoescape,
)

# ロガー設定
logger = logging.getLogger(__name__)


class ProposalGenerator:
    """
    提案書生成クラス

    Jinja2テンプレートエンジンを使用して、RFP情報と会社情報から
    提案書のドラフトをMarkdown形式で生成します。
    """

    def __init__(self, template_dir: Path | None = None) -> None:
        """
        ProposalGeneratorを初期化します。

        Args:
            template_dir: テンプレートディレクトリのパス（省略時は標準パス）

        Raises:
            FileNotFoundError: テンプレートディレクトリが見つからない場合
        """
        if template_dir is None:
            # デフォルトのテンプレートディレクトリ
            template_dir = Path(__file__).parent.parent / "templates"

        if not template_dir.exists():
            error_msg = f"テンプレートディレクトリが見つかりません: {template_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Jinja2環境をセットアップ
        # セキュリティのため、ユーザー入力を含む変数は明示的にエスケープする
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["md", "markdown"]),
            trim_blocks=True,  # ブロック後の改行を削除
            lstrip_blocks=True,  # ブロック前の空白を削除
        )

        # カスタムフィルタを登録
        self.env.filters["format_budget"] = self._format_budget
        self.env.filters["format_date"] = self._format_date

        logger.info(f"ProposalGenerator初期化完了: template_dir={template_dir}")

    def generate_proposal_draft(
        self,
        rfp: dict[str, Any],
        company: dict[str, Any],
        match_score: int | None = None,
        summary_points: list[str] | None = None,
    ) -> str:
        """
        提案書ドラフトを生成します。

        Args:
            rfp: RFP情報辞書
                - id: UUID
                - title: str - タイトル
                - issuing_org: str - 発注機関名
                - description: str - 説明
                - budget: int | None - 予算
                - region: str - 都道府県コード
                - deadline: date | str - 締切日
                - url: str | None - RFP URL
                - external_doc_urls: list[str] - 外部ドキュメントURL配列
            company: 会社情報辞書
                - id: UUID
                - name: str - 会社名
                - description: str | None - 企業説明
                - skills: list[str] - 保有スキル配列
                - regions: list[str] - 対応可能な都道府県コード配列
            match_score: マッチングスコア（0~100、オプション）
            summary_points: マッチングサマリーポイント（オプション）

        Returns:
            提案書ドラフトのMarkdown文字列

        Raises:
            ValueError: 必須フィールドが不足している場合
            TemplateNotFound: テンプレートファイルが見つからない場合
        """
        # 必須フィールドチェック
        required_rfp_fields = [
            "id",
            "title",
            "issuing_org",
            "description",
            "region",
            "deadline",
        ]
        required_company_fields = ["id", "name", "skills", "regions"]

        for field in required_rfp_fields:
            if field not in rfp:
                raise ValueError(f"RFPに必須フィールドがありません: {field}")

        for field in required_company_fields:
            if field not in company:
                raise ValueError(f"会社情報に必須フィールドがありません: {field}")

        logger.info(
            f"提案書生成開始: rfp_id={rfp['id']}, company_id={company['id']}"
        )

        try:
            # テンプレートを読み込み
            template = self.env.get_template("proposal_template.md")

            # テンプレート変数を準備
            context = {
                "rfp": rfp,
                "company": company,
                "match_score": match_score,
                "summary_points": summary_points or [],
            }

            # テンプレートをレンダリング
            proposal_markdown = template.render(**context)

            logger.info(
                f"提案書生成完了: rfp_id={rfp['id']}, company_id={company['id']}, "
                f"length={len(proposal_markdown)}"
            )

            return proposal_markdown

        except TemplateNotFound as e:
            error_msg = f"テンプレートファイルが見つかりません: {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"提案書生成エラー: {e}"
            logger.error(error_msg)
            raise

    def _format_budget(self, budget: int | None) -> str:
        """
        予算を日本円形式でフォーマットします。

        Args:
            budget: 予算（円）

        Returns:
            フォーマットされた予算文字列（例: "1,000,000円"）
            予算がNoneの場合は「未定」
        """
        if budget is None:
            return "未定"

        # 3桁区切りのカンマを追加
        return f"{budget:,}円"

    def _format_date(self, date_value: date | str | datetime | None) -> str:
        """
        日付を日本語形式でフォーマットします。

        Args:
            date_value: 日付（date、datetime、ISO形式文字列、またはNone）

        Returns:
            フォーマットされた日付文字列（例: "2025年11月8日"）
            日付がNoneの場合は「未定」
        """
        if date_value is None:
            return "未定"

        # ISO形式文字列の場合はdateオブジェクトに変換
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value).date()
            except ValueError:
                logger.warning(f"無効な日付形式: {date_value}")
                return str(date_value)

        # datetimeの場合はdateに変換
        if isinstance(date_value, datetime):
            date_value = date_value.date()

        # 日本語形式にフォーマット
        return f"{date_value.year}年{date_value.month}月{date_value.day}日"
