'use client';

import Link from 'next/link';
import { Calendar, MapPin, DollarSign, ExternalLink } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MatchScore } from './MatchScore';
import type { RFPWithMatching } from '@/types/rfp';

interface RfpCardProps {
  /** RFP情報（マッチングスコア付き） */
  rfp: RFPWithMatching;
  /** マッチングスコアを表示するか */
  showMatchScore?: boolean;
}

/**
 * RFPカードコンポーネント
 *
 * RFP案件の概要をカード形式で表示します。
 *
 * @example
 * ```tsx
 * <RfpCard rfp={rfp} showMatchScore={true} />
 * ```
 */
export function RfpCard({ rfp, showMatchScore = false }: RfpCardProps) {
  // 締切日のフォーマット
  const formatDeadline = (deadline: string | undefined): string => {
    if (!deadline) return '未定';
    try {
      const date = new Date(deadline);
      return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
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

  // 説明文を省略
  const truncateDescription = (text: string, maxLength: number = 150): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <CardTitle className="text-xl">
              <Link
                href={`/rfps/${rfp.id}`}
                className="hover:text-primary transition-colors"
              >
                {rfp.title}
              </Link>
            </CardTitle>
            <CardDescription className="flex items-center gap-2 text-sm">
              <span className="font-medium">{rfp.issuing_org}</span>
            </CardDescription>
          </div>

          {/* 外部リンク */}
          {rfp.url && (
            <Button
              variant="outline"
              size="sm"
              asChild
              className="shrink-0"
            >
              <a
                href={rfp.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1"
              >
                <ExternalLink className="h-4 w-4" />
                詳細
              </a>
            </Button>
          )}
        </div>

        {/* マッチングスコア */}
        {showMatchScore && rfp.match_score !== undefined && (
          <div className="mt-4">
            <MatchScore rfp={rfp} showDetails={false} />
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 説明文 */}
        <p className="text-sm text-muted-foreground leading-relaxed">
          {truncateDescription(rfp.description)}
        </p>

        {/* メタ情報 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
          {/* 地域 */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="h-4 w-4 shrink-0" />
            <span>{rfp.region}</span>
          </div>

          {/* 予算 */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <DollarSign className="h-4 w-4 shrink-0" />
            <span>{formatBudget(rfp.budget)}</span>
          </div>

          {/* 締切日 */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-4 w-4 shrink-0" />
            <span>{formatDeadline(rfp.deadline)}</span>
          </div>
        </div>

        {/* 外部ドキュメント */}
        {rfp.external_doc_urls && rfp.external_doc_urls.length > 0 && (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              添付資料 {rfp.external_doc_urls.length}件
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
