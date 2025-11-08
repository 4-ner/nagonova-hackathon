'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { PREFECTURES } from '@/lib/constants/prefectures';

/**
 * RFPフィルターの状態を表す型
 */
export interface RfpFilterState {
  /** 最小マッチングスコア */
  minScore?: number;
  /** 必須要件を満たす案件のみ表示 */
  mustRequirementsOnly: boolean;
  /** 締切日フィルター（日数） */
  deadlineDays?: number;
  /** 都道府県コード */
  region?: string;
  /** 最小予算（円） */
  budgetMin?: number;
  /** 最大予算（円） */
  budgetMax?: number;
}

/**
 * RFPフィルターコンポーネントのProps
 */
interface RfpFilterProps {
  /** 現在のフィルター状態 */
  filters: RfpFilterState;
  /** フィルター変更時のコールバック */
  onFilterChange: (filters: RfpFilterState) => void;
}

/**
 * 締切日フィルターの選択肢
 */
const DEADLINE_OPTIONS = [
  { value: 'all', label: 'すべて' },
  { value: '7', label: '7日以内' },
  { value: '14', label: '14日以内' },
  { value: '30', label: '30日以内' },
] as const;

/**
 * RFPフィルターコンポーネント
 *
 * 案件の絞り込み条件を設定するためのフィルターUIを提供します。
 * 締切日・地域・予算・スコアなどの複数の条件を組み合わせて検索できます。
 */
export function RfpFilter({ filters, onFilterChange }: RfpFilterProps) {
  // フィルターの一部を更新するヘルパー関数
  const updateFilter = (updates: Partial<RfpFilterState>) => {
    onFilterChange({ ...filters, ...updates });
  };

  // フィルターがデフォルト状態かどうかを判定
  const hasFilters =
    filters.minScore !== undefined ||
    filters.mustRequirementsOnly ||
    filters.deadlineDays !== undefined ||
    filters.region !== undefined ||
    filters.budgetMin !== undefined ||
    filters.budgetMax !== undefined;

  // フィルターをリセット
  const handleResetFilters = () => {
    onFilterChange({
      minScore: undefined,
      mustRequirementsOnly: false,
      deadlineDays: undefined,
      region: undefined,
      budgetMin: undefined,
      budgetMax: undefined,
    });
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-6">
          {/* グリッドレイアウト: 主要フィルター */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 締切日フィルター */}
            <div className="space-y-2">
              <Label htmlFor="deadline">締切日</Label>
              <Select
                value={filters.deadlineDays?.toString() ?? 'all'}
                onValueChange={(value) =>
                  updateFilter({
                    deadlineDays: value === 'all' ? undefined : parseInt(value, 10),
                  })
                }
              >
                <SelectTrigger id="deadline">
                  <SelectValue placeholder="すべて" />
                </SelectTrigger>
                <SelectContent>
                  {DEADLINE_OPTIONS.map((option) => (
                    <SelectItem
                      key={option.label}
                      value={option.value}
                    >
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 地域フィルター */}
            <div className="space-y-2">
              <Label htmlFor="region">都道府県</Label>
              <Select
                value={filters.region ?? 'all'}
                onValueChange={(value) =>
                  updateFilter({ region: value === 'all' ? undefined : value })
                }
              >
                <SelectTrigger id="region">
                  <SelectValue placeholder="全国" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全国</SelectItem>
                  {PREFECTURES.map((prefecture) => (
                    <SelectItem key={prefecture.code} value={prefecture.code}>
                      {prefecture.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 予算範囲: 最小値 */}
            <div className="space-y-2">
              <Label htmlFor="budgetMin">最小予算（円）</Label>
              <Input
                id="budgetMin"
                type="number"
                min={0}
                placeholder="例: 1000000"
                value={filters.budgetMin ?? ''}
                onChange={(e) => {
                  const value = e.target.value;
                  updateFilter({
                    budgetMin: value ? parseInt(value, 10) : undefined,
                  });
                }}
              />
            </div>

            {/* 予算範囲: 最大値 */}
            <div className="space-y-2">
              <Label htmlFor="budgetMax">最大予算（円）</Label>
              <Input
                id="budgetMax"
                type="number"
                min={0}
                placeholder="例: 10000000"
                value={filters.budgetMax ?? ''}
                onChange={(e) => {
                  const value = e.target.value;
                  updateFilter({
                    budgetMax: value ? parseInt(value, 10) : undefined,
                  });
                }}
              />
            </div>
          </div>

          {/* グリッドレイアウト: 詳細フィルター */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end pt-4 border-t">
            {/* 最小マッチングスコア */}
            <div className="space-y-2">
              <Label htmlFor="minScore">最小マッチングスコア</Label>
              <Input
                id="minScore"
                type="number"
                min={0}
                max={100}
                placeholder="例: 50"
                value={filters.minScore ?? ''}
                onChange={(e) => {
                  const value = e.target.value;
                  updateFilter({
                    minScore: value ? parseInt(value, 10) : undefined,
                  });
                }}
              />
            </div>

            {/* 必須要件のみ */}
            <div className="flex items-center gap-2 h-10">
              <input
                id="mustRequirementsOnly"
                type="checkbox"
                checked={filters.mustRequirementsOnly}
                onChange={(e) =>
                  updateFilter({ mustRequirementsOnly: e.target.checked })
                }
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="mustRequirementsOnly" className="cursor-pointer">
                必須要件を満たす案件のみ
              </Label>
            </div>

            {/* フィルターリセットボタン */}
            {hasFilters && (
              <Button
                variant="outline"
                onClick={handleResetFilters}
                className="w-full"
              >
                フィルターをリセット
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
