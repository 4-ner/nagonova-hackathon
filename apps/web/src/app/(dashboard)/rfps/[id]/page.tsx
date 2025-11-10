'use client';

import { use } from 'react';
import Link from 'next/link';
import {
  Calendar,
  MapPin,
  DollarSign,
  ExternalLink,
  FileText,
  Loader2,
  AlertCircle,
  FileEdit,
  Building2,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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

  // 締切までの日数を計算
  const getDaysUntilDeadline = (deadline: string | undefined): number | null => {
    if (!deadline) return null;
    try {
      const date = new Date(deadline);
      const today = new Date();
      const diffTime = date.getTime() - today.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    } catch {
      return null;
    }
  };

  const daysUntilDeadline = rfp ? getDaysUntilDeadline(rfp.deadline) : null;

  return (
    <div className="container mx-auto py-6 px-4 max-w-6xl">
      {/* 読み込み中 */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">案件情報を読み込んでいます...</p>
        </div>
      )}

      {/* エラー */}
      {error && (
        <Card className="border-destructive bg-destructive/5">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3 text-destructive">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-lg mb-1">エラーが発生しました</p>
                <p className="text-sm opacity-90">{error.message}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 詳細情報 */}
      {!isLoading && !error && rfp && (
        <div className="space-y-6">
          {/* メインヘッダーカード */}
          <Card className="border-2">
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {daysUntilDeadline !== null && daysUntilDeadline <= 7 && (
                      <Badge variant={daysUntilDeadline <= 3 ? 'destructive' : 'default'}>
                        <Clock className="h-3 w-3 mr-1" />
                        締切まであと{daysUntilDeadline}日
                      </Badge>
                    )}
                    {rfp.has_embedding && (
                      <Badge variant="secondary">
                        <Sparkles className="h-3 w-3 mr-1" />
                        AI検索対応
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-3xl leading-tight">{rfp.title}</CardTitle>
                  <CardDescription className="flex items-center gap-2 text-base">
                    <Building2 className="h-4 w-4" />
                    {rfp.issuing_org}
                  </CardDescription>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Button size="lg" asChild className="gap-2">
                  <Link href={`/rfps/${rfp.id}/proposal`}>
                    <FileEdit className="h-4 w-4" />
                    提案ドラフト生成
                  </Link>
                </Button>
                {rfp.url && (
                  <Button size="lg" variant="outline" asChild className="gap-2">
                    <a href={rfp.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4" />
                      元の案件を見る
                    </a>
                  </Button>
                )}
                <BookmarkButton rfpId={rfp.id} size="lg" variant="outline" />
              </div>
            </CardHeader>

            {/* マッチングスコア */}
            {rfp.match_score !== undefined && (
              <>
                <Separator />
                <CardContent className="pt-6">
                  <MatchScore rfp={rfp} showDetails={true} />
                </CardContent>
              </>
            )}
          </Card>

          {/* タブコンテンツ */}
          <Tabs defaultValue="details" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="details">案件詳細</TabsTrigger>
              <TabsTrigger value="info">基本情報</TabsTrigger>
              <TabsTrigger value="documents">添付資料</TabsTrigger>
            </TabsList>

            {/* 案件詳細タブ */}
            <TabsContent value="details" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>案件内容</CardTitle>
                  <CardDescription>
                    この案件の詳細な説明と要件です。
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                      {rfp.description}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* サマリーポイント */}
              {rfp.summary_points && rfp.summary_points.length > 0 && (
                <Card className="bg-primary/5 border-primary/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5" />
                      マッチング理由
                    </CardTitle>
                    <CardDescription>
                      あなたの会社がこの案件に適している理由
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {rfp.summary_points.map((point, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-primary mt-1">•</span>
                          <span className="text-sm">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* 基本情報タブ */}
            <TabsContent value="info" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>基本情報</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 地域 */}
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                      <div className="p-2 rounded-md bg-background">
                        <MapPin className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-muted-foreground mb-1">
                          対象地域
                        </p>
                        <p className="font-semibold text-lg">{rfp.region}</p>
                      </div>
                    </div>

                    {/* 予算 */}
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                      <div className="p-2 rounded-md bg-background">
                        <DollarSign className="h-5 w-5 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-muted-foreground mb-1">
                          予算
                        </p>
                        <p className="font-semibold text-lg">{formatBudget(rfp.budget)}</p>
                      </div>
                    </div>

                    {/* 締切日 */}
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                      <div className="p-2 rounded-md bg-background">
                        <Calendar className="h-5 w-5 text-orange-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-muted-foreground mb-1">
                          応募締切
                        </p>
                        <p className="font-semibold text-lg">
                          {formatDeadline(rfp.deadline)}
                        </p>
                        {daysUntilDeadline !== null && daysUntilDeadline > 0 && (
                          <p className="text-xs text-muted-foreground mt-1">
                            あと{daysUntilDeadline}日
                          </p>
                        )}
                      </div>
                    </div>

                    {/* 取得日時 */}
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                      <div className="p-2 rounded-md bg-background">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-muted-foreground mb-1">
                          情報取得日
                        </p>
                        <p className="font-semibold text-lg">
                          {formatDateTime(rfp.fetched_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <Separator className="my-6" />

                  {/* 外部ID */}
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono">
                      {rfp.external_id}
                    </Badge>
                    <span className="text-sm text-muted-foreground">外部案件ID</span>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 添付資料タブ */}
            <TabsContent value="documents" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>添付資料</CardTitle>
                  <CardDescription>
                    この案件に関連する資料やドキュメント
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {rfp.external_doc_urls && rfp.external_doc_urls.length > 0 ? (
                    <div className="space-y-3">
                      {rfp.external_doc_urls.map((url, index) => (
                        <a
                          key={index}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-4 rounded-lg border hover:bg-muted/50 transition-colors group"
                        >
                          <div className="p-2 rounded-md bg-primary/10">
                            <FileText className="h-5 w-5 text-primary" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium group-hover:text-primary transition-colors">
                              資料 {index + 1}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {url}
                            </p>
                          </div>
                          <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                        </a>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <FileText className="h-12 w-12 mx-auto mb-3 opacity-20" />
                      <p>添付資料はありません</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
