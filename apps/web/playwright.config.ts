import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2Eテスト設定
 *
 * 認証状態の共有、スクリーンショット、ビデオ録画などを設定
 */
export default defineConfig({
  // テストディレクトリ
  testDir: './e2e',

  // テストの最大実行時間
  timeout: 30 * 1000,

  // 各テストのリトライ回数
  retries: process.env.CI ? 2 : 0,

  // 並列実行するワーカー数
  workers: process.env.CI ? 1 : undefined,

  // レポーター設定
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  // 共通設定
  use: {
    // ベースURL（テスト対象アプリケーション）
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',

    // トレース設定（失敗時のみ）
    trace: 'on-first-retry',

    // スクリーンショット（失敗時のみ）
    screenshot: 'only-on-failure',

    // ビデオ録画（失敗時のみ）
    video: 'retain-on-failure',

    // ナビゲーションタイムアウト
    navigationTimeout: 10 * 1000,

    // アクションタイムアウト
    actionTimeout: 10 * 1000,
  },

  // プロジェクト設定（ブラウザ別）
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // モバイルブラウザ（オプション）
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 13'] },
    // },
  ],

  // 開発サーバー設定（オプション）
  // webServer: {
  //   command: 'pnpm dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },
});
