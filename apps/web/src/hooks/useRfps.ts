'use client';

import useSWR from 'swr';
import { apiGet } from '@/lib/api';
import type {
  RFPListResponse,
  RFPWithMatching,
  RFPWithMatchingListResponse,
} from '@/types/rfp';

/**
 * RFP一覧取得のクエリパラメータ
 */
export interface RFPListParams {
  /** ページ番号 */
  page?: number;
  /** ページサイズ */
  page_size?: number;
  /** 都道府県コードフィルター */
  region?: string;
  /** タイトル・説明文での検索 */
  query?: string;
}

/**
 * マッチングスコア付きRFP一覧取得のクエリパラメータ
 */
export interface RFPWithMatchingListParams {
  /** ページ番号 */
  page?: number;
  /** ページサイズ */
  page_size?: number;
  /** 最小マッチングスコア */
  min_score?: number;
  /** 必須要件を満たす案件のみ表示 */
  must_requirements_only?: boolean;
  /** 締切日フィルター（日数） */
  deadline_days?: number;
  /** 都道府県コード */
  region?: string;
  /** 最小予算（円） */
  budget_min?: number;
  /** 最大予算（円） */
  budget_max?: number;
}

/**
 * URLパラメータをクエリ文字列に変換
 */
function buildQueryString(params: RFPListParams | RFPWithMatchingListParams): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * RFP一覧を取得するカスタムフック
 *
 * @param params クエリパラメータ
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function RFPList() {
 *   const { data, error, isLoading } = useRfps({ page: 1, page_size: 20 });
 *
 *   if (isLoading) return <div>読み込み中...</div>;
 *   if (error) return <div>エラー: {error.message}</div>;
 *
 *   return (
 *     <ul>
 *       {data.items.map(rfp => (
 *         <li key={rfp.id}>{rfp.title}</li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 */
export function useRfps(params: RFPListParams = {}) {
  const queryString = buildQueryString(params);
  const url = `/api/rfps${queryString}`;

  return useSWR<RFPListResponse>(url, apiGet, {
    revalidateOnFocus: false,
    dedupingInterval: 60000, // 60秒間は重複リクエストを防ぐ
  });
}

/**
 * マッチングスコア付きRFP一覧を取得するカスタムフック
 *
 * @param params クエリパラメータ
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function MatchingRFPList() {
 *   const { data, error, isLoading } = useRfpsWithMatching({
 *     page: 1,
 *     page_size: 20,
 *     min_score: 50,
 *     must_requirements_only: true
 *   });
 *
 *   if (isLoading) return <div>読み込み中...</div>;
 *   if (error) return <div>エラー: {error.message}</div>;
 *
 *   return (
 *     <ul>
 *       {data.items.map(rfp => (
 *         <li key={rfp.id}>
 *           {rfp.title} - スコア: {rfp.match_score}
 *         </li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 */
export function useRfpsWithMatching(params: RFPWithMatchingListParams = {}) {
  const queryString = buildQueryString(params);
  const url = `/api/rfps/with-matching${queryString}`;

  return useSWR<RFPWithMatchingListResponse>(url, apiGet, {
    revalidateOnFocus: false,
    dedupingInterval: 60000, // 60秒間は重複リクエストを防ぐ
  });
}

/**
 * RFP詳細を取得するカスタムフック
 *
 * @param rfpId RFP ID
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function RFPDetail({ rfpId }: { rfpId: string }) {
 *   const { data, error, isLoading } = useRfp(rfpId);
 *
 *   if (isLoading) return <div>読み込み中...</div>;
 *   if (error) return <div>エラー: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       <h1>{data.title}</h1>
 *       <p>{data.description}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useRfp(rfpId: string | null) {
  const url = rfpId ? `/api/rfps/${rfpId}` : null;

  return useSWR<RFPWithMatching>(url, apiGet, {
    revalidateOnFocus: false,
  });
}
