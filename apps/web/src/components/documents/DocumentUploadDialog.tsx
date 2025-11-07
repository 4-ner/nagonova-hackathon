'use client';

import { useState, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Upload, File as FileIcon } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  useGenerateUploadUrl,
  useCreateFileDocument,
} from '@/hooks/useDocuments';
import type { DocumentKind } from '@/types/document';
import { mutate } from 'swr';

/**
 * ドキュメント種別の選択肢（ファイル型用）
 */
const FILE_DOCUMENT_KINDS: { value: DocumentKind; label: string }[] = [
  { value: 'pdf', label: 'PDF' },
  { value: 'word', label: 'Word' },
  { value: 'ppt', label: 'PowerPoint' },
  { value: 'image', label: '画像' },
  { value: 'text', label: 'テキスト' },
];

/**
 * バリデーションスキーマ
 */
const fileDocumentSchema = z.object({
  title: z
    .string()
    .min(1, 'タイトルは必須です')
    .max(200, 'タイトルは200文字以内で入力してください'),
  description: z.string().max(1000, '説明は1000文字以内で入力してください').optional(),
  kind: z.enum(['pdf', 'word', 'ppt', 'image', 'text'], {
    message: '種別を選択してください',
  }),
});

type FileDocumentFormData = z.infer<typeof fileDocumentSchema>;

interface DocumentUploadDialogProps {
  /** ダイアログのトリガーボタン */
  trigger?: React.ReactNode;
}

/**
 * ファイルアップロードダイアログ
 *
 * ファイルをアップロードしてドキュメントを作成するダイアログコンポーネント
 *
 * @example
 * ```tsx
 * <DocumentUploadDialog trigger={<Button>ファイルをアップロード</Button>} />
 * ```
 */
export function DocumentUploadDialog({ trigger }: DocumentUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { trigger: generateUploadUrl } = useGenerateUploadUrl();
  const { trigger: createFileDocument } = useCreateFileDocument();

  const form = useForm<FileDocumentFormData>({
    resolver: zodResolver(fileDocumentSchema),
    defaultValues: {
      title: '',
      description: '',
      kind: 'pdf',
    },
  });

  // ファイル選択
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // タイトルが空の場合、ファイル名から拡張子を除いた名前をセット
      if (!form.getValues('title')) {
        const titleWithoutExt = file.name.replace(/\.[^/.]+$/, '');
        form.setValue('title', titleWithoutExt);
      }
    }
  };

  // ファイル選択をクリア
  const handleClearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // フォーム送信
  const onSubmit = async (data: FileDocumentFormData) => {
    if (!selectedFile) {
      alert('ファイルを選択してください');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // 1. アップロードURL取得
      setUploadProgress(10);
      const { upload_url, storage_path } = await generateUploadUrl({
        filename: selectedFile.name,
        file_size: selectedFile.size,
      });

      // 2. Storageへアップロード
      setUploadProgress(30);
      const uploadResponse = await fetch(upload_url, {
        method: 'PUT',
        body: selectedFile,
        headers: {
          'Content-Type': selectedFile.type || 'application/octet-stream',
        },
      });

      if (!uploadResponse.ok) {
        throw new Error('ファイルのアップロードに失敗しました');
      }

      setUploadProgress(70);

      // 3. ドキュメントレコード作成
      await createFileDocument({
        title: data.title,
        description: data.description,
        kind: data.kind,
        storage_path,
        size_bytes: selectedFile.size,
      });

      setUploadProgress(100);

      // 一覧を再取得
      mutate('/api/documents');

      // ダイアログを閉じる
      setOpen(false);

      // フォームとファイルをリセット
      form.reset();
      handleClearFile();
      setUploadProgress(0);

      alert('ファイルをアップロードしました');
    } catch (error) {
      console.error('アップロードエラー:', error);
      alert('ファイルのアップロードに失敗しました');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Upload className="h-4 w-4 mr-2" />
            ファイルをアップロード
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>ファイルをアップロード</DialogTitle>
          <DialogDescription>
            PDF、Word、PowerPoint等のファイルをアップロードします
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* ファイル選択 */}
            <div className="space-y-2">
              <label className="text-sm font-medium">ファイル *</label>
              <div className="space-y-2">
                <Input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                  className="cursor-pointer"
                />
                {selectedFile && (
                  <div className="flex items-center gap-2 p-2 border rounded-md bg-muted/50">
                    <FileIcon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm flex-1">{selectedFile.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </span>
                    {!isUploading && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={handleClearFile}
                      >
                        ×
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* タイトル */}
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>タイトル *</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="ドキュメントのタイトル"
                      disabled={isUploading}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 説明 */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>説明</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="ドキュメントの説明（オプション）"
                      rows={3}
                      disabled={isUploading}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 種別 */}
            <FormField
              control={form.control}
              name="kind"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>種別 *</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    disabled={isUploading}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="種別を選択" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {FILE_DOCUMENT_KINDS.map((kind) => (
                        <SelectItem key={kind.value} value={kind.value}>
                          {kind.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* アップロードプログレス */}
            {isUploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>アップロード中...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={isUploading}
              >
                キャンセル
              </Button>
              <Button type="submit" disabled={isUploading || !selectedFile}>
                {isUploading ? 'アップロード中...' : 'アップロード'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
