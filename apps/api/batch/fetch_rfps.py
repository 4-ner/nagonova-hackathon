"""
RFP取得バッチスクリプト

KKJ APIから指定都道府県のRFPを取得してSupabaseに保存します。
"""

import argparse
import logging
from datetime import datetime
from typing import Any

from config import settings
from database import SupabaseClient
from services.kkj_api import KKJAPIClient

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    コマンドライン引数をパースします。

    Returns:
        argparse.Namespace: パースされた引数
    """
    parser = argparse.ArgumentParser(
        description="KKJ APIからRFPを取得してSupabaseに保存"
    )

    parser.add_argument(
        "--prefectures",
        type=str,
        default="13,27,28,40,01,11,12,14,23",
        help=(
            "都道府県コード（カンマ区切り）。"
            "デフォルト: 13,27,28,40,01,11,12,14,23 "
            "(東京、大阪、兵庫、福岡、北海道、埼玉、千葉、神奈川、愛知)"
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="県あたりの取得件数（デフォルト: 100）",
    )

    parser.add_argument(
        "--query",
        type=str,
        default="*",
        help="検索キーワード（デフォルト: *）",
    )

    parser.add_argument(
        "--ng-keywords",
        type=str,
        default="保守,運用,メンテナンス",
        help="NGキーワード（カンマ区切り、デフォルト: 保守,運用,メンテナンス）",
    )

    return parser.parse_args()


def map_rfp_to_db_record(rfp_data: dict[str, Any]) -> dict[str, Any]:
    """
    KKJ APIのRFPデータをデータベースレコード形式に変換します。

    Args:
        rfp_data: KKJ APIから取得したRFPデータ

    Returns:
        dict: データベースレコード形式のデータ
    """
    # 添付ファイルURLを抽出
    external_doc_urls = []
    for attachment in rfp_data.get("attachments", []):
        uri = attachment.get("uri", "")
        if uri:
            external_doc_urls.append(uri)

    # 締切日の処理: CftIssueDateを使用（YYYY-MM-DD形式）
    deadline_str = rfp_data.get("cft_issue_date", "")
    if deadline_str:
        try:
            # YYYY-MM-DD形式の場合はそのまま使用
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                # YYYY/MM/DD形式の場合は変換
                deadline_date = datetime.strptime(deadline_str, "%Y/%m/%d").date()
            except ValueError:
                # パースできない場合は現在日付を使用
                logger.warning(
                    f"締切日のパースに失敗しました: {deadline_str}. "
                    f"現在日付を使用します。"
                )
                deadline_date = datetime.now().date()
    else:
        deadline_date = datetime.now().date()

    return {
        "external_id": rfp_data.get("key", ""),
        "title": rfp_data.get("project_name", ""),
        "issuing_org": rfp_data.get("organization_name", ""),
        "description": rfp_data.get("project_description", ""),
        "budget": None,  # KKJ APIからは取得できないため、Noneを設定
        "region": rfp_data.get("prefecture_name", ""),
        "deadline": deadline_date.isoformat(),
        "url": rfp_data.get("external_document_uri", ""),
        "external_doc_urls": external_doc_urls,
        "fetched_at": datetime.now().isoformat(),
    }


def upsert_rfp(client: Any, rfp_record: dict[str, Any]) -> bool:
    """
    RFPデータをSupabaseにUPSERTします。

    Args:
        client: Supabaseクライアント
        rfp_record: データベースレコード形式のRFPデータ

    Returns:
        bool: UPSERT成功時True、失敗時False
    """
    try:
        # UPSERTを実行（external_idで重複チェック）
        result = (
            client.table("rfps")
            .upsert(
                rfp_record,
                on_conflict="external_id",  # external_idで重複チェック
            )
            .execute()
        )

        if result.data:
            logger.debug(
                f"UPSERT成功: external_id={rfp_record['external_id']}, "
                f"title={rfp_record['title']}"
            )
            return True
        else:
            logger.warning(
                f"UPSERT結果が空です: external_id={rfp_record['external_id']}"
            )
            return False

    except Exception as e:
        logger.error(
            f"UPSERT失敗: external_id={rfp_record['external_id']}, "
            f"error={e}"
        )
        return False


def fetch_and_save_rfps(
    prefecture_codes: list[str],
    count: int,
    query: str,
    ng_keywords: list[str],
) -> dict[str, int]:
    """
    指定都道府県のRFPを取得してSupabaseに保存します。

    Args:
        prefecture_codes: 都道府県コードのリスト
        count: 県あたりの取得件数
        query: 検索キーワード
        ng_keywords: NGキーワードのリスト

    Returns:
        dict: 処理結果の統計情報
            - total_fetched: 取得総数
            - total_saved: 保存成功数
            - total_failed: 保存失敗数
    """
    logger.info("=" * 80)
    logger.info("RFP取得バッチ処理開始")
    logger.info(f"対象都道府県: {prefecture_codes}")
    logger.info(f"県あたり取得件数: {count}")
    logger.info(f"検索キーワード: {query}")
    logger.info(f"NGキーワード: {ng_keywords}")
    logger.info("=" * 80)

    # KKJ APIクライアント初期化
    kkj_client = KKJAPIClient(api_url=settings.kkj_api_url)

    # Supabaseクライアント初期化（Service Role Key使用）
    supabase_client = SupabaseClient.get_service_client()

    stats = {
        "total_fetched": 0,
        "total_saved": 0,
        "total_failed": 0,
    }

    # 都道府県ごとに処理
    for prefecture_code in prefecture_codes:
        logger.info(f"\n--- 都道府県コード: {prefecture_code} の処理開始 ---")

        try:
            # RFP取得
            rfps = kkj_client.fetch_rfps(
                prefecture_code=prefecture_code,
                count=count,
                query=query,
                ng_keywords=ng_keywords,
            )

            logger.info(f"取得件数: {len(rfps)}件")
            stats["total_fetched"] += len(rfps)

            # 各RFPをSupabaseに保存
            saved_count = 0
            failed_count = 0

            for rfp in rfps:
                # データベースレコード形式に変換
                rfp_record = map_rfp_to_db_record(rfp)

                # UPSERT実行
                if upsert_rfp(supabase_client, rfp_record):
                    saved_count += 1
                else:
                    failed_count += 1

            logger.info(f"保存成功: {saved_count}件")
            logger.info(f"保存失敗: {failed_count}件")

            stats["total_saved"] += saved_count
            stats["total_failed"] += failed_count

        except Exception as e:
            logger.error(
                f"都道府県コード {prefecture_code} の処理中にエラー発生: {e}"
            )
            # エラーが発生しても次の都道府県の処理を続行
            continue

    # 処理結果サマリー
    logger.info("\n" + "=" * 80)
    logger.info("RFP取得バッチ処理完了")
    logger.info(f"取得総数: {stats['total_fetched']}件")
    logger.info(f"保存成功: {stats['total_saved']}件")
    logger.info(f"保存失敗: {stats['total_failed']}件")
    logger.info(
        f"成功率: {stats['total_saved'] / max(stats['total_fetched'], 1) * 100:.1f}%"
    )
    logger.info("=" * 80)

    return stats


def main() -> None:
    """メイン処理"""
    # コマンドライン引数パース
    args = parse_args()

    # 都道府県コードをリストに変換
    prefecture_codes = [code.strip() for code in args.prefectures.split(",")]

    # NGキーワードをリストに変換
    ng_keywords = [keyword.strip() for keyword in args.ng_keywords.split(",")]

    # RFP取得と保存を実行
    fetch_and_save_rfps(
        prefecture_codes=prefecture_codes,
        count=args.count,
        query=args.query,
        ng_keywords=ng_keywords,
    )


if __name__ == "__main__":
    main()
