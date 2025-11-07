'use client';

import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';
import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api';
import type {
  Document,
  DocumentListResponse,
  DocumentListParams,
  DocumentCreateUrlRequest,
  DocumentCreateFileRequest,
  DocumentUpdateRequest,
  UploadUrlResponse,
  DownloadUrlResponse,
} from '@/types/document';

/**
 * URLパラメータをクエリ文字列に変換
 */
function buildQueryString(params: DocumentListParams): string {
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
 * ドキュメント一覧を取得するカスタムフック
 *
 * @param params クエリパラメータ
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function DocumentList() {
 *   const { data, error, isLoading } = useDocuments({ page: 1, page_size: 20 });
 *
 *   if (isLoading) return <div>読み込み中...</div>;
 *   if (error) return <div>エラー: {error.message}</div>;
 *
 *   return (
 *     <ul>
 *       {data.items.map(doc => (
 *         <li key={doc.id}>{doc.title}</li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 */
export function useDocuments(params: DocumentListParams = {}) {
  const queryString = buildQueryString(params);
  const url = `/api/documents${queryString}`;

  return useSWR<DocumentListResponse>(url, apiGet, {
    revalidateOnFocus: false,
    dedupingInterval: 60000, // 60秒間は重複リクエストを防ぐ
  });
}

/**
 * ドキュメント詳細を取得するカスタムフック
 *
 * @param documentId ドキュメントID
 * @returns SWRレスポンス
 *
 * @example
 * ```tsx
 * function DocumentDetail({ documentId }: { documentId: string }) {
 *   const { data, error, isLoading } = useDocument(documentId);
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
export function useDocument(documentId: string | null) {
  const url = documentId ? `/api/documents/${documentId}` : null;

  return useSWR<Document>(url, apiGet, {
    revalidateOnFocus: false,
  });
}

/**
 * URL型ドキュメント作成のカスタムフック
 *
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function CreateUrlDocumentForm() {
 *   const { trigger, isMutating } = useCreateUrlDocument();
 *
 *   const handleSubmit = async (data: DocumentCreateUrlRequest) => {
 *     try {
 *       await trigger(data);
 *       alert('ドキュメントを作成しました');
 *     } catch (error) {
 *       alert('作成に失敗しました');
 *     }
 *   };
 *
 *   return <form onSubmit={handleSubmit}>...</form>;
 * }
 * ```
 */
export function useCreateUrlDocument() {
  return useSWRMutation(
    '/api/documents/url',
    async (url: string, { arg }: { arg: DocumentCreateUrlRequest }) => {
      return apiPost<Document>(url, arg);
    },
    {
      // ドキュメント一覧を再取得
      onSuccess: () => {
        // mutateを使ってキャッシュを更新することもできるが、
        // 簡単のためrevalidateOnMountで次回マウント時に再取得する
      },
    }
  );
}

/**
 * アップロードURL生成のカスタムフック
 *
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function FileUploadForm() {
 *   const { trigger } = useGenerateUploadUrl();
 *
 *   const handleFileSelect = async (file: File) => {
 *     const { upload_url, storage_path } = await trigger({
 *       filename: file.name,
 *       content_type: file.type,
 *     });
 *
 *     // upload_urlにファイルをアップロード
 *     await fetch(upload_url, {
 *       method: 'PUT',
 *       body: file,
 *       headers: { 'Content-Type': file.type },
 *     });
 *   };
 * }
 * ```
 */
export function useGenerateUploadUrl() {
  return useSWRMutation(
    '/api/documents/upload-url',
    async (
      url: string,
      { arg }: { arg: { filename: string; content_type: string } }
    ) => {
      return apiPost<UploadUrlResponse>(url, arg);
    }
  );
}

/**
 * ファイル型ドキュメント作成のカスタムフック
 *
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function CreateFileDocumentForm() {
 *   const { trigger } = useCreateFileDocument();
 *
 *   const handleSubmit = async (data: DocumentCreateFileRequest) => {
 *     try {
 *       await trigger(data);
 *       alert('ドキュメントを作成しました');
 *     } catch (error) {
 *       alert('作成に失敗しました');
 *     }
 *   };
 * }
 * ```
 */
export function useCreateFileDocument() {
  return useSWRMutation(
    '/api/documents/file',
    async (url: string, { arg }: { arg: DocumentCreateFileRequest }) => {
      return apiPost<Document>(url, arg);
    }
  );
}

/**
 * ダウンロードURL生成のカスタムフック
 *
 * @param documentId ドキュメントID
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function DownloadButton({ documentId }: { documentId: string }) {
 *   const { trigger, isMutating } = useGenerateDownloadUrl(documentId);
 *
 *   const handleDownload = async () => {
 *     const { download_url } = await trigger();
 *     window.open(download_url, '_blank');
 *   };
 *
 *   return (
 *     <button onClick={handleDownload} disabled={isMutating}>
 *       ダウンロード
 *     </button>
 *   );
 * }
 * ```
 */
export function useGenerateDownloadUrl(documentId: string) {
  return useSWRMutation(`/api/documents/${documentId}/download-url`, async (url: string) => {
    return apiGet<DownloadUrlResponse>(url);
  });
}

/**
 * ドキュメント更新のカスタムフック
 *
 * @param documentId ドキュメントID
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function EditDocumentForm({ documentId }: { documentId: string }) {
 *   const { trigger, isMutating } = useUpdateDocument(documentId);
 *
 *   const handleSubmit = async (data: DocumentUpdateRequest) => {
 *     try {
 *       await trigger(data);
 *       alert('更新しました');
 *     } catch (error) {
 *       alert('更新に失敗しました');
 *     }
 *   };
 * }
 * ```
 */
export function useUpdateDocument(documentId: string) {
  return useSWRMutation(
    `/api/documents/${documentId}`,
    async (url: string, { arg }: { arg: DocumentUpdateRequest }) => {
      return apiPut<Document>(url, arg);
    }
  );
}

/**
 * ドキュメント削除のカスタムフック
 *
 * @param documentId ドキュメントID
 * @returns SWRMutationレスポンス
 *
 * @example
 * ```tsx
 * function DeleteDocumentButton({ documentId }: { documentId: string }) {
 *   const { trigger, isMutating } = useDeleteDocument(documentId);
 *
 *   const handleDelete = async () => {
 *     if (!confirm('本当に削除しますか?')) return;
 *
 *     try {
 *       await trigger();
 *       alert('削除しました');
 *     } catch (error) {
 *       alert('削除に失敗しました');
 *     }
 *   };
 *
 *   return (
 *     <button onClick={handleDelete} disabled={isMutating}>
 *       削除
 *     </button>
 *   );
 * }
 * ```
 */
export function useDeleteDocument(documentId: string) {
  return useSWRMutation(`/api/documents/${documentId}`, async (url: string) => {
    return apiDelete<void>(url);
  });
}
