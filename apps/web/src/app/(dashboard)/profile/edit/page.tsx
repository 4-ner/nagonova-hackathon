'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import useSWR from 'swr';
import { apiGet, apiPut } from '@/lib/api';
import type { Company, UpdateCompanyRequest } from '@/types/company';
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
 * 会社プロフィール編集画面のバリデーションスキーマ
 */
const profileEditSchema = z.object({
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

type ProfileEditFormData = z.infer<typeof profileEditSchema>;

/**
 * 会社プロフィール編集画面
 *
 * 既存の会社情報を更新します
 */
export default function ProfileEditPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 会社情報取得
  const { data: company, error, isLoading } = useSWR<Company>(
    '/api/companies/me',
    apiGet
  );

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<ProfileEditFormData>({
    resolver: zodResolver(profileEditSchema),
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

  // データ取得後にフォームを初期化
  useEffect(() => {
    if (company) {
      reset({
        name: company.name,
        description: company.description || '',
        regions: company.regions || [],
        budget_min: company.budget_min || '',
        budget_max: company.budget_max || '',
        skills: company.skills || [],
        ng_keywords: company.ng_keywords || [],
      });
    }
  }, [company, reset]);

  /**
   * フォーム送信処理
   */
  const onSubmit = async (data: ProfileEditFormData) => {
    setIsSubmitting(true);

    try {
      // 空文字列をundefinedに変換
      const requestData: UpdateCompanyRequest = {
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
      await apiPut('/api/companies/me', requestData);

      // 成功通知
      toast.success('会社プロフィールを更新しました');

      // ダッシュボードにリダイレクト
      router.push('/');
    } catch (error) {
      console.error('会社プロフィール更新エラー:', error);
      toast.error('会社プロフィールの更新に失敗しました', {
        description:
          error instanceof Error ? error.message : '不明なエラーが発生しました',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ローディング中
  if (isLoading) {
    return (
      <div className="container mx-auto flex min-h-screen items-center justify-center px-4 py-8">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <p className="text-muted-foreground">読み込み中...</p>
        </div>
      </div>
    );
  }

  // エラー発生
  if (error) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">エラー</CardTitle>
            <CardDescription>
              会社プロフィール情報の取得に失敗しました
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error
                ? error.message
                : '不明なエラーが発生しました'}
            </p>
            <Button
              className="mt-4"
              variant="outline"
              onClick={() => router.push('/')}
            >
              ダッシュボードに戻る
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // データが存在しない
  if (!company) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>会社プロフィールが未作成</CardTitle>
            <CardDescription>
              会社プロフィールがまだ作成されていません
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push('/profile/setup')}>
              会社プロフィールを作成
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">会社プロフィール編集</CardTitle>
          <CardDescription>
            会社情報を更新してください
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
                type="button"
                variant="outline"
                onClick={() => router.push('/')}
                disabled={isSubmitting}
              >
                キャンセル
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                更新する
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
