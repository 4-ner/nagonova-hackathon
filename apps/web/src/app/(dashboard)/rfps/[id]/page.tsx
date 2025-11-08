'use client';

import { use } from 'react';
import Link from 'next/link';
import { ArrowLeft, Calendar, MapPin, DollarSign, ExternalLink, FileText, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MatchScore } from '@/components/rfp/MatchScore';
import { BookmarkButton } from '@/features/bookmarks/components/BookmarkButton';
import { useRfp } from '@/hooks/useRfps';

interface RfpDetailPageProps {
  params: Promise<{ id: string }>;
}

/**
 * RFP詳細ページ
 *
 * RFP案件の詳細情報を表示します。
 */
export default function RfpDetailPage({ params }: RfpDetailPageProps) {
  const { id } = use(params);
  const { data: rfp, error, isLoading } = useRfp(id);

  // 締切日のフォーマット
  const formatDeadline = (deadline: string | undefined): string => {
    if (!deadline) return '未定';
    try {
      const date = new Date(deadline);
      return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'short',
      });
    } catch {
      return '未定';
    }
  };

  // 予算のフォーマット
  const formatBudget = (budget: number | undefined): string => {
    if (!budget) return '非公開';
    return `¥${budget.toLocaleString()}`;
  };

  // 日時のフォーマット
  const formatDateTime = (dateTime: string): string => {
    try {
      const date = new Date(dateTime);
      return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateTime;
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      {/* 戻るボタン */}
      <div className="mb-6">
        <Button variant="ghost" asChild>
          <Link href="/rfps" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            案件一覧に戻る
          </Link>
        </Button>
      </div>

      {/* 読み込み中 */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">読み込み中...</span>
        </div>
      )}

      {/* エラー */}
      {error && (
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

      {/* 詳細情報 */}
      {!isLoading && !error && rfp && (
        <div className="space-y-6">
          {/* ヘッダー */}
          <Card>
            <CardHeader>
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <CardTitle className="text-2xl flex-1">{rfp.title}</CardTitle>
                  <BookmarkButton rfpId={rfp.id} size="default" variant="outline" />
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-muted-foreground">{rfp.issuing_org}</p>
                  {rfp.url && (
                    <Button variant="default" asChild>
                      <a
                        href={rfp.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2"
                      >
                        <ExternalLink className="h-4 w-4" />
                        元の案件を見る
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>

            {/* マッチングスコア */}
            {rfp.match_score !== undefined && (
              <CardContent className="border-t">
                <h3 className="font-semibold mb-3">マッチング評価</h3>
                <MatchScore rfp={rfp} showDetails={true} />
              </CardContent>
            )}
          </Card>

          {/* 基本情報 */}
          <Card>
            <CardHeader>
              <CardTitle>基本情報</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* 地域 */}
                <div className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">地域</p>
                    <p className="font-medium">{rfp.region}</p>
                  </div>
                </div>

                {/* 予算 */}
                <div className="flex items-start gap-3">
                  <DollarSign className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">予算</p>
                    <p className="font-medium">{formatBudget(rfp.budget)}</p>
                  </div>
                </div>

                {/* 締切日 */}
                <div className="flex items-start gap-3">
                  <Calendar className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">応募締切</p>
                    <p className="font-medium">{formatDeadline(rfp.deadline)}</p>
                  </div>
                </div>

                {/* 取得日時 */}
                <div className="flex items-start gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">情報取得日</p>
                    <p className="font-medium">{formatDateTime(rfp.fetched_at)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 案件詳細 */}
          <Card>
            <CardHeader>
              <CardTitle>案件詳細</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {rfp.description}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* 外部ドキュメント */}
          {rfp.external_doc_urls && rfp.external_doc_urls.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>添付資料</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {rfp.external_doc_urls.map((url, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline"
                      >
                        資料 {index + 1}
                      </a>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* メタ情報 */}
          <Card>
            <CardHeader>
              <CardTitle>その他の情報</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{rfp.external_id}</Badge>
                <span>外部ID</span>
              </div>
              {rfp.has_embedding && (
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">AI検索対応</Badge>
                  <span>セマンティック検索が利用可能です</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
