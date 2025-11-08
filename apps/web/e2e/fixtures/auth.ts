import { test as base, Page } from '@playwright/test';
import { createClient } from '@supabase/supabase-js';

/**
 * テスト用認証ヘルパー
 *
 * Supabase認証を使用して、テストユーザーでログインする
 */

// 環境変数からSupabase設定を取得
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// 必須環境変数のチェック
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error(
    'E2Eテストの実行には以下の環境変数が必要です:\n' +
    '- NEXT_PUBLIC_SUPABASE_URL\n' +
    '- NEXT_PUBLIC_SUPABASE_ANON_KEY'
  );
}

// テストユーザーの認証情報（環境変数から取得）
const TEST_USER_EMAIL = process.env.E2E_TEST_USER_EMAIL;
const TEST_USER_PASSWORD = process.env.E2E_TEST_USER_PASSWORD;

// テストユーザー認証情報のチェック
if (!TEST_USER_EMAIL || !TEST_USER_PASSWORD) {
  throw new Error(
    'E2Eテストの実行には以下の環境変数が必要です:\n' +
    '- E2E_TEST_USER_EMAIL\n' +
    '- E2E_TEST_USER_PASSWORD\n' +
    '詳細は apps/web/e2e/README.md を参照してください。'
  );
}

/**
 * 認証済みユーザーとしてログイン
 */
export async function loginAsUser(page: Page) {
  // Supabaseクライアントを作成
  const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  // メールとパスワードでログイン
  const { data, error } = await supabase.auth.signInWithPassword({
    email: TEST_USER_EMAIL,
    password: TEST_USER_PASSWORD,
  });

  if (error) {
    throw new Error(`ログインに失敗しました: ${error.message}`);
  }

  if (!data.session) {
    throw new Error('セッションが作成されませんでした');
  }

  // セッション情報をlocalStorageに設定
  await page.goto('/');
  await page.evaluate((session) => {
    // Supabaseのセッション情報をlocalStorageに保存
    const key = `sb-${new URL(session.supabaseUrl).hostname.split('.')[0]}-auth-token`;
    localStorage.setItem(
      key,
      JSON.stringify({
        access_token: session.accessToken,
        refresh_token: session.refreshToken,
        expires_at: session.expiresAt,
        user: session.user,
      })
    );
  }, {
    supabaseUrl: SUPABASE_URL,
    accessToken: data.session.access_token,
    refreshToken: data.session.refresh_token,
    expiresAt: data.session.expires_at,
    user: data.session.user,
  });

  return data.session;
}

/**
 * ログアウト
 */
export async function logout(page: Page) {
  await page.goto('/');
  await page.evaluate(() => {
    // localStorageからSupabase認証情報を削除
    Object.keys(localStorage)
      .filter(key => key.includes('sb-') && key.includes('-auth-token'))
      .forEach(key => localStorage.removeItem(key));
  });
}

/**
 * 認証済みコンテキストを提供するフィクスチャ
 */
type AuthFixtures = {
  authenticatedPage: Page;
};

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // テスト前に認証を実行
    await loginAsUser(page);

    // 認証済みページをテストで使用
    await use(page);

    // テスト後にログアウト（クリーンアップ）
    await logout(page);
  },
});

export { expect } from '@playwright/test';
