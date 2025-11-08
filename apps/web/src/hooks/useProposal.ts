'use client';

import useSWR from 'swr';
import { apiGetText } from '@/lib/api';

/**
 * 提案ドラフトを取得するカスタムフック
 *
 * @param rfpId RFP ID
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function ProposalDraft({ rfpId }: { rfpId: string }) {
 *   const { data, error, isLoading } = useProposalDraft(rfpId);
 *
 *   if (isLoading) return <div>生成中...</div>;
 *   if (error) return <div>エラー: {error.message}</div>;
 *
 *   return <div>{data}</div>;
 * }
 * ```
 */
export function useProposalDraft(rfpId: string | null) {
  const url = rfpId ? `/api/rfps/${rfpId}/proposal/draft` : null;

  return useSWR<string>(url, apiGetText, {
    revalidateOnFocus: false,
  });
}
