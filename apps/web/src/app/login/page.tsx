'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { createClient } from '@/lib/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Mail, Loader2 } from 'lucide-react';

/**
 * ログインフォームのバリデーションスキーマ
 */
const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'メールアドレスを入力してください')
    .email('有効なメールアドレスを入力してください'),
});

type LoginFormData = z.infer<typeof loginSchema>;

/**
 * ログインフォームコンポーネント
 */
function LoginForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/';

  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const supabase = createClient();

  /**
   * ログインフォーム送信処理
   */
  const onSubmit = async (data: LoginFormData) => {
    setIsSubmitting(true);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: data.email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback?redirect=${redirectTo}`,
        },
      });

      if (error) {
        throw error;
      }

      // 送信成功
      setEmailSent(true);
      toast.success('ログインリンクを送信しました', {
        description: 'メールを確認してください',
      });
    } catch (error) {
      console.error('ログインエラー:', error);
      toast.error('ログインに失敗しました', {
        description:
          error instanceof Error ? error.message : '不明なエラーが発生しました',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">RFP Radar</CardTitle>
          <CardDescription className="text-center">
            官公需入札案件マッチングシステム
          </CardDescription>
        </CardHeader>
        <CardContent>
          {emailSent ? (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Mail className="h-6 w-6 text-primary" />
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold">メールを確認してください</h3>
                <p className="text-sm text-muted-foreground">
                  {getValues('email')}にログインリンクを送信しました。メール内のリンクをクリックしてログインしてください。
                </p>
              </div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setEmailSent(false)}
              >
                別のメールアドレスで試す
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">メールアドレス</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  {...register('email')}
                  disabled={isSubmitting}
                />
                {errors.email && (
                  <p className="text-sm text-destructive">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    送信中...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    ログインリンクを送信
                  </>
                )}
              </Button>

              <p className="text-xs text-muted-foreground text-center">
                メールアドレスを入力すると、ログイン用のリンクが送信されます。
                <br />
                メール内のリンクをクリックしてログインしてください。
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * ログインページ
 *
 * メールOTP認証を使用してユーザーをログインさせます。
 */
export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-muted/40">
          <div className="text-lg text-muted-foreground">読み込み中...</div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
