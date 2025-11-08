"""
ProposalGeneratorサービスのテストケース

提案書生成サービスの単体テストを行います。
"""
import pytest
from datetime import date, datetime
from pathlib import Path
from jinja2 import TemplateNotFound

from services.proposal_generator import ProposalGenerator


@pytest.mark.unit
class TestProposalGeneratorInit:
    """ProposalGeneratorの初期化テストクラス"""

    def test_初期化_正常系_デフォルトテンプレートディレクトリ(self):
        """デフォルトのテンプレートディレクトリで正常に初期化できることを確認"""
        generator = ProposalGenerator()

        assert generator is not None
        assert generator.env is not None
        # カスタムフィルタが登録されていることを確認
        assert "format_budget" in generator.env.filters
        assert "format_date" in generator.env.filters

    def test_初期化_正常系_カスタムテンプレートディレクトリ(self, tmp_path):
        """カスタムテンプレートディレクトリで正常に初期化できることを確認"""
        # 一時テンプレートディレクトリを作成
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        generator = ProposalGenerator(template_dir=template_dir)

        assert generator is not None
        assert generator.env is not None

    def test_初期化_異常系_テンプレートディレクトリが存在しない(self, tmp_path):
        """存在しないテンプレートディレクトリを指定した場合エラーが発生することを確認"""
        non_existent_dir = tmp_path / "non_existent"

        with pytest.raises(FileNotFoundError, match="テンプレートディレクトリが見つかりません"):
            ProposalGenerator(template_dir=non_existent_dir)


@pytest.mark.unit
class TestFormatBudget:
    """予算フォーマットフィルタのテストクラス"""

    def test_format_budget_正常系_通常の予算(self):
        """通常の予算が正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_budget(10000000)

        assert result == "10,000,000円"

    def test_format_budget_正常系_小さい予算(self):
        """小さい予算が正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_budget(1000)

        assert result == "1,000円"

    def test_format_budget_正常系_ゼロ(self):
        """ゼロが正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_budget(0)

        assert result == "0円"

    def test_format_budget_正常系_None(self):
        """Noneの場合は「未定」を返すことを確認"""
        generator = ProposalGenerator()

        result = generator._format_budget(None)

        assert result == "未定"


@pytest.mark.unit
class TestFormatDate:
    """日付フォーマットフィルタのテストクラス"""

    def test_format_date_正常系_dateオブジェクト(self):
        """dateオブジェクトが正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_date(date(2025, 12, 31))

        assert result == "2025年12月31日"

    def test_format_date_正常系_datetimeオブジェクト(self):
        """datetimeオブジェクトが正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_date(datetime(2025, 12, 31, 15, 30, 0))

        assert result == "2025年12月31日"

    def test_format_date_正常系_ISO形式文字列(self):
        """ISO形式文字列が正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_date("2025-12-31")

        assert result == "2025年12月31日"

    def test_format_date_正常系_ISO形式文字列_時刻付き(self):
        """ISO形式文字列（時刻付き）が正しくフォーマットされることを確認"""
        generator = ProposalGenerator()

        result = generator._format_date("2025-12-31T15:30:00")

        assert result == "2025年12月31日"

    def test_format_date_正常系_None(self):
        """Noneの場合は「未定」を返すことを確認"""
        generator = ProposalGenerator()

        result = generator._format_date(None)

        assert result == "未定"

    def test_format_date_異常系_無効な文字列(self):
        """無効な日付形式の文字列の場合、そのまま返すことを確認"""
        generator = ProposalGenerator()

        result = generator._format_date("invalid-date")

        assert result == "invalid-date"


@pytest.mark.unit
class TestGenerateProposalDraft:
    """提案書生成メソッドのテストクラス"""

    @pytest.fixture
    def mock_rfp_data(self) -> dict:
        """テスト用のRFPデータ"""
        return {
            "id": "rfp-test-123",
            "title": "テストRFP案件",
            "issuing_org": "テスト組織",
            "description": "これはテスト用のRFP案件です。詳細な説明がここに入ります。",
            "budget": 10000000,
            "region": "東京都",
            "deadline": "2025-12-31",
            "url": "https://example.com/rfp/123",
            "external_doc_urls": ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"],
        }

    @pytest.fixture
    def mock_company_data(self) -> dict:
        """テスト用の会社データ"""
        return {
            "id": "company-test-123",
            "name": "テスト株式会社",
            "description": "テスト用の会社です",
            "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL"],
            "regions": ["東京都", "神奈川県"],
        }

    def test_generate_proposal_draft_正常系_基本情報のみ(
        self, mock_rfp_data, mock_company_data
    ):
        """基本情報のみで提案書が正常に生成されることを確認"""
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
        )

        # 生成された提案書のチェック
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        # RFP情報が含まれていることを確認
        assert mock_rfp_data["title"] in result
        assert mock_rfp_data["issuing_org"] in result
        assert "10,000,000円" in result  # 予算がフォーマットされている
        assert "2025年12月31日" in result  # 日付がフォーマットされている

        # 会社情報が含まれていることを確認
        assert mock_company_data["name"] in result
        assert mock_company_data["description"] in result

        # スキルが含まれていることを確認
        for skill in mock_company_data["skills"]:
            assert skill in result

    def test_generate_proposal_draft_正常系_マッチング情報あり(
        self, mock_rfp_data, mock_company_data
    ):
        """マッチング情報ありで提案書が正常に生成されることを確認"""
        generator = ProposalGenerator()

        match_score = 85
        summary_points = [
            "予算条件が適合しています",
            "地域条件が適合しています",
            "高いセマンティック類似度があります",
        ]

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
            match_score=match_score,
            summary_points=summary_points,
        )

        # マッチング情報が含まれていることを確認
        assert "85点" in result
        for point in summary_points:
            assert point in result

    def test_generate_proposal_draft_正常系_予算がNone(
        self, mock_rfp_data, mock_company_data
    ):
        """予算がNoneの場合も正常に生成されることを確認"""
        mock_rfp_data["budget"] = None
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
        )

        assert result is not None
        assert "未定" in result

    def test_generate_proposal_draft_正常系_外部ドキュメントURLなし(
        self, mock_rfp_data, mock_company_data
    ):
        """外部ドキュメントURLがない場合も正常に生成されることを確認"""
        mock_rfp_data["external_doc_urls"] = []
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
        )

        assert result is not None
        assert "外部資料なし" in result

    def test_generate_proposal_draft_異常系_RFP必須フィールド不足(
        self, mock_rfp_data, mock_company_data
    ):
        """RFPの必須フィールドが不足している場合エラーが発生することを確認"""
        # titleフィールドを削除
        del mock_rfp_data["title"]
        generator = ProposalGenerator()

        with pytest.raises(ValueError, match="RFPに必須フィールドがありません: title"):
            generator.generate_proposal_draft(
                rfp=mock_rfp_data,
                company=mock_company_data,
            )

    def test_generate_proposal_draft_異常系_会社必須フィールド不足(
        self, mock_rfp_data, mock_company_data
    ):
        """会社情報の必須フィールドが不足している場合エラーが発生することを確認"""
        # skillsフィールドを削除
        del mock_company_data["skills"]
        generator = ProposalGenerator()

        with pytest.raises(ValueError, match="会社情報に必須フィールドがありません: skills"):
            generator.generate_proposal_draft(
                rfp=mock_rfp_data,
                company=mock_company_data,
            )

    def test_generate_proposal_draft_正常系_会社descriptionがNone(
        self, mock_rfp_data, mock_company_data
    ):
        """会社のdescriptionがNoneでも正常に生成されることを確認"""
        mock_company_data["description"] = None
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
        )

        assert result is not None

    def test_generate_proposal_draft_正常系_URLがNone(
        self, mock_rfp_data, mock_company_data
    ):
        """RFPのURLがNoneでも正常に生成されることを確認"""
        mock_rfp_data["url"] = None
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
        )

        assert result is not None

    def test_generate_proposal_draft_正常系_summary_pointsが空リスト(
        self, mock_rfp_data, mock_company_data
    ):
        """summary_pointsが空リストでも正常に生成されることを確認"""
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
            match_score=85,
            summary_points=[],
        )

        assert result is not None
        assert "85点" in result

    def test_generate_proposal_draft_正常系_地域が複数(
        self, mock_rfp_data, mock_company_data
    ):
        """会社が複数の地域に対応している場合も正常に生成されることを確認"""
        mock_company_data["regions"] = ["東京都", "神奈川県", "千葉県", "埼玉県"]
        generator = ProposalGenerator()

        result = generator.generate_proposal_draft(
            rfp=mock_rfp_data,
            company=mock_company_data,
        )

        assert result is not None
        # 地域が含まれていることを確認
        for region in mock_company_data["regions"]:
            assert region in result
