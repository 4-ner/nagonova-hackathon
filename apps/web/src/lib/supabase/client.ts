import { createBrowserClient } from '@supabase/ssr';
import type { Database } from './database.types';

/**
 * ブラウザ用Supabaseクライアント
 * Client Componentsで使用する
 */
export function createClient() {
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
    return createBrowserClient<Database>(
      'https://placeholder.supabase.co',
      'placeholder-anon-key'
    );
  }

  return createBrowserClient<Database>(supabaseUrl, supabaseAnonKey);
}
