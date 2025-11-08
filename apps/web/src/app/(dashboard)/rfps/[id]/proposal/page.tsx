'use client';

import { use } from 'react';
import Link from 'next/link';
import { ArrowLeft, Loader2, AlertCircle, Copy, Download, FileEdit } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useProposalDraft } from '@/hooks/useProposal';
import { useRfp } from '@/hooks/useRfps';
import { toast } from 'sonner';

interface ProposalPageProps {
  params: Promise<{ id: string }>;
}

/**
 * 提案ドラフトページ
 *
 * RFP案件に対する提案書のドラフトを生成・表示します。
 */
export default function ProposalPage({ params }: ProposalPageProps) {
  const { id } = use(params);
  const { data: draft, error: draftError, isLoading: isDraftLoading } = useProposalDraft(id);
  const { data: rfp, error: rfpError, isLoading: isRfpLoading } = useRfp(id);

  const isLoading = isDraftLoading || isRfpLoading;
  const error = draftError || rfpError;

  /**
   * クリップボードにコピー
   */
  const handleCopy = async () => {
    if (!draft) return;

    try {
      await navigator.clipboard.writeText(draft);
      toast.success('提案ドラフトをクリップボードにコピーしました');
    } catch (err) {
      toast.error('コピーに失敗しました');
      console.error('Copy failed:', err);
    }
  };

  /**
   * Markdownファイルとしてダウンロード
   */
  const handleDownload = () => {
    if (!draft || !rfp) return;

    try {
      const blob = new Blob([draft], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `proposal-${rfp.external_id}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('提案ドラフトをダウンロードしました');
    } catch (err) {
      toast.error('ダウンロードに失敗しました');
      console.error('Download failed:', err);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-5xl">
      {/* 戻るボタン */}
      <div className="mb-6">
        <Button variant="ghost" asChild>
          <Link href={`/rfps/${id}`} className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            案件詳細に戻る
          </Link>
        </Button>
      </div>

      {/* ページタイトル */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <FileEdit className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">提案ドラフト</h1>
        </div>
        {rfp && (
          <p className="text-muted-foreground">
            案件: {rfp.title}
          </p>
        )}
      </div>

      {/* 読み込み中 */}
      {isLoading && (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center gap-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center">
                <p className="font-semibold text-lg">提案ドラフトを生成中...</p>
                <p className="text-sm text-muted-foreground mt-1">
                  AIが提案内容を分析しています。しばらくお待ちください。
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* エラー */}
      {!isLoading && error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div>
                <p className="font-semibold">エラーが発生しました</p>
                <p className="text-sm">{error.message}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ドラフト表示 */}
      {!isLoading && !error && draft && (
        <div className="space-y-6">
          {/* アクションボタン */}
          <Card>
            <CardHeader>
              <CardTitle>アクション</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Button onClick={handleCopy} variant="outline" className="gap-2">
                  <Copy className="h-4 w-4" />
                  コピー
                </Button>
                <Button onClick={handleDownload} variant="outline" className="gap-2">
                  <Download className="h-4 w-4" />
                  ダウンロード
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Markdownプレビュー */}
          <Card>
            <CardHeader>
              <CardTitle>プレビュー</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:leading-relaxed prose-ul:my-3 prose-ol:my-3 prose-li:my-1">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {draft}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>

          {/* 注意事項 */}
          <Card className="bg-muted/50">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">
                <strong>注意:</strong> このドラフトはAIにより自動生成されたものです。
                実際の提案書として使用する前に、内容を十分に確認・修正してください。
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
