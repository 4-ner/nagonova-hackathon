/**
 * 会社プロフィールの型定義
 */
export interface Company {
  /** 会社ID */
  id: string;
  /** ユーザーID */
  user_id: string;
  /** 会社名 */
  name: string;
  /** 会社説明 */
  description?: string;
  /** 対応可能地域 */
  regions: string[];
  /** 希望案件規模 - 最小金額 */
  budget_min?: number;
  /** 希望案件規模 - 最大金額 */
  budget_max?: number;
  /** 保有スキル */
  skills: string[];
  /** NGキーワード */
  ng_keywords: string[];
  /** 作成日時 */
  created_at: string;
  /** 更新日時 */
  updated_at: string;
}

/**
 * 会社プロフィール作成リクエスト
 */
export interface CreateCompanyRequest {
  /** 会社名 */
  name: string;
  /** 会社説明 */
  description?: string;
  /** 対応可能地域 */
  regions: string[];
  /** 希望案件規模 - 最小金額 */
  budget_min?: number;
  /** 希望案件規模 - 最大金額 */
  budget_max?: number;
  /** 保有スキル */
  skills: string[];
  /** NGキーワード */
  ng_keywords: string[];
}

/**
 * 会社プロフィール更新リクエスト
 */
export interface UpdateCompanyRequest extends CreateCompanyRequest {}
