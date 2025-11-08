'use client';

import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import type { RFPWithMatching } from '@/types/rfp';

interface MatchScoreProps {
  /** RFP情報（マッチングスコア付き） */
  rfp: RFPWithMatching;
  /** 詳細表示するか */
  showDetails?: boolean;
  /** 表示する要約ポイントの最大数（undefinedの場合は全て表示） */
  maxSummaryPoints?: number;
}

/**
 * マッチングスコア表示コンポーネント
 *
 * RFPのマッチングスコアと詳細情報を表示します。
 *
 * @example
 * ```tsx
 * <MatchScore rfp={rfp} showDetails={true} />
 * ```
 */
export function MatchScore({
  rfp,
  showDetails = false,
  maxSummaryPoints
}: MatchScoreProps) {
  const score = rfp.match_score ?? 0;

  // スコアに応じた色を返す
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  // スコアのテキスト色
  const getScoreTextColor = (score: number): string => {
    if (score >= 80) return 'text-green-700';
    if (score >= 60) return 'text-blue-700';
    if (score >= 40) return 'text-yellow-700';
    return 'text-gray-700';
  };

  return (
    <div className="space-y-3">
      {/* スコア表示 */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-24 rounded-full bg-gray-200 overflow-hidden`}
          >
            <div
              className={`h-full ${getScoreColor(score)} transition-all duration-300`}
              style={{ width: `${score}%` }}
            />
          </div>
          <span className={`text-lg font-bold ${getScoreTextColor(score)}`}>
            {score}点
          </span>
        </div>

        {/* バッジ */}
        <div className="flex gap-2">
          {rfp.must_requirements_ok && (
            <Badge variant="default">必須要件OK</Badge>
          )}
          {rfp.budget_match_ok && <Badge variant="secondary">予算適合</Badge>}
          {rfp.region_match_ok && <Badge variant="secondary">地域適合</Badge>}
        </div>
      </div>

      {/* 詳細情報 */}
      {showDetails && rfp.summary_points && rfp.summary_points.length > 0 && (
        <Card className="p-4 bg-muted/50">
          <h4 className="font-semibold mb-2 text-sm">マッチング理由</h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {(maxSummaryPoints !== undefined
              ? rfp.summary_points.slice(0, maxSummaryPoints)
              : rfp.summary_points
            ).map((point, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
          {maxSummaryPoints !== undefined &&
            rfp.summary_points.length > maxSummaryPoints && (
              <p className="mt-2 text-xs text-muted-foreground">
                他{rfp.summary_points.length - maxSummaryPoints}件
              </p>
            )}

          {/* マッチング要因の内訳 */}
          {rfp.match_factors && (
            <div className="mt-3 pt-3 border-t space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between">
                <span>スキルマッチ度:</span>
                <span className="font-mono">
                  {(rfp.match_factors.skill_match * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>地域係数:</span>
                <span className="font-mono">
                  ×{rfp.match_factors.region_coefficient.toFixed(1)}
                </span>
              </div>
              {rfp.match_factors.budget_boost > 0 && (
                <div className="flex justify-between">
                  <span>予算ボーナス:</span>
                  <span className="font-mono text-green-600">
                    +{(rfp.match_factors.budget_boost * 100).toFixed(0)}%
                  </span>
                </div>
              )}
              {rfp.match_factors.deadline_boost > 0 && (
                <div className="flex justify-between">
                  <span>納期ボーナス:</span>
                  <span className="font-mono text-blue-600">
                    +{(rfp.match_factors.deadline_boost * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
