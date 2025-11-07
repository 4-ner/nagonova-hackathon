# 認証システムセットアップガイド

RFP RadarのSupabase認証システムの実装と使用方法を説明します。

## 実装済みファイル

### 1. Supabaseクライアント

#### `/src/lib/supabase/client.ts`
ブラウザ用Supabaseクライアント。Client Componentsで使用します。

```typescript
import { createClient } from '@/lib/supabase/client';

const supabase = createClient();
```

#### `/src/lib/supabase/server.ts`
サーバー用Supabaseクライアント。Server Components、Server Actions、Route Handlersで使用します。

```typescript
import { createClient } from '@/lib/supabase/server';

const supabase = await createClient();
```

#### `/src/lib/supabase/middleware.ts`
Middleware用Supabaseクライアント。セッション管理と認証ガード処理で使用します。

#### `/src/lib/supabase/database.types.ts`
データベース型定義ファイル（プレースホルダー）。Supabase CLIで自動生成できます。

### 2. 認証プロバイダーとフック

#### `/src/providers/AuthProvider.tsx`
認証状態を管理するReact Context Provider。アプリ全体に認証状態を提供します。

#### `/src/hooks/useAuth.ts`
認証状態にアクセスするカスタムフック。

```typescript
const { user, session, loading, signOut } = useAuth();
```

### 3. Middleware

#### `/src/middleware.ts`
Next.js Middleware。未認証ユーザーを`/login`にリダイレクトします。

### 4. ページとルート

#### `/src/app/layout.tsx`
ルートレイアウト。AuthProviderでアプリ全体をラップします。

#### `/src/app/login/page.tsx`
ログインページ。メールOTP認証フォームを表示します。

#### `/src/app/auth/callback/route.ts`
OTPコールバックハンドラー。メールリンクからの認証を処理します。

#### `/src/app/page.tsx`
ホームページ。認証状態とAPIヘルスチェックを表示します。

## セットアップ手順

### 1. Supabaseプロジェクトの作成

1. [Supabase](https://supabase.com)にアクセスしてプロジェクトを作成
2. プロジェクトのURLとAnon Keyを取得

### 2. 環境変数の設定

`.env.local`ファイルを作成して以下を設定：

```bash
# .env.localファイル
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Supabase認証設定

Supabase Dashboardで以下を設定：

#### Email Templates
- メールテンプレートをカスタマイズ（オプション）

#### URL Configuration
- Site URL: `http://localhost:3000`（開発環境）
- Redirect URLs:
  - `http://localhost:3000/auth/callback`
  - `https://yourdomain.com/auth/callback`（本番環境）

#### Auth Providers
- Email OTPを有効化（デフォルトで有効）

### 4. 依存パッケージのインストール

```bash
cd apps/web
pnpm install
```

すでに以下のパッケージがインストールされています：
- `@supabase/ssr@0.7.0`
- `@supabase/supabase-js@2.80.0`

### 5. 開発サーバーの起動

```bash
cd apps/web
pnpm dev
```

## 使用方法

### ログインフロー

1. ユーザーが`http://localhost:3000`にアクセス
2. Middlewareが未認証を検出して`/login`にリダイレクト
3. ユーザーがメールアドレスを入力
4. Supabaseがログインリンクをメールで送信
5. ユーザーがメール内のリンクをクリック
6. `/auth/callback`でトークンを検証してセッションを作成
7. ホームページ（`/`）にリダイレクト

### コンポーネントでの認証状態の使用

```typescript
'use client';

import { useAuth } from '@/hooks/useAuth';

export default function MyComponent() {
  const { user, loading, signOut } = useAuth();

  if (loading) {
    return <div>読み込み中...</div>;
  }

  if (!user) {
    return <div>ログインしてください</div>;
  }

  return (
    <div>
      <p>ようこそ、{user.email}さん</p>
      <button onClick={signOut}>ログアウト</button>
    </div>
  );
}
```

### Server Componentsでの認証

```typescript
import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function ServerPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login');
  }

  return <div>ようこそ、{user.email}さん</div>;
}
```

### Server Actionsでの認証

```typescript
'use server';

import { createClient } from '@/lib/supabase/server';

export async function myServerAction() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    throw new Error('認証が必要です');
  }

  // データベース操作など
}
```

## トラブルシューティング

### メールが届かない

1. Supabase Dashboardの「Auth」→「Logs」でメール送信ログを確認
2. スパムフォルダを確認
3. メールアドレスが正しいか確認

### リダイレクトループが発生する

1. 環境変数が正しく設定されているか確認
2. Supabase DashboardのRedirect URLsが正しいか確認
3. ブラウザのキャッシュとCookieをクリア

### 型エラーが発生する

データベース型定義を生成してください：

```bash
npx supabase gen types typescript --project-id <project-id> > src/lib/supabase/database.types.ts
```

## 次のステップ

1. **Row Level Security (RLS)の設定**: Supabaseでテーブルごとにセキュリティポリシーを設定
2. **ユーザープロフィールテーブルの作成**: 追加のユーザー情報を保存
3. **ロールベースアクセス制御**: 管理者、一般ユーザーなどの権限管理
4. **メールテンプレートのカスタマイズ**: ブランディングに合わせたメールデザイン

## 参考資料

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase SSR Documentation](https://supabase.com/docs/guides/auth/server-side/nextjs)
- [Next.js Middleware Documentation](https://nextjs.org/docs/app/building-your-application/routing/middleware)
