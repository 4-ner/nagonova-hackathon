'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

/**
 * ログインフォームコンポーネント
 */
function LoginForm() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/';

  const supabase = createClient();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback?redirect=${redirectTo}`,
        },
      });

      if (error) {
        throw error;
      }

      setMessage({
        type: 'success',
        text: `${email}にログインリンクを送信しました。メールをご確認ください。`,
      });
    } catch (error) {
      console.error('ログインエラー:', error);
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'ログインに失敗しました',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            RFP Radar
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            官公需入札案件マッチングシステム
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              メールアドレス
            </label>
            <div className="mt-1">
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full appearance-none rounded-md border border-gray-300 px-3 py-2 placeholder-gray-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                placeholder="you@example.com"
                disabled={loading}
              />
            </div>
          </div>

          {message && (
            <div
              className={`rounded-md p-4 ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              <p className="text-sm">{message.text}</p>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative flex w-full justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'ログインリンクを送信中...' : 'ログインリンクを送信'}
            </button>
          </div>

          <div className="text-center text-xs text-gray-500">
            <p>メールアドレスを入力すると、ログイン用のリンクが送信されます。</p>
            <p className="mt-1">メール内のリンクをクリックしてログインしてください。</p>
          </div>
        </form>
      </div>
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
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="text-lg text-gray-600">読み込み中...</div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
