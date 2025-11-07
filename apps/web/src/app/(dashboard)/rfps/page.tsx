'use client';

import { useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { RfpCard } from '@/components/rfp/RfpCard';
import { useRfpsWithMatching } from '@/hooks/useRfps';

/**
 * RFP一覧ページ
 *
 * マッチングスコア付きでRFP案件を表示します。
 */
export default function RfpsPage() {
  const [page, setPage] = useState(1);
  const [minScore, setMinScore] = useState<number | undefined>(undefined);
  const [mustRequirementsOnly, setMustRequirementsOnly] = useState(false);

  const pageSize = 20;

  // マッチングスコア付きRFP一覧を取得
  const { data, error, isLoading } = useRfpsWithMatching({
    page,
    page_size: pageSize,
    min_score: minScore,
    must_requirements_only: mustRequirementsOnly,
  });

  // フィルタをリセット
  const handleResetFilters = () => {
    setMinScore(undefined);
    setMustRequirementsOnly(false);
    setPage(1);
  };

  // フィルタが適用されているか
  const hasFilters = minScore !== undefined || mustRequirementsOnly;

  // ページネーション
  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;
  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">おすすめ案件</h1>
        <p className="text-muted-foreground">
          あなたの会社プロフィールに基づいてマッチングされた案件を表示しています
        </p>
      </div>

      {/* フィルター */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            {/* 最小スコア */}
            <div className="space-y-2">
              <Label htmlFor="minScore">最小マッチングスコア</Label>
              <Input
                id="minScore"
                type="number"
                min={0}
                max={100}
                placeholder="例: 50"
                value={minScore ?? ''}
                onChange={(e) => {
                  const value = e.target.value;
                  setMinScore(value ? parseInt(value, 10) : undefined);
                  setPage(1);
                }}
              />
            </div>

            {/* 必須要件のみ */}
            <div className="flex items-center gap-2">
              <input
                id="mustRequirementsOnly"
                type="checkbox"
                checked={mustRequirementsOnly}
                onChange={(e) => {
                  setMustRequirementsOnly(e.target.checked);
                  setPage(1);
                }}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="mustRequirementsOnly" className="cursor-pointer">
                必須要件を満たす案件のみ
              </Label>
            </div>

            {/* フィルターリセット */}
            {hasFilters && (
              <Button
                variant="outline"
                onClick={handleResetFilters}
                className="w-full md:w-auto"
              >
                フィルターをリセット
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

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

      {/* 案件一覧 */}
      {!isLoading && !error && data && (
        <>
          {/* 件数表示 */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="secondary">
                {data.total}件
              </Badge>
              {hasFilters && (
                <span className="text-sm text-muted-foreground">
                  （フィルター適用中）
                </span>
              )}
            </div>
          </div>

          {/* 案件カード */}
          {data.items.length > 0 ? (
            <div className="space-y-4">
              {data.items.map((rfp) => (
                <RfpCard key={rfp.id} rfp={rfp} showMatchScore={true} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center py-12">
                <p className="text-muted-foreground">
                  条件に一致する案件が見つかりませんでした
                </p>
                {hasFilters && (
                  <Button
                    variant="link"
                    onClick={handleResetFilters}
                    className="mt-2"
                  >
                    フィルターをリセット
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {/* ページネーション */}
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-4">
              <Button
                variant="outline"
                onClick={() => setPage((p) => p - 1)}
                disabled={!canGoPrevious}
              >
                前へ
              </Button>
              <span className="text-sm text-muted-foreground">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={!canGoNext}
              >
                次へ
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
