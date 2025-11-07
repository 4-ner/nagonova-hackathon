'use client';

import { useState } from 'react';
import { FileText, Link as LinkIcon, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DocumentList } from '@/components/documents/DocumentList';
import { DocumentUrlDialog } from '@/components/documents/DocumentUrlDialog';
import { DocumentUploadDialog } from '@/components/documents/DocumentUploadDialog';
import type { Document } from '@/types/document';

/**
 * ドキュメント管理ページ
 *
 * 会社のドキュメント一覧を表示し、URLの追加やファイルのアップロードを行います。
 */
export default function DocumentsPage() {
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);

  // 編集ハンドラー（現在は未実装）
  const handleEdit = (document: Document) => {
    setEditingDocument(document);
    // TODO: 編集ダイアログの実装
    console.log('編集:', document);
  };

  return (
    <div className="container py-8 space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-8 w-8" />
            ドキュメント管理
          </h1>
          <p className="text-muted-foreground">
            会社のドキュメント、技術資料、実績資料などを管理します
          </p>
        </div>

        {/* アクションボタン */}
        <div className="flex items-center gap-2">
          <DocumentUrlDialog
            trigger={
              <Button variant="outline">
                <LinkIcon className="h-4 w-4 mr-2" />
                URLを追加
              </Button>
            }
          />
          <DocumentUploadDialog
            trigger={
              <Button>
                <Upload className="h-4 w-4 mr-2" />
                ファイルをアップロード
              </Button>
            }
          />
        </div>
      </div>

      {/* ドキュメント一覧 */}
      <DocumentList onEdit={handleEdit} />
    </div>
  );
}
