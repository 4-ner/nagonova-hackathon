"""
会社スキル埋め込み生成バッチスクリプト

Supabaseから未処理の会社スキルを取得し、埋め込みベクトルを生成してSupabaseに保存します。
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
        description="会社スキルの埋め込みベクトルを生成してSupabaseに保存"
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


def fetch_unprocessed_skills(client: Any, limit: int | None = None) -> list[dict[str, Any]]:
    """
    埋め込みが未生成の会社スキルを取得します。

    Args:
        client: Supabaseクライアント
        limit: 取得件数上限（Noneの場合は全件）

    Returns:
        list[dict]: 未処理会社スキルのリスト（作成日時の古い順）
    """
    try:
        logger.info("未処理会社スキル取得開始")

        # embeddingがNULLの会社スキルを取得（作成日時の古い順）
        query = (
            client.table("company_skill_embeddings")
            .select("id, company_id, skill_text")
            .is_("embedding", "null")
            .order("created_at", desc=False)  # 作成日時の古い順に処理
        )

        if limit:
            query = query.limit(limit)

        result = query.execute()

        skills = result.data if result.data else []
        logger.info(f"未処理会社スキル取得完了: {len(skills)}件")

        return skills

    except Exception as e:
        logger.error(f"未処理会社スキル取得失敗: {e}")
        raise


def generate_embedding_text(skill: dict[str, Any]) -> str:
    """
    会社スキルデータから埋め込み生成用のテキストを作成します。

    Args:
        skill: 会社スキルデータ

    Returns:
        str: 埋め込み生成用テキスト（スキルテキストのみ）

    Raises:
        ValueError: skill_textが空または存在しない場合
    """
    skill_text = skill.get("skill_text", "").strip()

    if not skill_text:
        raise ValueError(
            f"skill_textが空です: skill_id={skill.get('id', 'unknown')}"
        )

    return skill_text


def update_skill_embedding(
    client: Any, skill_id: str, embedding: list[float]
) -> bool:
    """
    会社スキルの埋め込みベクトルをSupabaseに保存します。

    Args:
        client: Supabaseクライアント
        skill_id: 会社スキルID
        embedding: 埋め込みベクトル

    Returns:
        bool: 更新成功時True、失敗時False
    """
    try:
        result = (
            client.table("company_skill_embeddings")
            .update({"embedding": embedding})
            .eq("id", skill_id)
            .execute()
        )

        if result.data:
            logger.debug(f"埋め込み更新成功: skill_id={skill_id}")
            return True
        else:
            logger.warning(f"埋め込み更新結果が空です: skill_id={skill_id}")
            return False

    except Exception as e:
        logger.error(f"埋め込み更新失敗: skill_id={skill_id}, error={e}")
        return False


def generate_and_save_embeddings(
    batch_size: int,
    limit: int | None = None,
) -> dict[str, int]:
    """
    未処理会社スキルの埋め込みを生成してSupabaseに保存します。

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
    logger.info("会社スキルEmbedding生成バッチ処理開始")
    logger.info(f"バッチサイズ: {batch_size}")
    logger.info(f"処理件数上限: {limit if limit else '制限なし'}")
    logger.info("=" * 80)

    # Supabaseクライアント初期化（Service Role Key使用）
    supabase_client = SupabaseClient.get_service_client()

    try:
        # EmbeddingService初期化
        embedding_service = EmbeddingService(api_key=settings.openai_api_key)

        # 未処理会社スキル取得
        skills = fetch_unprocessed_skills(supabase_client, limit=limit)

        if not skills:
            logger.info("処理対象の会社スキルがありません")
            return {
                "total_processed": 0,
                "total_success": 0,
                "total_failed": 0,
            }

        stats = {
            "total_processed": len(skills),
            "total_success": 0,
            "total_failed": 0,
        }

        logger.info(f"\n処理開始: {len(skills)}件の会社スキルを処理します")

        # バッチ処理
        total_batches = (len(skills) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(skills), batch_size):
            batch_end = min(batch_idx + batch_size, len(skills))
            batch_skills = skills[batch_idx:batch_end]
            current_batch_num = (batch_idx // batch_size) + 1

            logger.info(
                f"\n--- バッチ {current_batch_num}/{total_batches} 処理中 "
                f"(スキル {batch_idx + 1}-{batch_end}) ---"
            )

            # バッチ内の各会社スキルを処理
            batch_success = 0
            batch_failed = 0

            for i, skill in enumerate(batch_skills):
                skill_index = batch_idx + i + 1
                skill_id = skill.get("id", "")

                try:
                    # 埋め込み生成用テキスト作成
                    text = generate_embedding_text(skill)

                    # 埋め込み生成
                    logger.debug(
                        f"[{skill_index}/{len(skills)}] 埋め込み生成中: "
                        f"skill_id={skill_id}, skill_text={skill.get('skill_text', '')[:50]}..."
                    )
                    embedding = embedding_service.generate_embedding(text)

                    # Supabaseに保存
                    if update_skill_embedding(supabase_client, skill_id, embedding):
                        batch_success += 1
                        stats["total_success"] += 1
                        logger.info(
                            f"[{skill_index}/{len(skills)}] 処理成功: "
                            f"skill_id={skill_id}"
                        )
                    else:
                        batch_failed += 1
                        stats["total_failed"] += 1

                except Exception as e:
                    logger.error(
                        f"[{skill_index}/{len(skills)}] 処理失敗: "
                        f"skill_id={skill_id}, error={e}"
                    )
                    batch_failed += 1
                    stats["total_failed"] += 1
                    # エラーが発生しても次の会社スキルの処理を続行

            logger.info(
                f"バッチ {current_batch_num}/{total_batches} 完了: "
                f"成功={batch_success}/{len(batch_skills)}, "
                f"失敗={batch_failed}/{len(batch_skills)}"
            )

        # 処理結果サマリー
        logger.info("\n" + "=" * 80)
        logger.info("会社スキルEmbedding生成バッチ処理完了")
        logger.info(f"処理総数: {stats['total_processed']}件")
        logger.info(f"成功: {stats['total_success']}件")
        logger.info(f"失敗: {stats['total_failed']}件")
        logger.info(
            f"成功率: {stats['total_success'] / max(stats['total_processed'], 1) * 100:.1f}%"
        )
        logger.info("=" * 80)

        return stats

    finally:
        # リソースのクリーンアップ
        if hasattr(supabase_client, 'close'):
            try:
                supabase_client.close()
                logger.debug("Supabaseクライアントをクローズしました")
            except Exception as e:
                logger.warning(f"Supabaseクライアントのクローズ中にエラー: {e}")


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
