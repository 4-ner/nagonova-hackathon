'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import { useCreateUrlDocument } from '@/hooks/useDocuments';
import type { DocumentKind } from '@/types/document';
import { mutate } from 'swr';

/**
 * ドキュメント種別の選択肢（URL型用）
 */
const URL_DOCUMENT_KINDS: { value: DocumentKind; label: string }[] = [
  { value: 'url', label: 'URL' },
  { value: 'pdf', label: 'PDF' },
  { value: 'word', label: 'Word' },
  { value: 'ppt', label: 'PowerPoint' },
  { value: 'text', label: 'テキスト' },
];

/**
 * バリデーションスキーマ
 */
const urlDocumentSchema = z.object({
  title: z
    .string()
    .min(1, 'タイトルは必須です')
    .max(200, 'タイトルは200文字以内で入力してください'),
  description: z.string().max(1000, '説明は1000文字以内で入力してください').optional(),
  kind: z.enum(['url', 'pdf', 'word', 'ppt', 'text', 'image'], {
    message: '種別を選択してください',
  }),
  url: z.string().url('有効なURLを入力してください'),
});

type UrlDocumentFormData = z.infer<typeof urlDocumentSchema>;

interface DocumentUrlDialogProps {
  /** ダイアログのトリガーボタン */
  trigger?: React.ReactNode;
}

/**
 * URL型ドキュメント作成ダイアログ
 *
 * URLを入力してドキュメントを作成するダイアログコンポーネント
 *
 * @example
 * ```tsx
 * <DocumentUrlDialog trigger={<Button>URLを追加</Button>} />
 * ```
 */
export function DocumentUrlDialog({ trigger }: DocumentUrlDialogProps) {
  const [open, setOpen] = useState(false);
  const { trigger: createDocument, isMutating } = useCreateUrlDocument();

  const form = useForm<UrlDocumentFormData>({
    resolver: zodResolver(urlDocumentSchema),
    defaultValues: {
      title: '',
      description: '',
      kind: 'url',
      url: '',
    },
  });

  // フォーム送信
  const onSubmit = async (data: UrlDocumentFormData) => {
    try {
      await createDocument(data);
      // 一覧を再取得
      mutate('/api/documents');
      // ダイアログを閉じる
      setOpen(false);
      // フォームをリセット
      form.reset();
      alert('URLを追加しました');
    } catch (error) {
      console.error('URL追加エラー:', error);
      alert('URLの追加に失敗しました');
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || <Button variant="outline">URLを追加</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>URLを追加</DialogTitle>
          <DialogDescription>
            外部リンクやオンラインドキュメントのURLを登録します
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* URL */}
            <FormField
              control={form.control}
              name="url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL *</FormLabel>
                  <FormControl>
                    <Input
                      type="url"
                      placeholder="https://example.com/document.pdf"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    ドキュメントのURLを入力してください
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* タイトル */}
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>タイトル *</FormLabel>
                  <FormControl>
                    <Input placeholder="ドキュメントのタイトル" {...field} />
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
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="種別を選択" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {URL_DOCUMENT_KINDS.map((kind) => (
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

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={isMutating}
              >
                キャンセル
              </Button>
              <Button type="submit" disabled={isMutating}>
                {isMutating ? '追加中...' : '追加'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
