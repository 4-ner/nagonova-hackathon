"""
datetime_parserモジュールのテスト
"""

from datetime import datetime

import pytest
import pytz

from utils.datetime_parser import parse_kkj_datetime


class TestParseKkjDatetime:
    """parse_kkj_datetime関数のテストクラス"""

    def test_valid_datetime_string(self):
        """正常な日時文字列のパース"""
        result = parse_kkj_datetime("2025/11/15 14:00:00")

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 0
        assert result.second == 0
        # タイムゾーン名の比較（pytzオブジェクト自体は異なる可能性があるため）
        assert result.tzinfo.zone == "Asia/Tokyo"

    def test_empty_string(self):
        """空文字列はNoneを返す"""
        result = parse_kkj_datetime("")
        assert result is None

    def test_none_value(self):
        """Noneは�Noneを返す"""
        result = parse_kkj_datetime(None)
        assert result is None

    def test_invalid_format(self):
        """無効なフォーマットはNoneを返す"""
        result = parse_kkj_datetime("invalid")
        assert result is None

    def test_wrong_date_format(self):
        """間違った日付フォーマットはNoneを返す"""
        result = parse_kkj_datetime("2025-11-15 14:00:00")  # ハイフン区切り
        assert result is None

    def test_partial_datetime(self):
        """不完全な日時文字列はNoneを返す"""
        result = parse_kkj_datetime("2025/11/15")
        assert result is None

    def test_utc_timezone(self):
        """UTCタイムゾーンの指定"""
        result = parse_kkj_datetime("2025/12/01 09:30:00", "UTC")

        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 1
        assert result.hour == 9
        assert result.minute == 30
        assert result.second == 0
        assert result.tzinfo == pytz.UTC

    def test_us_eastern_timezone(self):
        """US/Easternタイムゾーンの指定"""
        result = parse_kkj_datetime("2025/06/15 10:00:00", "US/Eastern")

        assert result is not None
        assert result.tzinfo.zone == "US/Eastern"

    def test_invalid_timezone(self):
        """無効なタイムゾーン名はNoneを返す"""
        result = parse_kkj_datetime("2025/11/15 14:00:00", "Invalid/Timezone")
        assert result is None

    def test_leap_year_date(self):
        """閏年の日付もパース可能"""
        result = parse_kkj_datetime("2024/02/29 12:00:00")

        assert result is not None
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29

    def test_invalid_date(self):
        """存在しない日付はNoneを返す"""
        result = parse_kkj_datetime("2025/02/30 12:00:00")
        assert result is None

    def test_midnight(self):
        """深夜0時のパース"""
        result = parse_kkj_datetime("2025/11/15 00:00:00")

        assert result is not None
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_end_of_day(self):
        """23:59:59のパース"""
        result = parse_kkj_datetime("2025/11/15 23:59:59")

        assert result is not None
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_whitespace_only(self):
        """空白のみの文字列はNoneを返す"""
        result = parse_kkj_datetime("   ")
        assert result is None
