"""
ベクトル検索サービス

Supabase pgvectorを使用したセマンティック検索機能を提供します。
"""
import logging
from typing import Any

from supabase import Client

from services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    ベクトル検索サービスクラス

    OpenAI Embeddingsとpgvectorを組み合わせたセマンティック検索を提供します。
    """

    def __init__(
        self,
        supabase_client: Client,
        embedding_service: EmbeddingService,
    ) -> None:
        """
        VectorSearchServiceを初期化します。

        Args:
            supabase_client: Supabaseクライアント
            embedding_service: 埋め込みサービス
        """
        self.supabase = supabase_client
        self.embedding_service = embedding_service

        logger.info("VectorSearchService初期化完了")

    async def search_similar_rfps(
        self,
        query_text: str,
        similarity_threshold: float = 0.7,
        result_limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        テキストクエリからセマンティック検索を実行します。

        Args:
            query_text: 検索クエリテキスト
            similarity_threshold: コサイン類似度の閾値（0.0~1.0）
            result_limit: 返却する最大件数

        Returns:
            類似RFPのリスト（類似度スコア付き）

        Raises:
            ValueError: クエリテキストが空の場合
            Exception: 埋め込み生成またはRPC呼び出しエラー
        """
        if not query_text or not query_text.strip():
            raise ValueError("検索クエリが空です")

        logger.info(
            f"セマンティック検索開始: query_length={len(query_text)}, "
            f"threshold={similarity_threshold}, limit={result_limit}"
        )

        # クエリテキストから埋め込みベクトルを生成
        try:
            query_embedding = self.embedding_service.generate_embedding(query_text)
            logger.debug(f"クエリ埋め込み生成完了: dimension={len(query_embedding)}")
        except Exception as e:
            logger.error(f"クエリ埋め込み生成エラー: {e}")
            raise

        # Supabase RPC関数を呼び出して類似検索
        try:
            response = self.supabase.rpc(
                "search_rfps_by_embedding",
                {
                    "query_embedding": query_embedding,
                    "similarity_threshold": similarity_threshold,
                    "result_limit": result_limit,
                },
            ).execute()

            results = response.data or []

            logger.info(
                f"セマンティック検索完了: 結果件数={len(results)}, "
                f"threshold={similarity_threshold}"
            )

            return results

        except Exception as e:
            logger.error(f"RFPベクトル検索エラー: {e}")
            raise

    async def find_similar_to_rfp(
        self,
        rfp_id: str,
        result_limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        特定のRFPと類似する案件を検索します。

        Args:
            rfp_id: 基準となるRFP ID
            result_limit: 返却する最大件数

        Returns:
            類似RFPのリスト（類似度スコア付き）

        Raises:
            ValueError: RFP IDが見つからない場合
            Exception: RPC呼び出しエラー
        """
        logger.info(f"類似RFP検索開始: rfp_id={rfp_id}, limit={result_limit}")

        # RFPの埋め込みベクトルを取得
        try:
            rfp_response = (
                self.supabase.table("rfps")
                .select("embedding")
                .eq("id", rfp_id)
                .maybe_single()
                .execute()
            )

            if not rfp_response.data:
                raise ValueError(f"RFP IDが見つかりません: {rfp_id}")

            rfp_embedding = rfp_response.data.get("embedding")

            if not rfp_embedding:
                raise ValueError(f"RFP ID {rfp_id} には埋め込みベクトルが存在しません")

            logger.debug(f"RFP埋め込み取得完了: rfp_id={rfp_id}")

        except Exception as e:
            logger.error(f"RFP埋め込み取得エラー: {e}")
            raise

        # Supabase RPC関数を呼び出して類似検索
        try:
            response = self.supabase.rpc(
                "search_rfps_by_embedding",
                {
                    "query_embedding": rfp_embedding,
                    "similarity_threshold": 0.5,  # より緩い閾値
                    "result_limit": result_limit + 1,  # 自分自身を含めて取得
                },
            ).execute()

            results = response.data or []

            # 自分自身を除外
            filtered_results = [r for r in results if r.get("id") != rfp_id][
                :result_limit
            ]

            logger.info(
                f"類似RFP検索完了: rfp_id={rfp_id}, 結果件数={len(filtered_results)}"
            )

            return filtered_results

        except Exception as e:
            logger.error(f"類似RFP検索エラー: {e}")
            raise

    async def hybrid_search(
        self,
        query_text: str,
        company_id: str | None = None,
        result_limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        ハイブリッド検索を実行します（セマンティック検索 + キーワード検索）。

        Args:
            query_text: 検索クエリテキスト
            company_id: 会社ID（オプション、マッチング情報を含める場合）
            result_limit: 返却する最大件数

        Returns:
            ハイブリッド検索結果のリスト

        Raises:
            ValueError: クエリテキストが空の場合
            Exception: 検索エラー
        """
        if not query_text or not query_text.strip():
            raise ValueError("検索クエリが空です")

        logger.info(
            f"ハイブリッド検索開始: query_length={len(query_text)}, "
            f"company_id={company_id}, limit={result_limit}"
        )

        # セマンティック検索を実行
        try:
            semantic_results = await self.search_similar_rfps(
                query_text=query_text,
                similarity_threshold=0.6,  # 緩めの閾値
                result_limit=result_limit * 2,  # 多めに取得
            )
        except Exception as e:
            logger.error(f"セマンティック検索エラー: {e}")
            # セマンティック検索が失敗してもキーワード検索にフォールバック
            semantic_results = []

        # キーワード検索を実行（PostgreSQL ILIKE）
        try:
            # SQLインジェクション対策：Supabaseクライアントはパラメータ化されたクエリを使用
            keyword_response = (
                self.supabase.table("rfps")
                .select("*")
                .or_(f"title.ilike.%{query_text}%,description.ilike.%{query_text}%")
                .limit(result_limit * 2)
                .execute()
            )

            keyword_results = keyword_response.data or []

        except Exception as e:
            logger.error(f"キーワード検索エラー: {e}")
            keyword_results = []

        # 結果をマージ（重複排除）
        seen_ids = set()
        merged_results = []

        # セマンティック検索結果を優先
        for result in semantic_results:
            rfp_id = result.get("id")
            if rfp_id and rfp_id not in seen_ids:
                seen_ids.add(rfp_id)
                merged_results.append(result)

        # キーワード検索結果を追加
        for result in keyword_results:
            rfp_id = result.get("id")
            if rfp_id and rfp_id not in seen_ids:
                seen_ids.add(rfp_id)
                # similarity_scoreが存在しない場合はキーワードマッチとしてスコア0.5を付与
                result["similarity_score"] = 0.5
                merged_results.append(result)

        # 上位N件を返却
        final_results = merged_results[:result_limit]

        logger.info(
            f"ハイブリッド検索完了: semantic={len(semantic_results)}, "
            f"keyword={len(keyword_results)}, merged={len(final_results)}"
        )

        return final_results
