import { createClient } from '@/lib/supabase/client';

/**
 * APIエラークラス
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * 認証トークン付きfetchを実行
 *
 * @param url APIエンドポイント
 * @param options fetchオプション
 * @returns レスポンスデータ
 * @throws {ApiError} APIエラー時
 */
export async function fetchWithAuth<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const supabase = createClient();

  // 現在のセッションを取得
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new ApiError('認証されていません', 401);
  }

  // APIベースURL
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // デフォルトヘッダーとマージ
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${session.access_token}`,
    ...options.headers,
  };

  try {
    const response = await fetch(`${baseUrl}${url}`, {
      ...options,
      headers,
    });

    // エラーハンドリング
    if (!response.ok) {
      let errorMessage = `APIエラー: ${response.status}`;
      let errorData: unknown = undefined;

      try {
        errorData = await response.json();
        if (errorData && typeof errorData === 'object' && 'detail' in errorData) {
          errorMessage = String(errorData.detail);
        }
      } catch {
        // JSONパースエラーは無視
        errorMessage = await response.text();
      }

      throw new ApiError(errorMessage, response.status, errorData);
    }

    // 204 No Contentの場合は空オブジェクトを返す
    if (response.status === 204) {
      return {} as T;
    }

    // レスポンスをJSONとしてパース
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // ネットワークエラーなど
    throw new ApiError(
      error instanceof Error ? error.message : 'ネットワークエラー',
      0
    );
  }
}

/**
 * GET リクエスト
 */
export async function apiGet<T>(url: string): Promise<T> {
  return fetchWithAuth<T>(url, { method: 'GET' });
}

/**
 * POST リクエスト
 */
export async function apiPost<T>(url: string, data: unknown): Promise<T> {
  return fetchWithAuth<T>(url, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * PUT リクエスト
 */
export async function apiPut<T>(url: string, data: unknown): Promise<T> {
  return fetchWithAuth<T>(url, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * DELETE リクエスト
 */
export async function apiDelete<T>(url: string): Promise<T> {
  return fetchWithAuth<T>(url, { method: 'DELETE' });
}
