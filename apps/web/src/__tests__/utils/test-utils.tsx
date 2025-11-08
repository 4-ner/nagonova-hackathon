/**
 * テストユーティリティ
 *
 * React Testing Libraryのカスタムレンダラーとモックデータを提供します。
 */
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { SWRConfig } from 'swr';

/**
 * SWRキャッシュを無効化したカスタムレンダラー
 *
 * テスト間でキャッシュが共有されないようにします。
 */
export function renderWithSWR(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
        {children}
      </SWRConfig>
    ),
    ...options,
  });
}

/**
 * テスト用のモックRFPデータ
 */
export const mockRfpData = {
  id: 'rfp-test-123',
  external_id: 'ext-rfp-123',
  title: 'テストRFP案件',
  issuing_org: 'テスト組織',
  description: 'これはテスト用のRFP案件です。',
  budget: 10000000,
  region: '東京都',
  deadline: '2025-12-31',
  url: 'https://example.com/rfp/123',
  external_doc_urls: ['https://example.com/doc1.pdf'],
  has_embedding: true,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  fetched_at: '2025-01-01T00:00:00Z',
};

/**
 * テスト用のモックブックマークデータ
 */
export const mockBookmarkData = {
  id: 'bookmark-test-123',
  user_id: 'test-user-123',
  rfp_id: 'rfp-test-123',
  created_at: '2025-01-01T00:00:00Z',
  rfp: mockRfpData,
};

/**
 * テスト用のブックマーク一覧レスポンス
 */
export const mockBookmarkListResponse = {
  total: 1,
  items: [mockBookmarkData],
  page: 1,
  page_size: 20,
};
