import { type NextRequest } from 'next/server';
import { updateSession } from '@/lib/supabase/middleware';

/**
 * Next.js Middleware
 *
 * すべてのリクエストでセッションを更新し、未認証ユーザーを保護されたルートからリダイレクトします。
 *
 * 認証フロー:
 * 1. すべてのリクエストでセッションを更新（リフレッシュトークンがあれば自動更新）
 * 2. 未認証ユーザーが保護されたルートにアクセスした場合、/loginにリダイレクト
 * 3. 認証済みユーザーが/loginにアクセスした場合、ホーム（/）にリダイレクト
 */
export async function middleware(request: NextRequest) {
  const { supabaseResponse, session } = await updateSession(request);

  const { pathname } = request.nextUrl;

  // 公開ルート（認証不要）
  const isPublicRoute = pathname === '/login';

  // 保護されたルート（認証必須）
  const isProtectedRoute =
    pathname.startsWith('/profile') ||
    pathname.startsWith('/dashboard') ||
    pathname === '/';

  // 未認証ユーザーが保護されたルートにアクセスした場合、/loginにリダイレクト
  if (!session && !isPublicRoute && isProtectedRoute) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = '/login';
    // リダイレクト元のURLを保存して、ログイン後に戻れるようにする
    redirectUrl.searchParams.set('redirect', pathname);
    return Response.redirect(redirectUrl);
  }

  // 認証済みユーザーが/loginにアクセスした場合、ホームにリダイレクト
  if (session && isPublicRoute) {
    const redirectUrl = request.nextUrl.clone();
    // redirect パラメータがあればそこにリダイレクト、なければホームへ
    const redirectTo = request.nextUrl.searchParams.get('redirect');
    redirectUrl.pathname = redirectTo && redirectTo !== '/login' ? redirectTo : '/';
    redirectUrl.search = '';
    return Response.redirect(redirectUrl);
  }

  return supabaseResponse;
}

/**
 * Middlewareを適用するパス
 *
 * 除外パターン:
 * - _next/static (静的ファイル)
 * - _next/image (画像最適化)
 * - favicon.ico (ファビコン)
 * - その他の静的アセット (.svg, .png, .jpg, .jpeg, .gif, .webp)
 */
export const config = {
  matcher: [
    /*
     * 以下を除くすべてのパスにマッチ:
     * - _next/static (静的ファイル)
     * - _next/image (画像最適化ファイル)
     * - favicon.ico (ファビコンファイル)
     * - その他の静的アセット (.svg, .png, .jpg, .jpeg, .gif, .webp)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
