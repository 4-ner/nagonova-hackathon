'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiPost } from '@/lib/api';
import type { CreateCompanyRequest } from '@/types/company';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { TagInput } from '@/components/ui/tag-input';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

/**
 * 会社プロフィール設定画面のバリデーションスキーマ
 */
const profileSetupSchema = z.object({
  name: z
    .string()
    .min(1, '会社名を入力してください')
    .max(200, '会社名は200文字以内で入力してください'),
  description: z.string().optional(),
  regions: z.array(z.string()).min(0, '地域を1つ以上選択してください'),
  budget_min: z
    .number()
    .min(0, '最小金額は0以上である必要があります')
    .optional()
    .or(z.literal('')),
  budget_max: z
    .number()
    .min(0, '最大金額は0以上である必要があります')
    .optional()
    .or(z.literal('')),
  skills: z
    .array(z.string())
    .min(1, '保有スキルを1つ以上入力してください'),
  ng_keywords: z.array(z.string()),
}).refine(
  (data) => {
    // 予算の最小値と最大値の整合性チェック
    if (
      typeof data.budget_min === 'number' &&
      typeof data.budget_max === 'number'
    ) {
      return data.budget_min <= data.budget_max;
    }
    return true;
  },
  {
    message: '最小金額は最大金額以下である必要があります',
    path: ['budget_min'],
  }
);

type ProfileSetupFormData = z.infer<typeof profileSetupSchema>;

/**
 * 会社プロフィール設定画面
 *
 * 新規ユーザー向けの初回設定画面
 * 会社名、スキル等を入力して会社プロフィールを作成します
 */
export default function ProfileSetupPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<ProfileSetupFormData>({
    resolver: zodResolver(profileSetupSchema),
    defaultValues: {
      name: '',
      description: '',
      regions: [],
      budget_min: '',
      budget_max: '',
      skills: [],
      ng_keywords: [],
    },
  });

  /**
   * フォーム送信処理
   */
  const onSubmit = async (data: ProfileSetupFormData) => {
    setIsSubmitting(true);

    try {
      // 空文字列をundefinedに変換
      const requestData: CreateCompanyRequest = {
        name: data.name,
        description: data.description || undefined,
        regions: data.regions,
        budget_min:
          typeof data.budget_min === 'number' ? data.budget_min : undefined,
        budget_max:
          typeof data.budget_max === 'number' ? data.budget_max : undefined,
        skills: data.skills,
        ng_keywords: data.ng_keywords,
      };

      // API呼び出し
      await apiPost('/api/companies', requestData);

      // 成功通知
      toast.success('会社プロフィールを作成しました', {
        description: 'ダッシュボードに移動します',
      });

      // ダッシュボードにリダイレクト
      router.push('/');
    } catch (error) {
      console.error('会社プロフィール作成エラー:', error);
      toast.error('会社プロフィールの作成に失敗しました', {
        description:
          error instanceof Error ? error.message : '不明なエラーが発生しました',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">会社プロフィール設定</CardTitle>
          <CardDescription>
            会社名やスキル等を入力して会社プロフィールを作成してください
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* 会社名 */}
            <div className="space-y-2">
              <Label htmlFor="name">
                会社名 <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                type="text"
                placeholder="株式会社サンプル"
                {...register('name')}
                disabled={isSubmitting}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            {/* 会社説明 */}
            <div className="space-y-2">
              <Label htmlFor="description">会社説明</Label>
              <textarea
                id="description"
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="会社の特徴や強みを入力してください"
                {...register('description')}
                disabled={isSubmitting}
              />
              {errors.description && (
                <p className="text-sm text-destructive">
                  {errors.description.message}
                </p>
              )}
            </div>

            {/* 対応可能地域 */}
            <div className="space-y-2">
              <Label htmlFor="regions">対応可能地域</Label>
              <Controller
                name="regions"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="地域を入力してEnterキーで追加: 例 東京都、大阪府"
                    disabled={isSubmitting}
                  />
                )}
              />
              {errors.regions && (
                <p className="text-sm text-destructive">
                  {errors.regions.message}
                </p>
              )}
            </div>

            {/* 希望案件規模 */}
            <div className="space-y-4">
              <Label>希望案件規模（円）</Label>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="budget_min" className="text-sm text-muted-foreground">
                    最小金額
                  </Label>
                  <Input
                    id="budget_min"
                    type="number"
                    placeholder="1000000"
                    min="0"
                    {...register('budget_min', {
                      setValueAs: (v) => (v === '' ? '' : Number(v)),
                    })}
                    disabled={isSubmitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="budget_max" className="text-sm text-muted-foreground">
                    最大金額
                  </Label>
                  <Input
                    id="budget_max"
                    type="number"
                    placeholder="10000000"
                    min="0"
                    {...register('budget_max', {
                      setValueAs: (v) => (v === '' ? '' : Number(v)),
                    })}
                    disabled={isSubmitting}
                  />
                </div>
              </div>
              {errors.budget_min && (
                <p className="text-sm text-destructive">
                  {errors.budget_min.message}
                </p>
              )}
              {errors.budget_max && (
                <p className="text-sm text-destructive">
                  {errors.budget_max.message}
                </p>
              )}
            </div>

            {/* 保有スキル */}
            <div className="space-y-2">
              <Label htmlFor="skills">
                保有スキル <span className="text-destructive">*</span>
              </Label>
              <Controller
                name="skills"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="スキルを入力してEnterキーで追加: 例 Webデザイン、システム開発"
                    disabled={isSubmitting}
                  />
                )}
              />
              {errors.skills && (
                <p className="text-sm text-destructive">
                  {errors.skills.message}
                </p>
              )}
            </div>

            {/* NGキーワード */}
            <div className="space-y-2">
              <Label htmlFor="ng_keywords">NGキーワード</Label>
              <Controller
                name="ng_keywords"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="避けたいキーワードを追加: 例 長期出張"
                    disabled={isSubmitting}
                  />
                )}
              />
              {errors.ng_keywords && (
                <p className="text-sm text-destructive">
                  {errors.ng_keywords.message}
                </p>
              )}
            </div>

            {/* 送信ボタン */}
            <div className="flex justify-end space-x-4">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full sm:w-auto"
              >
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                会社プロフィールを作成
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
