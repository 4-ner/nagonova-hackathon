# E2Eテスト

Playwrightを使用したEnd-to-Endテストのドキュメントです。

## 概要

このディレクトリには、RFP Radarアプリケーションの主要なユーザーフローをカバーするE2Eテストが含まれています。

## テストファイル構成

```
e2e/
├── fixtures/
│   └── auth.ts              # 認証ヘルパーとフィクスチャ
├── auth.spec.ts             # 認証フローのテスト
├── rfps.spec.ts             # RFP閲覧・フィルタリングのテスト
├── bookmarks.spec.ts        # ブックマーク機能のテスト
├── proposal.spec.ts         # 提案生成のテスト
└── README.md                # このファイル
```

## テストカバレッジ

### 認証フロー (`auth.spec.ts`)

- 未認証ユーザーのログインページへのリダイレクト
- ログインページの表示
- メールアドレスのバリデーション
- 認証済みユーザーの保護ページへのアクセス
- ログアウト機能
- リダイレクトパラメータの動作

### RFP閲覧・フィルタリング (`rfps.spec.ts`)

- RFP一覧ページの表示
- 件数表示
- RFPカードの表示
- 地域フィルタリング
- 予算フィルタリング
- キーワード検索
- RFP詳細ページへの遷移
- ページネーション
- フィルターのクリア
- エラーハンドリング

### ブックマーク機能 (`bookmarks.spec.ts`)

- ブックマークボタンの表示
- RFP一覧からのブックマーク追加
- RFP詳細ページからのブックマーク追加
- ブックマーク一覧での確認
- ブックマークの削除
- 件数表示
- ブックマーク済みアイコンの表示

### 提案生成 (`proposal.spec.ts`)

- 提案生成ページへの遷移
- 提案ドラフト生成画面の表示
- Markdownプレビューの表示
- アクションボタンの表示
- コピー機能
- ダウンロード機能
- 戻るボタン
- 注意事項の表示
- エラーハンドリング
- Markdownフォーマットの適用

## セットアップ

### 1. 環境変数の設定

`.env.test`ファイルを作成し、必要な環境変数を設定します。

```bash
cp .env.test.example .env.test
```

`.env.test`の内容を編集：

```env
# Supabase設定
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API設定
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Playwright設定
PLAYWRIGHT_BASE_URL=http://localhost:3000

# テストユーザー認証情報
E2E_TEST_USER_EMAIL=test@example.com
E2E_TEST_USER_PASSWORD=test-password-123
```

### 2. テストユーザーの作成

Supabaseダッシュボードで、E2Eテスト用のユーザーアカウントを作成します。

1. Supabaseダッシュボードにログイン
2. 「Authentication」→「Users」へ移動
3. 「Add user」をクリック
4. `.env.test`で設定したメールアドレスとパスワードでユーザーを作成

### 3. 開発サーバーの起動

E2Eテストを実行する前に、開発サーバーを起動しておく必要があります。

```bash
# フロントエンド
pnpm dev

# バックエンド（別ターミナル）
cd ../api
uvx uvicorn main:app --reload --port 8000
```

## テストの実行

### すべてのテストを実行

```bash
pnpm test:e2e
```

### UIモードで実行（推奨）

```bash
pnpm test:e2e:ui
```

UIモードでは、テストの実行状態を視覚的に確認でき、デバッグが容易です。

### デバッグモードで実行

```bash
pnpm test:e2e:debug
```

### ヘッドモードで実行（ブラウザを表示）

```bash
pnpm test:e2e:headed
```

### 特定のブラウザでテスト

```bash
# Chromiumのみ
pnpm test:e2e:chromium

# Firefoxのみ
pnpm test:e2e:firefox

# WebKitのみ
pnpm test:e2e:webkit
```

### 特定のテストファイルを実行

```bash
# 認証テストのみ
pnpm test:e2e e2e/auth.spec.ts

# RFPテストのみ
pnpm test:e2e e2e/rfps.spec.ts
```

### 特定のテストケースを実行

```bash
# テスト名で絞り込み
pnpm test:e2e -g "ログイン"
```

## テスト結果

### レポートの表示

テスト実行後、HTMLレポートを表示できます。

```bash
npx playwright show-report
```

レポートには以下の情報が含まれます：

- テストの成功/失敗状況
- 実行時間
- スクリーンショット（失敗時）
- ビデオ録画（失敗時）
- トレースファイル（失敗時）

### アーティファクトの場所

- レポート: `playwright-report/`
- スクリーンショット: `test-results/`
- ビデオ: `test-results/`

## 認証ヘルパーの使用

`fixtures/auth.ts`には、認証済みユーザーとしてテストを実行するためのヘルパーが含まれています。

### 認証済みページフィクスチャ

```typescript
import { test, expect } from './fixtures/auth';

test('認証が必要なテスト', async ({ authenticatedPage: page }) => {
  // pageは既に認証済みの状態
  await page.goto('/dashboard');
  // テストコード...
});
```

### 手動でログイン

```typescript
import { loginAsUser, logout } from './fixtures/auth';

test('手動ログインテスト', async ({ page }) => {
  await loginAsUser(page);
  // テストコード...
  await logout(page);
});
```

## ベストプラクティス

### 1. テストの独立性

各テストは独立して実行できるように設計してください。他のテストの実行結果に依存しないようにします。

### 2. 適切な待機

要素の表示を待つ際は、適切なタイムアウトを設定してください。

```typescript
// 良い例
await expect(page.locator('h1')).toBeVisible({ timeout: 5000 });

// 悪い例（固定の待機時間）
await page.waitForTimeout(3000);
```

### 3. セレクタの選択

- 可能な限り、セマンティックなセレクタを使用
- テキスト内容ではなく、`data-testid`などの属性を使用することを推奨

```typescript
// 良い例
await page.locator('[data-testid="login-button"]').click();

// 許容できる例
await page.locator('button').filter({ hasText: 'ログイン' }).click();
```

### 4. エラーハンドリング

テストが失敗した場合に備えて、適切なエラーメッセージを設定してください。

```typescript
await expect(page.locator('h1')).toContainText('ダッシュボード', {
  timeout: 5000,
});
```

## トラブルシューティング

### テストが失敗する場合

1. **開発サーバーが起動しているか確認**
   - フロントエンド: `http://localhost:3000`
   - バックエンド: `http://localhost:8000`

2. **環境変数が正しく設定されているか確認**
   - `.env.test`ファイルが存在するか
   - Supabaseの認証情報が正しいか

3. **テストユーザーが存在するか確認**
   - Supabaseダッシュボードでユーザーを確認

4. **ブラウザが正しくインストールされているか確認**
   ```bash
   pnpx playwright install
   ```

5. **レポートとスクリーンショットを確認**
   ```bash
   npx playwright show-report
   ```

### タイムアウトエラー

テストがタイムアウトする場合、以下を確認してください：

- ネットワークの状態
- APIサーバーが正常に動作しているか
- データベースに十分なテストデータがあるか

### 認証エラー

認証に失敗する場合：

- テストユーザーの認証情報が正しいか
- Supabaseの設定が正しいか
- `.env.test`の環境変数が読み込まれているか

## CI/CDでの実行

GitHub ActionsなどのCI/CD環境で実行する場合：

```yaml
- name: Install Playwright Browsers
  run: pnpx playwright install --with-deps

- name: Run E2E tests
  run: pnpm test:e2e
  env:
    NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
    E2E_TEST_USER_EMAIL: ${{ secrets.E2E_TEST_USER_EMAIL }}
    E2E_TEST_USER_PASSWORD: ${{ secrets.E2E_TEST_USER_PASSWORD }}
```

## 参考資料

- [Playwright公式ドキュメント](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Next.js Testing](https://nextjs.org/docs/testing)
