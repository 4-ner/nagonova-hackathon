"""
KKJ API連携サービス

官公需情報ポータルサイトからRFPデータを取得します。
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

# ロガー設定
logger = logging.getLogger(__name__)

# 都道府県コードマッピング（JIS X0401準拠）
PREFECTURE_NAMES = {
    "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県",
    "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
    "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
    "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
    "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
    "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
    "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
    "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
    "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
    "46": "鹿児島県", "47": "沖縄県",
}


class KKJAPIClient:
    """
    官公需情報ポータルサイト検索APIクライアント

    外部APIからRFP情報を取得し、パースして返します。
    """

    def __init__(self, api_url: str = "http://www.kkj.go.jp/api/") -> None:
        """
        KKJ APIクライアントを初期化します。

        Args:
            api_url: KKJ APIのエンドポイントURL
        """
        self.api_url = api_url
        self.timeout = 30.0  # タイムアウト: 30秒
        self.max_retries = 3  # 最大リトライ回数
        self.rate_limit_delay = 1.0  # レート制限: 1秒

    def fetch_rfps(
        self,
        prefecture_code: str,
        count: int = 100,
        query: str = "*",
        ng_keywords: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        指定した都道府県のRFP情報を取得します。

        Args:
            prefecture_code: 都道府県コード（JIS X0401準拠、01-47）
            count: 取得件数（デフォルト100、最大1000）
            query: 検索クエリ（デフォルト "*"で全件）
            ng_keywords: NGキーワードのリスト（除外したいキーワード）

        Returns:
            RFP情報のdictリスト

        Raises:
            httpx.HTTPError: HTTP通信エラー
            ValueError: XMLパースエラー
        """
        logger.info(
            f"KKJ API呼び出し開始: prefecture_code={prefecture_code}, "
            f"count={count}, query={query}"
        )

        # パラメータ検証
        if prefecture_code not in PREFECTURE_NAMES:
            raise ValueError(
                f"無効な都道府県コード: {prefecture_code}. "
                f"01-47の範囲で指定してください。"
            )

        if count > 1000:
            logger.warning(f"count={count}は最大値1000を超えています。1000に制限します。")
            count = 1000

        # APIリクエストパラメータ
        params = {
            "Query": query,
            "LG_Code": prefecture_code,
            "Count": str(count),
        }

        # リトライロジック
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"リクエスト試行 {attempt}/{self.max_retries}")

                # HTTPリクエスト実行
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(self.api_url, params=params)
                    response.raise_for_status()

                # XMLパース
                rfps = self._parse_xml_response(response.text)
                logger.info(f"RFP取得成功: {len(rfps)}件")

                # NGキーワードフィルタリング
                if ng_keywords:
                    rfps = self._filter_by_ng_keywords(rfps, ng_keywords)
                    logger.info(f"NGキーワードフィルタ後: {len(rfps)}件")

                # レート制限遵守
                time.sleep(self.rate_limit_delay)

                return rfps

            except httpx.HTTPError as e:
                logger.warning(
                    f"HTTPエラー発生 (試行 {attempt}/{self.max_retries}): {e}"
                )
                last_exception = e
                if attempt < self.max_retries:
                    # 指数バックオフでリトライ
                    wait_time = 2**attempt
                    logger.info(f"{wait_time}秒後にリトライします...")
                    time.sleep(wait_time)
            except ET.ParseError as e:
                logger.error(f"XMLパースエラー: {e}")
                raise ValueError(f"XMLのパースに失敗しました: {e}") from e

        # すべてのリトライ失敗
        error_msg = f"最大リトライ回数({self.max_retries})を超えました"
        logger.error(error_msg)
        raise last_exception or Exception(error_msg)

    def _parse_xml_response(self, xml_content: str) -> list[dict[str, Any]]:
        """
        XMLレスポンスをパースしてdictのリストに変換します。

        Args:
            xml_content: XML文字列

        Returns:
            RFP情報のdictリスト

        Raises:
            ET.ParseError: XMLパースエラー
            ValueError: エラー要素が含まれている場合
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML解析失敗: {e}")
            raise

        # エラーチェック
        error_elem = root.find("Error")
        if error_elem is not None:
            error_msg = error_elem.text or "不明なエラー"
            logger.error(f"API エラーレスポンス: {error_msg}")
            raise ValueError(f"KKJ APIエラー: {error_msg}")

        # 検索結果を抽出
        rfps: list[dict[str, Any]] = []
        search_results = root.find("SearchResults")

        if search_results is None:
            logger.warning("SearchResults要素が見つかりません")
            return rfps

        # ヒット件数をログ出力
        search_hits_elem = search_results.find("SearchHits")
        if search_hits_elem is not None and search_hits_elem.text:
            logger.info(f"検索ヒット件数: {search_hits_elem.text}")

        # 各検索結果をパース
        for search_result in search_results.findall("SearchResult"):
            rfp_data = self._parse_search_result(search_result)
            rfps.append(rfp_data)

        return rfps

    def _parse_search_result(self, search_result: ET.Element) -> dict[str, Any]:
        """
        SearchResult要素を1件パースします。

        Args:
            search_result: SearchResult XML要素

        Returns:
            RFP情報のdict
        """
        rfp: dict[str, Any] = {}

        # 必須フィールド
        rfp["project_name"] = self._get_text(search_result, "ProjectName", "")
        rfp["organization_name"] = self._get_text(
            search_result, "OrganizationName", ""
        )
        rfp["cft_issue_date"] = self._get_text(search_result, "CftIssueDate", "")
        rfp["external_document_uri"] = self._get_text(
            search_result, "ExternalDocumentURI", ""
        )

        # 都道府県情報
        lg_code = self._get_text(search_result, "LgCode", "")
        rfp["lg_code"] = lg_code
        rfp["prefecture_name"] = PREFECTURE_NAMES.get(lg_code, "")

        # オプションフィールド
        rfp["result_id"] = self._get_text(search_result, "ResultId", "")
        rfp["key"] = self._get_text(search_result, "Key", "")
        rfp["date"] = self._get_text(search_result, "Date", "")
        rfp["file_type"] = self._get_text(search_result, "FileType", "")
        rfp["file_size"] = self._get_text(search_result, "FileSize", "")
        rfp["city_code"] = self._get_text(search_result, "CityCode", "")
        rfp["city_name"] = self._get_text(search_result, "CityName", "")
        rfp["certification"] = self._get_text(search_result, "Certification", "")
        rfp["period_end_time"] = self._get_text(search_result, "PeriodEndTime", "")
        rfp["category"] = self._get_text(search_result, "Category", "")
        rfp["procedure_type"] = self._get_text(search_result, "ProcedureType", "")
        rfp["location"] = self._get_text(search_result, "Location", "")
        rfp["tender_submission_deadline"] = self._get_text(
            search_result, "TenderSubmissionDeadline", ""
        )
        rfp["opening_tenders_event"] = self._get_text(
            search_result, "OpeningTendersEvent", ""
        )
        rfp["item_code"] = self._get_text(search_result, "ItemCode", "")
        rfp["project_description"] = self._get_text(
            search_result, "ProjectDescription", ""
        )

        # 添付ファイル
        attachments = []
        attachments_elem = search_result.find("Attachments")
        if attachments_elem is not None:
            for attachment in attachments_elem.findall("Attachment"):
                attachments.append(
                    {
                        "name": self._get_text(attachment, "Name", ""),
                        "uri": self._get_text(attachment, "Uri", ""),
                    }
                )
        rfp["attachments"] = attachments

        return rfp

    def _get_text(
        self, element: ET.Element, tag: str, default: str = ""
    ) -> str:
        """
        XML要素からテキストを安全に取得します。

        Args:
            element: 親XML要素
            tag: 取得したい子要素のタグ名
            default: 要素が存在しない場合のデフォルト値

        Returns:
            要素のテキスト、または存在しない場合はdefault
        """
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    def _filter_by_ng_keywords(
        self, rfps: list[dict[str, Any]], ng_keywords: list[str]
    ) -> list[dict[str, Any]]:
        """
        NGキーワードを含むRFPを除外します。

        件名（project_name）または公告文（project_description）に
        NGキーワードが含まれている場合、そのRFPを除外します。

        Args:
            rfps: RFP情報のリスト
            ng_keywords: NGキーワードのリスト

        Returns:
            フィルタリング後のRFP情報のリスト
        """
        if not ng_keywords:
            return rfps

        logger.info(f"NGキーワードフィルタリング開始: {ng_keywords}")

        filtered_rfps = []
        for rfp in rfps:
            project_name = rfp.get("project_name", "").lower()
            project_description = rfp.get("project_description", "").lower()

            # NGキーワードチェック
            has_ng_keyword = False
            for ng_keyword in ng_keywords:
                ng_lower = ng_keyword.lower()
                if ng_lower in project_name or ng_lower in project_description:
                    logger.debug(
                        f"NGキーワード '{ng_keyword}' が検出されました: "
                        f"{rfp.get('project_name', '')}"
                    )
                    has_ng_keyword = True
                    break

            if not has_ng_keyword:
                filtered_rfps.append(rfp)

        logger.info(
            f"フィルタリング結果: {len(rfps)}件 → {len(filtered_rfps)}件"
        )
        return filtered_rfps
