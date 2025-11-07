import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';
import type { Database } from './database.types';

/**
 * Middleware用Supabaseクライアント
 * セッション管理と認証ガード処理で使用する
 */
export async function updateSession(request: NextRequest) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // ビルド時（環境変数未設定時）はダミーの値を使用
  if (!supabaseUrl || !supabaseAnonKey) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error(
        'NEXT_PUBLIC_SUPABASE_URLとNEXT_PUBLIC_SUPABASE_ANON_KEYが環境変数に設定されていません'
      );
    }
    // ビルド時のみダミー値を使用
    return {
      supabaseResponse: NextResponse.next({ request }),
      session: null,
    };
  }

  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabase = createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) =>
          request.cookies.set(name, value)
        );
        supabaseResponse = NextResponse.next({
          request,
        });
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options)
        );
      },
    },
  });

  // セッションを更新（リフレッシュトークンがあれば自動的にリフレッシュ）
  // IMPORTANT: getUser()ではなくgetSession()を使用する
  // getUser()はJWTを検証するだけでリフレッシュしないため
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return { supabaseResponse, session };
}
