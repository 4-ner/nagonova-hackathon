import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

/**
 * Supabase Auth コールバックハンドラー
 *
 * メールOTPリンクをクリックした後のコールバックを処理します。
 * トークンを検証してセッションを作成し、ユーザーをリダイレクトします。
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const redirect = searchParams.get('redirect') || '/';

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      // 認証成功 - リダイレクト先へ遷移
      const forwardedHost = request.headers.get('x-forwarded-host');
      const isLocalEnv = process.env.NODE_ENV === 'development';
      const redirectUrl = isLocalEnv
        ? `${origin}${redirect}`
        : `https://${forwardedHost}${redirect}`;

      return NextResponse.redirect(redirectUrl);
    }
  }

  // エラー時またはコードがない場合はログインページへ
  return NextResponse.redirect(`${origin}/login?error=認証に失敗しました`);
}
