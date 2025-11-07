/**
 * ドキュメント管理関連の型定義
 */

/**
 * ドキュメント種別
 */
export type DocumentKind = 'url' | 'pdf' | 'word' | 'ppt' | 'image' | 'text';

/**
 * ドキュメント基本型
 */
export interface Document {
  id: string;
  company_id: string;
  title: string;
  description?: string;
  kind: DocumentKind;
  url?: string;
  storage_path?: string;
  file_size?: number;
  mime_type?: string;
  created_at: string;
  updated_at: string;
}

/**
 * ドキュメント一覧レスポンス
 */
export interface DocumentListResponse {
  total: number;
  items: Document[];
  page: number;
  page_size: number;
}

/**
 * URL型ドキュメント作成リクエスト
 */
export interface DocumentCreateUrlRequest {
  title: string;
  description?: string;
  kind: DocumentKind;
  url: string;
}

/**
 * ファイル型ドキュメント作成リクエスト
 */
export interface DocumentCreateFileRequest {
  title: string;
  description?: string;
  kind: DocumentKind;
  storage_path: string;
  file_size: number;
  mime_type: string;
}

/**
 * ドキュメント更新リクエスト
 */
export interface DocumentUpdateRequest {
  title?: string;
  description?: string;
}

/**
 * アップロードURL生成レスポンス
 */
export interface UploadUrlResponse {
  upload_url: string;
  storage_path: string;
  expires_in: number;
}

/**
 * ダウンロードURL生成レスポンス
 */
export interface DownloadUrlResponse {
  download_url: string;
  expires_in: number;
}

/**
 * ドキュメント一覧取得パラメータ
 */
export interface DocumentListParams {
  page?: number;
  page_size?: number;
}
