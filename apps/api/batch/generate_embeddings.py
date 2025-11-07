"""
Embedding生成バッチスクリプト

Supabaseから未処理のRFPを取得し、埋め込みベクトルを生成してSupabaseに保存します。
"""

import argparse
import logging
from typing import Any

from config import settings
from database import SupabaseClient
from services.embedding import EmbeddingService

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
        description="RFPの埋め込みベクトルを生成してSupabaseに保存"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="バッチサイズ（デフォルト: 100）",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="処理件数上限（デフォルト: なし）",
    )

    return parser.parse_args()


def fetch_unprocessed_rfps(client: Any, limit: int | None = None) -> list[dict[str, Any]]:
    """
    埋め込みが未生成のRFPを取得します。

    Args:
        client: Supabaseクライアント
        limit: 取得件数上限（Noneの場合は全件）

    Returns:
        list[dict]: 未処理RFPのリスト
    """
    try:
        logger.info("未処理RFP取得開始")

        # embeddingがNULLのRFPを取得
        query = client.table("rfps").select("id, title, description").is_("embedding", "null")

        if limit:
            query = query.limit(limit)

        result = query.execute()

        rfps = result.data if result.data else []
        logger.info(f"未処理RFP取得完了: {len(rfps)}件")

        return rfps

    except Exception as e:
        logger.error(f"未処理RFP取得失敗: {e}")
        raise


def generate_embedding_text(rfp: dict[str, Any]) -> str:
    """
    RFPデータから埋め込み生成用のテキストを作成します。

    Args:
        rfp: RFPデータ

    Returns:
        str: 埋め込み生成用テキスト（タイトル + 説明）
    """
    title = rfp.get("title", "")
    description = rfp.get("description", "")

    return f"{title}\n\n{description}"


def update_rfp_embedding(
    client: Any, rfp_id: str, embedding: list[float]
) -> bool:
    """
    RFPの埋め込みベクトルをSupabaseに保存します。

    Args:
        client: Supabaseクライアント
        rfp_id: RFP ID
        embedding: 埋め込みベクトル

    Returns:
        bool: 更新成功時True、失敗時False
    """
    try:
        result = (
            client.table("rfps")
            .update({"embedding": embedding})
            .eq("id", rfp_id)
            .execute()
        )

        if result.data:
            logger.debug(f"埋め込み更新成功: rfp_id={rfp_id}")
            return True
        else:
            logger.warning(f"埋め込み更新結果が空です: rfp_id={rfp_id}")
            return False

    except Exception as e:
        logger.error(f"埋め込み更新失敗: rfp_id={rfp_id}, error={e}")
        return False


def generate_and_save_embeddings(
    batch_size: int,
    limit: int | None = None,
) -> dict[str, int]:
    """
    未処理RFPの埋め込みを生成してSupabaseに保存します。

    Args:
        batch_size: バッチサイズ
        limit: 処理件数上限（Noneの場合は全件）

    Returns:
        dict: 処理結果の統計情報
            - total_processed: 処理総数
            - total_success: 成功数
            - total_failed: 失敗数
    """
    logger.info("=" * 80)
    logger.info("Embedding生成バッチ処理開始")
    logger.info(f"バッチサイズ: {batch_size}")
    logger.info(f"処理件数上限: {limit if limit else '制限なし'}")
    logger.info("=" * 80)

    # Supabaseクライアント初期化（Service Role Key使用）
    supabase_client = SupabaseClient.get_service_client()

    # EmbeddingService初期化
    embedding_service = EmbeddingService(api_key=settings.openai_api_key)

    # 未処理RFP取得
    rfps = fetch_unprocessed_rfps(supabase_client, limit=limit)

    if not rfps:
        logger.info("処理対象のRFPがありません")
        return {
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
        }

    stats = {
        "total_processed": len(rfps),
        "total_success": 0,
        "total_failed": 0,
    }

    logger.info(f"\n処理開始: {len(rfps)}件のRFPを処理します")

    # バッチ処理
    total_batches = (len(rfps) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(rfps), batch_size):
        batch_end = min(batch_idx + batch_size, len(rfps))
        batch_rfps = rfps[batch_idx:batch_end]
        current_batch_num = (batch_idx // batch_size) + 1

        logger.info(
            f"\n--- バッチ {current_batch_num}/{total_batches} 処理中 "
            f"(RFP {batch_idx + 1}-{batch_end}) ---"
        )

        # バッチ内の各RFPを処理
        batch_success = 0
        batch_failed = 0

        for i, rfp in enumerate(batch_rfps):
            rfp_index = batch_idx + i + 1
            rfp_id = rfp.get("id", "")

            try:
                # 埋め込み生成用テキスト作成
                text = generate_embedding_text(rfp)

                # 埋め込み生成
                logger.debug(
                    f"[{rfp_index}/{len(rfps)}] 埋め込み生成中: "
                    f"rfp_id={rfp_id}, title={rfp.get('title', '')[:50]}..."
                )
                embedding = embedding_service.generate_embedding(text)

                # Supabaseに保存
                if update_rfp_embedding(supabase_client, rfp_id, embedding):
                    batch_success += 1
                    stats["total_success"] += 1
                    logger.info(
                        f"[{rfp_index}/{len(rfps)}] 処理成功: "
                        f"rfp_id={rfp_id}"
                    )
                else:
                    batch_failed += 1
                    stats["total_failed"] += 1

            except Exception as e:
                logger.error(
                    f"[{rfp_index}/{len(rfps)}] 処理失敗: "
                    f"rfp_id={rfp_id}, error={e}"
                )
                batch_failed += 1
                stats["total_failed"] += 1
                # エラーが発生しても次のRFPの処理を続行

        logger.info(
            f"バッチ {current_batch_num}/{total_batches} 完了: "
            f"成功={batch_success}/{len(batch_rfps)}, "
            f"失敗={batch_failed}/{len(batch_rfps)}"
        )

    # 処理結果サマリー
    logger.info("\n" + "=" * 80)
    logger.info("Embedding生成バッチ処理完了")
    logger.info(f"処理総数: {stats['total_processed']}件")
    logger.info(f"成功: {stats['total_success']}件")
    logger.info(f"失敗: {stats['total_failed']}件")
    logger.info(
        f"成功率: {stats['total_success'] / max(stats['total_processed'], 1) * 100:.1f}%"
    )
    logger.info("=" * 80)

    return stats


def main() -> None:
    """メイン処理"""
    # コマンドライン引数パース
    args = parse_args()

    # Embedding生成と保存を実行
    generate_and_save_embeddings(
        batch_size=args.batch_size,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
