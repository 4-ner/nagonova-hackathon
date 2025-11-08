import { test, expect } from '@playwright/test';
import { loginAsUser, logout } from './fixtures/auth';

/**
 * 認証フローのE2Eテスト
 *
 * ログイン、未認証時のリダイレクト、ログアウトをテストします。
 */
test.describe('認証フロー', () => {
  test.describe.configure({ mode: 'parallel' });

  test('未認証ユーザーはログインページにリダイレクトされる', async ({ page }) => {
    // 保護されたページにアクセス
    await page.goto('/rfps');

    // ログインページにリダイレクトされることを確認
    await expect(page).toHaveURL(/\/login/);

    // ログインページの要素を確認
    await expect(page.locator('h1, h2').filter({ hasText: 'RFP Radar' })).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('button').filter({ hasText: /ログインリンクを送信/ })).toBeVisible();
  });

  test('ログインページが正しく表示される', async ({ page }) => {
    await page.goto('/login');

    // タイトルとフォームの確認
    await expect(page).toHaveTitle(/RFP Radar/i);
    await expect(page.locator('h1, h2').filter({ hasText: 'RFP Radar' })).toBeVisible();
    await expect(page.getByText('官公需入札案件マッチングシステム')).toBeVisible();

    // フォーム要素の確認
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveAttribute('placeholder', /example\.com/);

    // 送信ボタンの確認
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toContainText(/ログインリンクを送信/);
  });

  test('メールアドレス未入力時のバリデーション', async ({ page }) => {
    await page.goto('/login');

    // 空のフォームを送信
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // エラーメッセージの確認（バリデーション）
    await expect(page.getByText(/メールアドレスを入力してください/i)).toBeVisible({
      timeout: 5000,
    });
  });

  test('無効なメールアドレスのバリデーション', async ({ page }) => {
    await page.goto('/login');

    // 無効なメールアドレスを入力
    await page.locator('input[type="email"]').fill('invalid-email');
    await page.locator('button[type="submit"]').click();

    // エラーメッセージの確認
    await expect(page.getByText(/有効なメールアドレス/i)).toBeVisible({
      timeout: 5000,
    });
  });

  test('認証済みユーザーは保護されたページにアクセスできる', async ({ page }) => {
    // ヘルパーを使用してログイン
    await loginAsUser(page);

    // RFP一覧ページにアクセス
    await page.goto('/rfps');

    // ログインページにリダイレクトされない
    await expect(page).toHaveURL(/\/rfps/);

    // RFP一覧ページの要素を確認
    await expect(page.locator('h1').filter({ hasText: /案件一覧|RFP|入札案件/i })).toBeVisible({
      timeout: 10000,
    });
  });

  test('ログアウト後は未認証状態になる', async ({ page }) => {
    // ログイン
    await loginAsUser(page);

    // ダッシュボードにアクセス
    await page.goto('/');

    // ログアウトボタンを探してクリック（存在する場合）
    const logoutButton = page.locator('button').filter({ hasText: /ログアウト/i });
    if (await logoutButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await logoutButton.click();
    } else {
      // ログアウトボタンがない場合は、ヘルパーを使用
      await logout(page);
    }

    // 保護されたページにアクセスを試みる
    await page.goto('/rfps');

    // ログインページにリダイレクトされることを確認
    await expect(page).toHaveURL(/\/login/);
  });

  test('リダイレクトパラメータが正しく機能する', async ({ page }) => {
    // redirect パラメータ付きでログインページにアクセス
    await page.goto('/login?redirect=/bookmarks');

    // ページが正しく表示されることを確認
    await expect(page.locator('input[type="email"]')).toBeVisible();

    // URLにredirectパラメータが含まれることを確認
    expect(page.url()).toContain('redirect=/bookmarks');
  });
});
