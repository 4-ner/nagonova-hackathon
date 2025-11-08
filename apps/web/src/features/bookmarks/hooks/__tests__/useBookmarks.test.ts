/**
 * useBookmarksカスタムフックのテスト
 */
import { renderHook, waitFor } from '@testing-library/react';
import { SWRConfig } from 'swr';
import { useBookmarks, useIsBookmarked } from '../useBookmarks';
import * as api from '@/lib/api';
import { mockBookmarkListResponse } from '@/__tests__/utils/test-utils';

// APIモック
jest.mock('@/lib/api');
const mockedApiGet = api.apiGet as jest.MockedFunction<typeof api.apiGet>;

// SWRラッパー
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
    {children}
  </SWRConfig>
);

describe('useBookmarks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('ブックマーク一覧が正常に取得できる', async () => {
    // APIモックの設定
    mockedApiGet.mockResolvedValueOnce(mockBookmarkListResponse);

    // フックをレンダリング
    const { result } = renderHook(() => useBookmarks({ page: 1, page_size: 20 }), {
      wrapper,
    });

    // 初期状態の確認
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(true);

    // データ取得完了を待つ
    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    // データの検証
    expect(result.current.data).toEqual(mockBookmarkListResponse);
    expect(result.current.error).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it('エラー時に適切にハンドリングされる', async () => {
    // APIエラーのモック
    const error = new Error('Network error');
    mockedApiGet.mockRejectedValueOnce(error);

    // フックをレンダリング
    const { result } = renderHook(() => useBookmarks(), { wrapper });

    // エラー発生を待つ
    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    // エラーの検証
    expect(result.current.error).toBeDefined();
    expect(result.current.data).toBeUndefined();
  });

  it('クエリパラメータが正しくURLに反映される', async () => {
    mockedApiGet.mockResolvedValueOnce(mockBookmarkListResponse);

    const params = { page: 2, page_size: 10 };
    renderHook(() => useBookmarks(params), { wrapper });

    await waitFor(() => {
      expect(mockedApiGet).toHaveBeenCalledWith(
        expect.stringContaining('page=2'),
        expect.anything()
      );
      expect(mockedApiGet).toHaveBeenCalledWith(
        expect.stringContaining('page_size=10'),
        expect.anything()
      );
    });
  });
});

describe('useIsBookmarked', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('RFPがブックマーク済みの場合trueを返す', async () => {
    // ブックマーク一覧のモック
    mockedApiGet.mockResolvedValueOnce(mockBookmarkListResponse);

    // フックをレンダリング
    const { result } = renderHook(
      () => useIsBookmarked(mockBookmarkListResponse.items[0].rfp_id),
      { wrapper }
    );

    // データ取得完了を待つ
    await waitFor(() => {
      expect(result.current.isBookmarked).toBe(true);
    });

    expect(result.current.isBookmarked).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it('RFPがブックマークされていない場合falseを返す', async () => {
    // 空のブックマーク一覧のモック
    mockedApiGet.mockResolvedValueOnce({
      total: 0,
      items: [],
      page: 1,
      page_size: 20,
    });

    // フックをレンダリング
    const { result } = renderHook(() => useIsBookmarked('non-existent-rfp-id'), {
      wrapper,
    });

    // データ取得完了を待つ
    await waitFor(() => {
      expect(result.current.isBookmarked).toBe(false);
    });

    expect(result.current.isBookmarked).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  it('rfpIdがnullの場合、falseを返す', () => {
    // フックをレンダリング
    const { result } = renderHook(() => useIsBookmarked(null), { wrapper });

    // 即座にfalseが返される
    expect(result.current.isBookmarked).toBe(false);
    expect(result.current.isLoading).toBe(false);

    // APIが呼ばれていないことを確認
    expect(mockedApiGet).not.toHaveBeenCalled();
  });
});
