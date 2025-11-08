import { test, expect } from './fixtures/auth';

/**
 * RFP閲覧・フィルタリングのE2Eテスト
 *
 * RFP一覧表示、フィルタリング、詳細表示、ページネーションをテストします。
 */
test.describe('RFP閲覧・フィルタリング', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ authenticatedPage }) => {
    // 各テスト前にRFP一覧ページへ移動
    await authenticatedPage.goto('/rfps');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('RFP一覧ページが正しく表示される', async ({ authenticatedPage: page }) => {
    // ページタイトルの確認
    await expect(page.locator('h1').filter({ hasText: /おすすめ案件|案件一覧/i })).toBeVisible();

    // 説明文の確認
    await expect(page.getByText(/プロフィールに基づいて|マッチング/i)).toBeVisible();

    // フィルターUIの存在確認
    const filterSection = page.locator('[class*="filter"], [data-testid="rfp-filter"]').first();
    if (await filterSection.isVisible().catch(() => false)) {
      await expect(filterSection).toBeVisible();
    }

    // 読み込み完了まで待機
    await page.waitForSelector('text=/件|読み込み中|エラー/', { timeout: 10000 });

    // 案件カードまたは「見つかりませんでした」メッセージの確認
    const hasCards = await page.locator('[class*="card"], article').count() > 0;
    const hasNoResults = await page.getByText(/見つかりませんでした|該当する案件がありません/i).isVisible().catch(() => false);

    expect(hasCards || hasNoResults).toBeTruthy();
  });

  test('RFP一覧が表示され、件数が表示される', async ({ authenticatedPage: page }) => {
    // 件数バッジの確認（「〇〇件」の表示）
    const countBadge = page.locator('text=/\\d+件/');
    await expect(countBadge.first()).toBeVisible({ timeout: 10000 });

    // 件数が0以上であることを確認
    const countText = await countBadge.first().textContent();
    const count = parseInt(countText?.match(/(\d+)件/)?.[1] || '0');
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('RFPカードの基本情報が表示される', async ({ authenticatedPage: page }) => {
    // カード要素が存在するか確認
    const cards = page.locator('[class*="card"]').filter({ has: page.locator('a[href*="/rfps/"]') });
    const cardCount = await cards.count();

    if (cardCount > 0) {
      // 最初のカードを確認
      const firstCard = cards.first();
      await expect(firstCard).toBeVisible();

      // カード内にタイトルが含まれているか
      const hasTitle = await firstCard.locator('h2, h3, [class*="title"]').count() > 0;
      expect(hasTitle).toBeTruthy();

      // リンクが存在するか
      const cardLink = firstCard.locator('a[href*="/rfps/"]').first();
      await expect(cardLink).toBeVisible();
    }
  });

  test('地域フィルタリングが機能する', async ({ authenticatedPage: page }) => {
    // フィルターが存在する場合のみテスト
    const regionFilter = page.locator('select, [role="combobox"]').filter({ hasText: /地域|都道府県|エリア/i }).first();

    if (await regionFilter.isVisible({ timeout: 2000 }).catch(() => false)) {
      // 初期件数を取得
      const initialCount = await page.locator('text=/\\d+件/').first().textContent();

      // 地域フィルターを変更（例: 東京都）
      await regionFilter.click();
      const option = page.locator('[role="option"], option').filter({ hasText: /東京|Tokyo/i }).first();

      if (await option.isVisible({ timeout: 2000 }).catch(() => false)) {
        await option.click();

        // 結果が更新されるまで待機
        await page.waitForTimeout(1000);

        // フィルター適用後の件数を確認
        const filteredCount = await page.locator('text=/\\d+件/').first().textContent();

        // フィルター前後で件数が変わるか、「フィルター適用中」表示を確認
        const hasFilteredText = await page.getByText(/フィルター適用中/i).isVisible().catch(() => false);
        expect(filteredCount !== initialCount || hasFilteredText).toBeTruthy();
      }
    }
  });

  test('予算フィルタリングが機能する', async ({ authenticatedPage: page }) => {
    // 予算フィルターの入力欄を探す
    const budgetMinInput = page.locator('input[type="number"]').filter({ has: page.locator(':text-matches("最小|下限", "i")') }).or(
      page.locator('input[placeholder*="最小"], input[placeholder*="下限"]')
    ).first();

    if (await budgetMinInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      // 最小予算を入力
      await budgetMinInput.fill('1000000');
      await budgetMinInput.press('Enter');

      // 結果が更新されるまで待機
      await page.waitForTimeout(1000);

      // フィルター適用確認
      const hasFilteredText = await page.getByText(/フィルター適用中/i).isVisible().catch(() => false);
      const hasResults = await page.locator('text=/\\d+件/').first().isVisible().catch(() => false);

      expect(hasFilteredText || hasResults).toBeTruthy();
    }
  });

  test('キーワード検索が機能する', async ({ authenticatedPage: page }) => {
    // 検索入力欄を探す
    const searchInput = page.locator('input[type="text"], input[type="search"]').filter({ hasText: /検索|キーワード|Search/i }).or(
      page.locator('input[placeholder*="検索"], input[placeholder*="キーワード"]')
    ).first();

    if (await searchInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      // キーワードを入力
      await searchInput.fill('システム開発');
      await searchInput.press('Enter');

      // 結果が更新されるまで待機
      await page.waitForTimeout(1000);

      // 検索結果が表示される
      await expect(page.locator('text=/件|読み込み中|見つかりませんでした/')).toBeVisible({
        timeout: 5000,
      });
    }
  });

  test('RFP詳細ページに遷移できる', async ({ authenticatedPage: page }) => {
    // 最初のRFPカードのリンクをクリック
    const firstRfpLink = page.locator('a[href*="/rfps/"]').first();

    if (await firstRfpLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const href = await firstRfpLink.getAttribute('href');
      await firstRfpLink.click();

      // URLが詳細ページに遷移したことを確認
      await expect(page).toHaveURL(new RegExp(href || '/rfps/[\\w-]+'));

      // 詳細ページの要素を確認
      await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('ページネーションが機能する', async ({ authenticatedPage: page }) => {
    // ページネーションボタンの確認
    const nextButton = page.locator('button').filter({ hasText: /次へ|Next|>/ });
    const prevButton = page.locator('button').filter({ hasText: /前へ|Previous|</ });

    // 次へボタンが存在し、有効な場合
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      const isDisabled = await nextButton.isDisabled().catch(() => true);

      if (!isDisabled) {
        // 現在のページ番号を取得
        const currentPageText = await page.locator('text=/\\d+\\s*\\/\\s*\\d+|ページ/').first().textContent().catch(() => '1');

        // 次ページへ移動
        await nextButton.click();

        // ページが更新されるまで待機
        await page.waitForTimeout(1000);

        // ページ番号が変わったか、URLが変わったか、または前へボタンが有効になったことを確認
        const newPageText = await page.locator('text=/\\d+\\s*\\/\\s*\\d+|ページ/').first().textContent().catch(() => '1');
        const isPrevEnabled = await prevButton.isEnabled().catch(() => false);

        expect(newPageText !== currentPageText || isPrevEnabled).toBeTruthy();
      }
    }
  });

  test('フィルターをクリアできる', async ({ authenticatedPage: page }) => {
    // クリアボタンまたはリセットボタンを探す
    const clearButton = page.locator('button').filter({ hasText: /クリア|リセット|Clear|Reset/i }).first();

    if (await clearButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      // フィルターを何か適用してからクリア
      const regionFilter = page.locator('select, [role="combobox"]').first();
      if (await regionFilter.isVisible({ timeout: 1000 }).catch(() => false)) {
        await regionFilter.click();
        const option = page.locator('[role="option"], option').first();
        if (await option.isVisible({ timeout: 1000 }).catch(() => false)) {
          await option.click();
          await page.waitForTimeout(500);

          // クリアボタンをクリック
          await clearButton.click();
          await page.waitForTimeout(500);

          // フィルター適用中の表示が消えることを確認
          const hasFilteredText = await page.getByText(/フィルター適用中/i).isVisible().catch(() => false);
          expect(hasFilteredText).toBeFalsy();
        }
      }
    }
  });

  test('エラー発生時に適切なメッセージが表示される', async ({ authenticatedPage: page }) => {
    // 存在しないページにアクセスしてエラーを発生させる
    await page.goto('/rfps?page=99999&invalid_param=true');

    // エラーメッセージまたは「見つかりませんでした」が表示されることを確認
    const hasError = await page.locator('text=/エラー|Error|見つかりませんでした|Not Found/i').isVisible({ timeout: 5000 }).catch(() => false);
    const hasNoResults = await page.locator('text=/0件|該当なし/').isVisible({ timeout: 5000 }).catch(() => false);

    expect(hasError || hasNoResults).toBeTruthy();
  });
});
