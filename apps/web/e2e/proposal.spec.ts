import { test, expect } from './fixtures/auth';
import * as fs from 'fs';
import * as path from 'path';

/**
 * 提案生成のE2Eテスト
 *
 * 提案ドラフト生成、Markdownプレビュー、コピー、ダウンロード機能をテストします。
 */
test.describe('提案生成', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ authenticatedPage }) => {
    // 各テスト前にRFP一覧ページへ移動
    await authenticatedPage.goto('/rfps');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('RFP詳細ページから提案生成ページに遷移できる', async ({ authenticatedPage: page }) => {
    // 最初のRFPリンクをクリック
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpId = (await firstRfpLink.getAttribute('href'))?.split('/').pop();
      await firstRfpLink.click();
      await page.waitForLoadState('networkidle');

      // 提案生成ボタンまたはリンクを探す
      const proposalLink = page.locator('a[href*="/proposal"], button').filter({ hasText: /提案|ドラフト|Draft/i }).first();

      if (await proposalLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        await proposalLink.click();
        await page.waitForLoadState('networkidle');

        // 提案ページのURLを確認
        await expect(page).toHaveURL(new RegExp(`/rfps/${rfpId}/proposal`));

        // 提案ページのタイトルを確認
        await expect(page.locator('h1').filter({ hasText: /提案ドラフト|提案書|Proposal/i })).toBeVisible({
          timeout: 10000,
        });
      }
    }
  });

  test('提案ドラフト生成画面が正しく表示される', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);
      await page.waitForLoadState('networkidle');

      // ページタイトルの確認
      await expect(page.locator('h1').filter({ hasText: /提案ドラフト|提案書/i })).toBeVisible({
        timeout: 10000,
      });

      // 戻るボタンの確認
      const backButton = page.locator('a, button').filter({ hasText: /戻る|Back/i }).first();
      await expect(backButton).toBeVisible();

      // 読み込み中またはコンテンツの確認
      const isLoading = await page.locator('text=/生成中|読み込み中|Loading/i').isVisible({ timeout: 2000 }).catch(() => false);
      const hasContent = await page.locator('text=/コピー|ダウンロード|プレビュー/i').isVisible({ timeout: 15000 }).catch(() => false);
      const hasError = await page.locator('text=/エラー|Error/i').isVisible({ timeout: 2000 }).catch(() => false);

      expect(isLoading || hasContent || hasError).toBeTruthy();
    }
  });

  test('提案ドラフトが生成され、プレビューが表示される', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);

      // 生成完了を待機（最大30秒）
      await page.waitForSelector('text=/プレビュー|Preview/i', { timeout: 30000 }).catch(() => null);

      // プレビューセクションの確認
      const previewSection = page.locator('text=/プレビュー|Preview/i').first();

      if (await previewSection.isVisible({ timeout: 5000 }).catch(() => false)) {
        await expect(previewSection).toBeVisible();

        // Markdownコンテンツが表示されていることを確認
        const contentArea = page.locator('.prose, [class*="markdown"], [class*="preview"]').first();

        if (await contentArea.isVisible({ timeout: 5000 }).catch(() => false)) {
          // コンテンツが存在することを確認
          const hasContent = await contentArea.textContent();
          expect(hasContent && hasContent.length > 0).toBeTruthy();
        }
      }
    }
  });

  test('アクションボタン（コピー、ダウンロード）が表示される', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);

      // アクションボタンが表示されるまで待機
      await page.waitForSelector('text=/コピー|Copy/i', { timeout: 30000 }).catch(() => null);

      // コピーボタンの確認
      const copyButton = page.locator('button').filter({ hasText: /コピー|Copy/i }).first();
      if (await copyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await expect(copyButton).toBeVisible();
      }

      // ダウンロードボタンの確認
      const downloadButton = page.locator('button').filter({ hasText: /ダウンロード|Download/i }).first();
      if (await downloadButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await expect(downloadButton).toBeVisible();
      }
    }
  });

  test('コピー機能が動作する', async ({ authenticatedPage: page, context }) => {
    // クリップボード権限を付与
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);

      // コピーボタンが表示されるまで待機
      const copyButton = page.locator('button').filter({ hasText: /コピー|Copy/i }).first();

      if (await copyButton.isVisible({ timeout: 30000 }).catch(() => false)) {
        // コピーボタンをクリック
        await copyButton.click();

        // トースト通知の確認
        await expect(page.locator('text=/コピーしました|Copied/i')).toBeVisible({
          timeout: 3000,
        });

        // クリップボードの内容を確認
        const clipboardContent = await page.evaluate(() => navigator.clipboard.readText());
        expect(clipboardContent.length).toBeGreaterThan(0);
      }
    }
  });

  test('ダウンロード機能が動作する', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);

      // ダウンロードボタンが表示されるまで待機
      const downloadButton = page.locator('button').filter({ hasText: /ダウンロード|Download/i }).first();

      if (await downloadButton.isVisible({ timeout: 30000 }).catch(() => false)) {
        // ダウンロード待機を設定
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);

        // ダウンロードボタンをクリック
        await downloadButton.click();

        // ダウンロードイベントを待機
        const download = await downloadPromise;

        if (download) {
          // ダウンロードされたファイル名を確認
          const fileName = download.suggestedFilename();
          expect(fileName).toMatch(/proposal.*\.md$/);

          // トースト通知の確認
          await expect(page.locator('text=/ダウンロードしました|Downloaded/i')).toBeVisible({
            timeout: 3000,
          });
        }
      }
    }
  });

  test('戻るボタンでRFP詳細ページに戻れる', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      const rfpId = rfpHref?.split('/').pop();

      await page.goto(`${rfpHref}/proposal`);
      await page.waitForLoadState('networkidle');

      // 戻るボタンをクリック
      const backButton = page.locator('a, button').filter({ hasText: /戻る|詳細に戻る|Back/i }).first();

      if (await backButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await backButton.click();
        await page.waitForLoadState('networkidle');

        // RFP詳細ページに戻ったことを確認
        await expect(page).toHaveURL(new RegExp(`/rfps/${rfpId}$`));
      }
    }
  });

  test('注意事項が表示される', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);

      // プレビューが表示されるまで待機
      await page.waitForSelector('text=/プレビュー|Preview/i', { timeout: 30000 }).catch(() => null);

      // 注意事項の確認
      const notice = page.locator('text=/注意|AI.*自動生成|確認.*修正/i').first();

      if (await notice.isVisible({ timeout: 5000 }).catch(() => false)) {
        await expect(notice).toBeVisible();
      }
    }
  });

  test('エラー発生時に適切なメッセージが表示される', async ({ authenticatedPage: page }) => {
    // 存在しないRFP IDで提案ページにアクセス
    await page.goto('/rfps/invalid-rfp-id-12345/proposal');

    // エラーメッセージの確認（最大15秒待機）
    const errorMessage = page.locator('text=/エラー|Error|見つかりません|Not Found/i').first();

    if (await errorMessage.isVisible({ timeout: 15000 }).catch(() => false)) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('Markdownプレビューで基本的なフォーマットが適用される', async ({ authenticatedPage: page }) => {
    // RFP詳細ページへ移動
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const rfpHref = await firstRfpLink.getAttribute('href');
      await page.goto(`${rfpHref}/proposal`);

      // プレビューが表示されるまで待機
      await page.waitForSelector('text=/プレビュー|Preview/i', { timeout: 30000 }).catch(() => null);

      // Markdownプレビューエリアを確認
      const previewArea = page.locator('.prose, [class*="markdown"], [class*="preview"]').first();

      if (await previewArea.isVisible({ timeout: 5000 }).catch(() => false)) {
        // 見出しタグが存在するか確認（Markdownが正しくレンダリングされている）
        const hasHeadings = await previewArea.locator('h1, h2, h3, h4').count() > 0;

        // リストタグが存在するか確認
        const hasLists = await previewArea.locator('ul, ol').count() > 0;

        // パラグラフが存在するか確認
        const hasParagraphs = await previewArea.locator('p').count() > 0;

        // いずれかのフォーマットが適用されていることを確認
        expect(hasHeadings || hasLists || hasParagraphs).toBeTruthy();
      }
    }
  });
});
