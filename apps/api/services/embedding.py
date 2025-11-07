"""
OpenAI Embeddings API連携サービス

テキストから埋め込みベクトルを生成します。
"""

import logging
import re
import time
from typing import Any

from openai import OpenAI, OpenAIError, RateLimitError

# ロガー設定
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    OpenAI Embeddings API連携サービス

    text-embedding-3-smallモデルを使用して、テキストから1536次元の埋め込みベクトルを生成します。
    """

    def __init__(self, api_key: str) -> None:
        """
        EmbeddingServiceを初期化します。

        Args:
            api_key: OpenAI APIキー

        Raises:
            ValueError: APIキーが空の場合
        """
        if not api_key or not api_key.strip():
            raise ValueError("OpenAI APIキーが指定されていません")

        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        self.max_retries = 3  # 最大リトライ回数
        self.timeout = 60.0  # タイムアウト: 60秒
        self.rate_limit_wait = 60.0  # レート制限時の待機時間: 60秒
        self.batch_delay = 0.5  # バッチ処理時のリクエスト間隔: 0.5秒

        logger.info(
            f"EmbeddingService初期化完了: model={self.model}, "
            f"dimensions={self.dimensions}"
        )

    def generate_embedding(self, text: str) -> list[float]:
        """
        単一テキストの埋め込みベクトルを生成します。

        Args:
            text: 埋め込みを生成するテキスト（最大8191トークン）

        Returns:
            1536次元の埋め込みベクトル（float配列）

        Raises:
            ValueError: テキストが空の場合
            OpenAIError: OpenAI APIエラー
        """
        # テキストクリーニング
        cleaned_text = self._clean_text(text)

        logger.debug(f"埋め込み生成開始: text_length={len(cleaned_text)}")

        # リトライロジック
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"リクエスト試行 {attempt}/{self.max_retries}")

                # OpenAI Embeddings API呼び出し
                response = self.client.embeddings.create(
                    model=self.model,
                    input=cleaned_text,
                    dimensions=self.dimensions,
                )

                # 埋め込みベクトルを抽出
                embedding = response.data[0].embedding

                logger.debug(
                    f"埋め込み生成成功: dimension={len(embedding)}, "
                    f"usage={response.usage.total_tokens} tokens"
                )

                return embedding

            except RateLimitError as e:
                logger.warning(
                    f"レート制限エラー発生 (試行 {attempt}/{self.max_retries}): {e}"
                )
                last_exception = e

                if attempt < self.max_retries:
                    logger.info(
                        f"レート制限: {self.rate_limit_wait}秒待機後にリトライします..."
                    )
                    time.sleep(self.rate_limit_wait)
                else:
                    logger.error(
                        f"レート制限エラー: 最大リトライ回数({self.max_retries})到達"
                    )

            except OpenAIError as e:
                logger.warning(
                    f"OpenAI APIエラー発生 (試行 {attempt}/{self.max_retries}): {e}"
                )
                last_exception = e

                if attempt < self.max_retries:
                    # 指数バックオフでリトライ
                    wait_time = 2**attempt
                    logger.info(f"{wait_time}秒後にリトライします...")
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"OpenAI APIエラー: 最大リトライ回数({self.max_retries})到達"
                    )

            except Exception as e:
                logger.error(f"予期しないエラー: {e}")
                raise

        # すべてのリトライ失敗
        error_msg = f"埋め込み生成失敗: 最大リトライ回数({self.max_retries})を超えました"
        logger.error(error_msg)
        raise last_exception or Exception(error_msg)

    def generate_embeddings_batch(
        self, texts: list[str], batch_size: int = 100
    ) -> list[list[float]]:
        """
        複数のテキストをバッチ処理で埋め込みベクトルに変換します。

        バッチサイズごとに分割して処理し、エラーが発生した場合はスキップして続行します。

        Args:
            texts: 埋め込みを生成するテキストのリスト
            batch_size: 1回のバッチサイズ（デフォルト100）

        Returns:
            埋め込みベクトルのリスト（各テキストに対応する1536次元のベクトル）
            エラーが発生したテキストの位置には空のリストが入ります
        """
        if not texts:
            logger.warning("テキストリストが空です")
            return []

        logger.info(
            f"バッチ埋め込み生成開始: total_texts={len(texts)}, "
            f"batch_size={batch_size}"
        )

        embeddings: list[list[float]] = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(texts), batch_size):
            batch_end = min(batch_idx + batch_size, len(texts))
            batch_texts = texts[batch_idx:batch_end]
            current_batch_num = (batch_idx // batch_size) + 1

            logger.info(
                f"バッチ {current_batch_num}/{total_batches} 処理中: "
                f"texts {batch_idx + 1}-{batch_end}"
            )

            # バッチ内の各テキストを個別に処理
            for i, text in enumerate(batch_texts):
                text_index = batch_idx + i + 1
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                    logger.debug(f"テキスト {text_index}/{len(texts)} 処理完了")

                except Exception as e:
                    logger.error(
                        f"テキスト {text_index}/{len(texts)} の埋め込み生成失敗: {e}"
                    )
                    # エラー時は空のリストを追加してスキップ
                    embeddings.append([])

                # レート制限対応: リクエスト間隔を設ける
                if text_index < len(texts):
                    time.sleep(self.batch_delay)

            logger.info(
                f"バッチ {current_batch_num}/{total_batches} 完了: "
                f"成功={sum(1 for e in embeddings[batch_idx:batch_end] if e)}/{len(batch_texts)}"
            )

        success_count = sum(1 for e in embeddings if e)
        logger.info(
            f"バッチ埋め込み生成完了: "
            f"成功={success_count}/{len(texts)} ({success_count / len(texts) * 100:.1f}%)"
        )

        return embeddings

    def _clean_text(self, text: str) -> str:
        """
        テキストをクリーニングします。

        - 連続する空白・改行を1つにまとめる
        - 前後の空白を削除
        - 空文字列の場合はエラー

        Args:
            text: クリーニングするテキスト

        Returns:
            クリーニング後のテキスト

        Raises:
            ValueError: テキストが空の場合
        """
        if not text:
            raise ValueError("テキストが空です")

        # 前後の空白を削除
        cleaned = text.strip()

        # 連続する空白を1つにまとめる
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 連続する改行を1つにまとめる
        cleaned = re.sub(r"\n+", "\n", cleaned)

        # クリーニング後に空になった場合はエラー
        if not cleaned:
            raise ValueError("クリーニング後のテキストが空です")

        return cleaned
