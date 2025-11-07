"""
サービスレイヤー

外部API連携やビジネスロジックを提供します。
"""

from .kkj_api import KKJAPIClient

__all__ = ["KKJAPIClient"]
