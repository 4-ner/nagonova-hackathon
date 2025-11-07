'use client';

import { useContext } from 'react';
import { AuthContext, type AuthContextType } from '@/providers/AuthProvider';

/**
 * 認証状態にアクセスするカスタムフック
 *
 * AuthProviderでラップされたコンポーネント内で使用できます。
 *
 * @throws {Error} AuthProviderの外で使用された場合にエラーをスロー
 *
 * @example
 * ```tsx
 * function ProfilePage() {
 *   const { user, loading, signOut } = useAuth();
 *
 *   if (loading) {
 *     return <div>読み込み中...</div>;
 *   }
 *
 *   if (!user) {
 *     return <div>ログインしてください</div>;
 *   }
 *
 *   return (
 *     <div>
 *       <p>メール: {user.email}</p>
 *       <button onClick={signOut}>ログアウト</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuthはAuthProviderの内部で使用する必要があります');
  }

  return context;
}
