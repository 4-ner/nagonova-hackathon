'use client';

import { FileText } from 'lucide-react';
import { DocumentCard } from './DocumentCard';
import { useDocuments } from '@/hooks/useDocuments';
import type { Document } from '@/types/document';

interface DocumentListProps {
  /** ページ番号 */
  page?: number;
  /** ページサイズ */
  pageSize?: number;
  /** 編集ボタンのコールバック（オプション） */
  onEdit?: (document: Document) => void;
}

/**
 * ドキュメント一覧コンポーネント
 *
 * ドキュメント一覧を表示します。
 *
 * @example
 * ```tsx
 * <DocumentList page={1} pageSize={20} onEdit={handleEdit} />
 * ```
 */
export function DocumentList({ page = 1, pageSize = 20, onEdit }: DocumentListProps) {
  const { data, error, isLoading } = useDocuments({
    page,
    page_size: pageSize,
  });

  // ローディング状態
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-2">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
          <p className="text-sm text-muted-foreground">読み込み中...</p>
        </div>
      </div>
    );
  }

  // エラー状態
  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-2">
          <p className="text-destructive font-semibold">エラーが発生しました</p>
          <p className="text-sm text-muted-foreground">
            {error.message || 'ドキュメントの取得に失敗しました'}
          </p>
        </div>
      </div>
    );
  }

  // データが存在しない場合
  if (!data || data.items.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-4">
          <FileText className="h-16 w-16 text-muted-foreground mx-auto" />
          <div className="space-y-2">
            <p className="text-lg font-semibold">ドキュメントがありません</p>
            <p className="text-sm text-muted-foreground">
              URLを追加するか、ファイルをアップロードしてください
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ドキュメント一覧表示
  return (
    <div className="space-y-4">
      {/* 件数表示 */}
      <div className="text-sm text-muted-foreground">
        全 {data.total} 件中 {data.items.length} 件を表示
      </div>

      {/* カード一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.items.map((document) => (
          <DocumentCard key={document.id} document={document} onEdit={onEdit} />
        ))}
      </div>
    </div>
  );
}
