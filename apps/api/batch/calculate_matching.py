"""
マッチングスコア計算バッチスクリプト

Supabaseから全会社プロフィールとRFPを取得し、マッチングスコアを計算してmatch_snapshotsテーブルに保存します。
"""

import argparse
import logging
import time
from datetime import datetime
from typing import Any

from config import settings
from database import SupabaseClient
from services.embedding import EmbeddingService
from services.matching_engine import MatchingEngine

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
        description="会社プロフィールとRFPのマッチングスコアを計算してmatch_snapshotsテーブルに保存"
    )

    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="特定ユーザーIDのみ処理（オプション、指定なしは全ユーザー）",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="処理するRFP件数上限（デフォルト: なし）",
    )

    return parser.parse_args()


def fetch_companies(client: Any, user_id: str | None = None) -> list[dict[str, Any]]:
    """
    会社プロフィールを取得します。

    Args:
        client: Supabaseクライアント（Service Role Key使用）
        user_id: 特定ユーザーIDのみ取得（Noneの場合は全ユーザー）

    Returns:
        list[dict]: 会社プロフィールのリスト
    """
    try:
        logger.info("会社プロフィール取得開始")

        query = client.table("companies").select(
            "id, user_id, name, skills, regions, budget_min, budget_max, ng_keywords"
        )

        if user_id:
            query = query.eq("user_id", user_id)

        result = query.execute()

        companies = result.data if result.data else []
        logger.info(f"会社プロフィール取得完了: {len(companies)}件")

        return companies

    except Exception as e:
        logger.error(f"会社プロフィール取得失敗: {e}")
        raise


def fetch_rfps(client: Any, limit: int | None = None) -> list[dict[str, Any]]:
    """
    RFPを取得します（embedding IS NOT NULL）。

    Args:
        client: Supabaseクライアント（Service Role Key使用）
        limit: 取得件数上限（Noneの場合は全件）

    Returns:
        list[dict]: RFPのリスト
    """
    try:
        logger.info("RFP取得開始")

        # embeddingがNOT NULLのRFPを取得
        query = (
            client.table("rfps")
            .select("id, title, description, budget, region, deadline")
            .not_.is_("embedding", "null")
            .order("deadline", desc=False)
        )

        if limit:
            query = query.limit(limit)

        result = query.execute()

        rfps = result.data if result.data else []
        logger.info(f"RFP取得完了: {len(rfps)}件")

        return rfps

    except Exception as e:
        logger.error(f"RFP取得失敗: {e}")
        raise


def delete_existing_snapshots(
    client: Any, user_id: str | None = None
) -> int:
    """
    既存のマッチングスナップショットを削除します。

    Args:
        client: Supabaseクライアント（Service Role Key使用）
        user_id: 特定ユーザーIDのみ削除（Noneの場合は全ユーザー）

    Returns:
        int: 削除された件数
    """
    try:
        logger.info("既存スナップショット削除開始")

        if user_id:
            # 特定ユーザーの既存スナップショットを削除
            result = client.table("match_snapshots").delete().eq("user_id", user_id).execute()
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"既存スナップショット削除完了: {deleted_count}件 (user_id={user_id})")
        else:
            # 全ユーザーの既存スナップショットを削除
            # 注意: 本番環境では慎重に実行すること
            logger.warning("全ユーザーの既存スナップショットを削除します")

            # Supabaseでは DELETE で WHERE 条件なしはサポートされていないため、
            # 全件取得してからIDベースで削除
            existing = client.table("match_snapshots").select("id").execute()
            existing_ids = [row["id"] for row in existing.data] if existing.data else []

            if existing_ids:
                # バッチ削除（1000件ずつ）
                batch_size = 1000
                deleted_count = 0
                for i in range(0, len(existing_ids), batch_size):
                    batch_ids = existing_ids[i:i + batch_size]
                    result = client.table("match_snapshots").delete().in_("id", batch_ids).execute()
                    deleted_count += len(result.data) if result.data else 0

                logger.info(f"既存スナップショット削除完了: {deleted_count}件 (全ユーザー)")
            else:
                logger.info("削除対象のスナップショットがありません")
                deleted_count = 0

        return deleted_count

    except Exception as e:
        logger.error(f"既存スナップショット削除失敗: {e}")
        raise


def save_match_snapshots(
    client: Any, snapshots: list[dict[str, Any]]
) -> tuple[int, int]:
    """
    マッチングスナップショットをSupabaseに保存します（バッチ処理）。

    Args:
        client: Supabaseクライアント（Service Role Key使用）
        snapshots: 保存するスナップショットのリスト

    Returns:
        tuple[int, int]: (成功数, 失敗数)
    """
    if not snapshots:
        return 0, 0

    batch_size = 100
    total_batches = (len(snapshots) + batch_size - 1) // batch_size
    success_count = 0
    failed_count = 0

    for batch_idx in range(0, len(snapshots), batch_size):
        batch_end = min(batch_idx + batch_size, len(snapshots))
        batch_snapshots = snapshots[batch_idx:batch_end]
        current_batch_num = (batch_idx // batch_size) + 1

        try:
            logger.debug(
                f"スナップショット保存バッチ {current_batch_num}/{total_batches}: "
                f"{batch_idx + 1}-{batch_end}件"
            )

            result = client.table("match_snapshots").insert(batch_snapshots).execute()

            if result.data:
                batch_success = len(result.data)
                success_count += batch_success
                logger.debug(
                    f"スナップショット保存バッチ {current_batch_num}/{total_batches} 完了: "
                    f"成功={batch_success}件"
                )
            else:
                failed_count += len(batch_snapshots)
                logger.warning(
                    f"スナップショット保存バッチ {current_batch_num}/{total_batches} 失敗: "
                    f"結果が空です"
                )

        except Exception as e:
            logger.error(
                f"スナップショット保存バッチ {current_batch_num}/{total_batches} 失敗: {e}"
            )
            failed_count += len(batch_snapshots)

    logger.info(f"スナップショット保存完了: 成功={success_count}件, 失敗={failed_count}件")

    return success_count, failed_count


def calculate_and_save_matching(
    user_id: str | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    """
    マッチングスコアを計算してmatch_snapshotsテーブルに保存します。

    Args:
        user_id: 特定ユーザーIDのみ処理（Noneの場合は全ユーザー）
        limit: 処理するRFP件数上限（Noneの場合は全件）

    Returns:
        dict: 処理結果の統計情報
            - total_companies: 会社数
            - total_rfps: RFP数
            - total_processed: 処理総数（会社×RFP）
            - total_success: 成功数
            - total_failed: 失敗数
            - total_saved: 保存成功数
            - elapsed_time: 所要時間（秒）
    """
    start_time = time.time()

    logger.info("=" * 80)
    logger.info("マッチングスコア計算バッチ処理開始")
    logger.info(f"ユーザーID指定: {user_id if user_id else '全ユーザー'}")
    logger.info(f"RFP件数上限: {limit if limit else '制限なし'}")
    logger.info("=" * 80)

    # Supabaseクライアント初期化（Service Role Key使用）
    supabase_client = SupabaseClient.get_service_client()

    # EmbeddingService初期化
    embedding_service = EmbeddingService(api_key=settings.openai_api_key)

    # MatchingEngine初期化
    matching_engine = MatchingEngine(
        supabase_client=supabase_client,
        embedding_service=embedding_service,
    )

    # 既存スナップショット削除
    deleted_count = delete_existing_snapshots(supabase_client, user_id=user_id)

    # 会社プロフィール取得
    companies = fetch_companies(supabase_client, user_id=user_id)

    if not companies:
        logger.warning("処理対象の会社プロフィールがありません")
        return {
            "total_companies": 0,
            "total_rfps": 0,
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_saved": 0,
            "elapsed_time": 0,
        }

    # RFP取得
    rfps = fetch_rfps(supabase_client, limit=limit)

    if not rfps:
        logger.warning("処理対象のRFPがありません")
        return {
            "total_companies": len(companies),
            "total_rfps": 0,
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_saved": 0,
            "elapsed_time": 0,
        }

    # 統計情報初期化
    stats = {
        "total_companies": len(companies),
        "total_rfps": len(rfps),
        "total_processed": 0,
        "total_success": 0,
        "total_failed": 0,
        "total_saved": 0,
        "elapsed_time": 0,
    }

    total_combinations = len(companies) * len(rfps)
    logger.info(
        f"\n処理開始: {len(companies)}社 × {len(rfps)}件のRFP = {total_combinations}件のマッチング計算"
    )

    # マッチングスコア計算
    snapshots: list[dict[str, Any]] = []

    for company_idx, company in enumerate(companies):
        company_num = company_idx + 1
        logger.info(
            f"\n--- 会社 {company_num}/{len(companies)} 処理中: "
            f"company_id={company['id']}, name={company.get('name', '(名前なし)')} ---"
        )

        for rfp_idx, rfp in enumerate(rfps):
            rfp_num = rfp_idx + 1
            combination_num = company_idx * len(rfps) + rfp_num

            try:
                stats["total_processed"] += 1

                # マッチングスコア計算
                result = matching_engine.calculate_matching_score(company, rfp)

                # スナップショット作成
                snapshot = {
                    "user_id": company["user_id"],
                    "rfp_id": rfp["id"],
                    "score": result["score"],
                    "must_ok": result["must_ok"],
                    "budget_ok": result["budget_ok"],
                    "region_ok": result["region_ok"],
                    "factors": result["factors"],
                    "summary_points": result["summary_points"],
                }

                snapshots.append(snapshot)
                stats["total_success"] += 1

                logger.debug(
                    f"[{combination_num}/{total_combinations}] マッチング計算成功: "
                    f"company_id={company['id']}, rfp_id={rfp['id']}, score={result['score']}"
                )

            except Exception as e:
                logger.error(
                    f"[{combination_num}/{total_combinations}] マッチング計算失敗: "
                    f"company_id={company['id']}, rfp_id={rfp['id']}, error={e}"
                )
                stats["total_failed"] += 1
                # エラーが発生しても次の組み合わせの処理を続行

        logger.info(
            f"会社 {company_num}/{len(companies)} 完了: "
            f"処理={len(rfps)}件, "
            f"累計成功={stats['total_success']}/{stats['total_processed']}件"
        )

    # スナップショットを保存
    logger.info(f"\nスナップショット保存開始: {len(snapshots)}件")
    saved_count, save_failed_count = save_match_snapshots(supabase_client, snapshots)
    stats["total_saved"] = saved_count

    # 所要時間計算
    elapsed_time = time.time() - start_time
    stats["elapsed_time"] = round(elapsed_time, 2)

    # 処理結果サマリー
    logger.info("\n" + "=" * 80)
    logger.info("マッチングスコア計算バッチ処理完了")
    logger.info(f"会社数: {stats['total_companies']}社")
    logger.info(f"RFP数: {stats['total_rfps']}件")
    logger.info(f"処理総数: {stats['total_processed']}件")
    logger.info(f"計算成功: {stats['total_success']}件")
    logger.info(f"計算失敗: {stats['total_failed']}件")
    logger.info(
        f"計算成功率: {stats['total_success'] / max(stats['total_processed'], 1) * 100:.1f}%"
    )
    logger.info(f"保存成功: {stats['total_saved']}件")
    logger.info(f"保存失敗: {save_failed_count}件")
    logger.info(
        f"保存成功率: {stats['total_saved'] / max(len(snapshots), 1) * 100:.1f}%"
    )
    logger.info(f"所要時間: {stats['elapsed_time']:.2f}秒")
    logger.info(
        f"平均処理時間: {stats['elapsed_time'] / max(stats['total_processed'], 1):.3f}秒/件"
    )
    logger.info("=" * 80)

    return stats


def main() -> None:
    """メイン処理"""
    # コマンドライン引数パース
    args = parse_args()

    # マッチングスコア計算と保存を実行
    calculate_and_save_matching(
        user_id=args.user_id,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
