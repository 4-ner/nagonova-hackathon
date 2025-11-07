'use client';

import { FileText, Download, ExternalLink, Trash2, Edit, File } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useGenerateDownloadUrl, useDeleteDocument } from '@/hooks/useDocuments';
import type { Document, DocumentKind } from '@/types/document';
import { mutate } from 'swr';

interface DocumentCardProps {
  /** ドキュメント情報 */
  document: Document;
  /** 編集ボタンのコールバック（オプション） */
  onEdit?: (document: Document) => void;
}

/**
 * ドキュメント種別のラベルを取得
 */
function getKindLabel(kind: DocumentKind): string {
  const labels: Record<DocumentKind, string> = {
    url: 'URL',
    pdf: 'PDF',
    word: 'Word',
    ppt: 'PowerPoint',
    image: '画像',
    text: 'テキスト',
  };
  return labels[kind] || kind;
}

/**
 * ドキュメント種別のバリアントを取得
 */
function getKindVariant(kind: DocumentKind): 'default' | 'secondary' | 'outline' {
  if (kind === 'url') return 'outline';
  return 'secondary';
}

/**
 * ファイルサイズをフォーマット
 */
function formatFileSize(bytes: number | undefined): string {
  if (!bytes) return '-';

  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * 日付をフォーマット
 */
function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return '-';
  }
}

/**
 * ドキュメントカードコンポーネント
 *
 * ドキュメントの概要をカード形式で表示します。
 *
 * @example
 * ```tsx
 * <DocumentCard document={doc} onEdit={handleEdit} />
 * ```
 */
export function DocumentCard({ document, onEdit }: DocumentCardProps) {
  const { trigger: generateDownloadUrl, isMutating: isDownloading } =
    useGenerateDownloadUrl(document.id);
  const { trigger: deleteDocument, isMutating: isDeleting } = useDeleteDocument(
    document.id
  );

  // ダウンロード処理
  const handleDownload = async () => {
    try {
      const { download_url } = await generateDownloadUrl();
      window.open(download_url, '_blank');
    } catch (error) {
      console.error('ダウンロードエラー:', error);
      alert('ダウンロードに失敗しました');
    }
  };

  // 外部リンクを開く
  const handleOpenUrl = () => {
    if (document.url) {
      window.open(document.url, '_blank', 'noopener,noreferrer');
    }
  };

  // 削除処理
  const handleDelete = async () => {
    if (!confirm('本当にこのドキュメントを削除しますか？')) {
      return;
    }

    try {
      await deleteDocument();
      // 一覧を再取得
      mutate('/api/documents');
      alert('ドキュメントを削除しました');
    } catch (error) {
      console.error('削除エラー:', error);
      alert('削除に失敗しました');
    }
  };

  const isUrlType = document.kind === 'url';
  const isFileType = !isUrlType && document.storage_path;

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">{document.title}</CardTitle>
            </div>
            {document.description && (
              <CardDescription className="text-sm">
                {document.description}
              </CardDescription>
            )}
          </div>

          {/* 種別バッジ */}
          <Badge variant={getKindVariant(document.kind)}>
            {getKindLabel(document.kind)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* メタ情報 */}
        <div className="grid grid-cols-2 gap-3 text-sm text-muted-foreground">
          {/* ファイルサイズ */}
          <div className="flex items-center gap-2">
            <File className="h-4 w-4 shrink-0" />
            <span>{formatFileSize(document.size_bytes)}</span>
          </div>

          {/* 作成日時 */}
          <div className="text-right">
            <span>{formatDate(document.created_at)}</span>
          </div>
        </div>

        {/* アクションボタン */}
        <div className="flex items-center gap-2">
          {/* ダウンロード（ファイル型の場合） */}
          {isFileType && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              disabled={isDownloading}
              className="flex items-center gap-1"
            >
              <Download className="h-4 w-4" />
              {isDownloading ? 'ダウンロード中...' : 'ダウンロード'}
            </Button>
          )}

          {/* 外部リンク（URL型の場合） */}
          {isUrlType && document.url && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenUrl}
              className="flex items-center gap-1"
            >
              <ExternalLink className="h-4 w-4" />
              リンクを開く
            </Button>
          )}

          {/* 編集ボタン */}
          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(document)}
              className="flex items-center gap-1"
            >
              <Edit className="h-4 w-4" />
              編集
            </Button>
          )}

          {/* 削除ボタン */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex items-center gap-1 text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            {isDeleting ? '削除中...' : '削除'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
