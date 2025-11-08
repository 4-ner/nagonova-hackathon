"""
KKJ API日時形式パーサー

KKJ APIの日時形式（YYYY/MM/DD HH:MM:SS）をPostgreSQL TIMESTAMP WITH TIME ZONEに変換します。
"""

from datetime import datetime
from typing import Optional

import pytz


def parse_kkj_datetime(
    date_str: Optional[str], timezone: str = "Asia/Tokyo"
) -> Optional[datetime]:
    """
    KKJ API日時文字列をタイムゾーン付きdatetimeオブジェクトに変換します。

    KKJ APIから返される日時形式（YYYY/MM/DD HH:MM:SS）をパースし、
    指定されたタイムゾーンを付与したdatetimeオブジェクトを返します。

    Args:
        date_str: KKJ API日時文字列（例: "2025/11/15 14:00:00"）
                 None、空文字列、または無効なフォーマットの場合はNoneを返します
        timezone: タイムゾーン名（デフォルト: "Asia/Tokyo"）
                 pytzでサポートされるタイムゾーン名を指定できます

    Returns:
        タイムゾーン付きdatetimeオブジェクト、またはNone

    Examples:
        >>> parse_kkj_datetime("2025/11/15 14:00:00")
        datetime.datetime(2025, 11, 15, 14, 0, 0, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>)

        >>> parse_kkj_datetime("")
        None

        >>> parse_kkj_datetime(None)
        None

        >>> parse_kkj_datetime("invalid")
        None

        >>> parse_kkj_datetime("2025/12/01 09:30:00", "UTC")
        datetime.datetime(2025, 12, 1, 9, 30, 0, tzinfo=<UTC>)
    """
    # None または 空文字列の場合はNoneを返す
    if not date_str:
        return None

    try:
        # KKJ API日時形式でパース
        naive_dt = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")

        # タイムゾーンを付与
        tz = pytz.timezone(timezone)
        aware_dt = tz.localize(naive_dt)

        return aware_dt

    except (ValueError, pytz.exceptions.UnknownTimeZoneError):
        # パースエラーまたは無効なタイムゾーンの場合はNoneを返す
        return None
