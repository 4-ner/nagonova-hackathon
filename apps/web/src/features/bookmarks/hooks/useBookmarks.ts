'use client';

import useSWR, { mutate } from 'swr';
import useSWRMutation from 'swr/mutation';
import { apiGet, apiPost, apiDelete } from '@/lib/api';
import type { Bookmark, BookmarkListResponse } from '@/types/rfp';

/**
 * ブックマーク一覧取得のクエリパラメータ
 */
export interface BookmarkListParams {
  /** ページ番号 */
  page?: number;
  /** ページサイズ */
  page_size?: number;
}

/**
 * URLパラメータをクエリ文字列に変換
 */
function buildQueryString(params: BookmarkListParams): string {
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
 * ブックマーク一覧を取得するカスタムフック
 *
 * @param params クエリパラメータ
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function BookmarkList() {
 *   const { data, error, isLoading } = useBookmarks({ page: 1, page_size: 20 });
 *
 *   if (isLoading) return <div>読み込み中...</div>;
 *   if (error) return <div>エラー: {error.message}</div>;
 *
 *   return (
 *     <ul>
 *       {data.items.map(bookmark => (
 *         <li key={bookmark.id}>{bookmark.rfp?.title}</li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 */
export function useBookmarks(params: BookmarkListParams = {}) {
  const queryString = buildQueryString(params);
  const url = `/api/bookmarks${queryString}`;

  return useSWR<BookmarkListResponse>(url, apiGet, {
    revalidateOnFocus: false,
    dedupingInterval: 60000, // 60秒間は重複リクエストを防ぐ
  });
}

/**
 * ブックマーク追加のカスタムフック
 *
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function AddBookmarkButton({ rfpId }: { rfpId: string }) {
 *   const { trigger, isMutating } = useAddBookmark();
 *
 *   const handleAdd = async () => {
 *     try {
 *       await trigger({ rfp_id: rfpId });
 *       alert('ブックマークに追加しました');
 *     } catch (error) {
 *       alert('追加に失敗しました');
 *     }
 *   };
 *
 *   return (
 *     <button onClick={handleAdd} disabled={isMutating}>
 *       ブックマークに追加
 *     </button>
 *   );
 * }
 * ```
 */
export function useAddBookmark() {
  return useSWRMutation(
    '/api/bookmarks',
    async (url: string, { arg }: { arg: { rfp_id: string } }) => {
      return apiPost<Bookmark>(url, arg);
    },
    {
      // ブックマーク一覧を再取得
      onSuccess: () => {
        // ブックマーク一覧のキャッシュを無効化して再取得
        mutate((key) => typeof key === 'string' && key.startsWith('/api/bookmarks'));
      },
    }
  );
}

/**
 * ブックマーク削除のカスタムフック
 *
 * @param rfpId RFP ID
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function RemoveBookmarkButton({ rfpId }: { rfpId: string }) {
 *   const { trigger, isMutating } = useRemoveBookmark(rfpId);
 *
 *   const handleRemove = async () => {
 *     try {
 *       await trigger();
 *       alert('ブックマークから削除しました');
 *     } catch (error) {
 *       alert('削除に失敗しました');
 *     }
 *   };
 *
 *   return (
 *     <button onClick={handleRemove} disabled={isMutating}>
 *       ブックマークから削除
 *     </button>
 *   );
 * }
 * ```
 */
export function useRemoveBookmark(rfpId: string) {
  return useSWRMutation(`/api/bookmarks/rfp/${rfpId}`, async (url: string) => {
    return apiDelete<void>(url);
  }, {
    // ブックマーク一覧を再取得
    onSuccess: () => {
      // ブックマーク一覧のキャッシュを無効化して再取得
      mutate((key) => typeof key === 'string' && key.startsWith('/api/bookmarks'));
    },
  });
}

/**
 * 特定のRFPがブックマーク済みかチェックするカスタムフック
 *
 * @param rfpId RFP ID
 * @returns ブックマーク済みかどうか
 *
 * @example
 * ```tsx
 * function BookmarkStatus({ rfpId }: { rfpId: string }) {
 *   const { isBookmarked, isLoading } = useIsBookmarked(rfpId);
 *
 *   if (isLoading) return <span>確認中...</span>;
 *   return <span>{isBookmarked ? 'ブックマーク済み' : '未ブックマーク'}</span>;
 * }
 * ```
 */
export function useIsBookmarked(rfpId: string | null) {
  const url = rfpId ? `/api/bookmarks/check/${rfpId}` : null;

  const { data, isLoading } = useSWR<{ is_bookmarked: boolean; bookmark_id: string | null }>(
    url,
    apiGet,
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000, // 60秒間は重複リクエストを防ぐ
    }
  );

  if (!rfpId) {
    return { isBookmarked: false, isLoading: false };
  }

  const isBookmarked = data?.is_bookmarked ?? false;

  return { isBookmarked, isLoading };
}
