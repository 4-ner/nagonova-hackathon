/**
 * RFP案件の型定義
 */

/**
 * RFP基本情報
 */
export interface RFP {
  /** RFP ID */
  id: string;
  /** 外部システムのID */
  external_id: string;
  /** 案件タイトル */
  title: string;
  /** 発行組織名 */
  issuing_org: string;
  /** 案件詳細 */
  description: string;
  /** 予算（円） */
  budget?: number;
  /** 都道府県コード */
  region: string;
  /** 応募締切日 */
  deadline: string;
  /** RFP URL */
  url?: string;
  /** 外部ドキュメントURL配列 */
  external_doc_urls: string[];
  /** 埋め込みベクトルが存在するか */
  has_embedding: boolean;
  /** 作成日時 */
  created_at: string;
  /** 更新日時 */
  updated_at: string;
  /** 取得日時 */
  fetched_at: string;
  /** 案件カテゴリ */
  category?: string;
  /** 入札手続きの種類 */
  procedure_type?: string;
  /** 仕様書発行日（ISO8601形式） */
  cft_issue_date?: string;
  /** 入札締切日時（ISO8601形式） */
  tender_deadline?: string;
  /** 開札日時（ISO8601形式） */
  opening_event_date?: string;
  /** 品目分類コード */
  item_code?: string;
  /** 地方自治体コード */
  lg_code?: string;
  /** 市区町村コード */
  city_code?: string;
  /** 参加資格情報 */
  certification?: string;
}

/**
 * RFP一覧レスポンス
 */
export interface RFPListResponse {
  /** 総件数 */
  total: number;
  /** RFPアイテム配列 */
  items: RFP[];
  /** 現在のページ番号 */
  page: number;
  /** ページサイズ */
  page_size: number;
}

/**
 * マッチング要因の内訳
 */
export interface MatchingFactors {
  /** スキルマッチ度（0.0-1.0） */
  skill: number;
  /** 地域係数（0.0-1.0） */
  region: number;
  /** 予算マッチ度（0.0-1.0） */
  budget: number;
  /** 納期マッチ度（0.0-1.0） */
  deadline: number;
  /** 必須要件を満たすか */
  must: boolean;
}

/**
 * マッチングスコア付きRFP
 */
export interface RFPWithMatching extends RFP {
  /** マッチングスコア（0-100） */
  match_score?: number;
  /** 必須要件を満たすか */
  must_requirements_ok?: boolean;
  /** 予算が適合するか */
  budget_match_ok?: boolean;
  /** 地域が適合するか */
  region_match_ok?: boolean;
  /** マッチング要因の内訳 */
  match_factors?: MatchingFactors;
  /** マッチング理由のサマリー */
  summary_points?: string[];
  /** マッチングスコア計算日時 */
  match_calculated_at?: string;
}

/**
 * マッチングスコア付きRFP一覧レスポンス
 */
export interface RFPWithMatchingListResponse {
  /** 総件数 */
  total: number;
  /** RFPアイテム配列 */
  items: RFPWithMatching[];
  /** 現在のページ番号 */
  page: number;
  /** ページサイズ */
  page_size: number;
}

/**
 * ブックマーク型
 */
export interface Bookmark {
  /** ブックマークID */
  id: string;
  /** ユーザーID */
  user_id: string;
  /** RFP ID */
  rfp_id: string;
  /** 作成日時 */
  created_at: string;
  /** RFP情報（optional） */
  rfp?: RFP;
}

/**
 * ブックマーク一覧レスポンス
 */
export interface BookmarkListResponse {
  /** 総件数 */
  total: number;
  /** ブックマークアイテム配列 */
  items: Bookmark[];
  /** 現在のページ番号 */
  page: number;
  /** ページサイズ */
  page_size: number;
}
